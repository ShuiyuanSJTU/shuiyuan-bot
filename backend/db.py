import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from contextlib import contextmanager

from .bot_config import config as Config
from .utils import is_running_under_pytest
from .utils.singleton import Singleton

logger = logging.getLogger(__name__)

_Base = declarative_base()

class Base(_Base):
    __abstract__ = True

    @classmethod
    def where(cls, *args, **kwargs):
        if len(args) > 0 and len(kwargs) > 0:
            raise ValueError("You can only use either positional or keyword arguments, not both.")
        if len(args) > 0:
            return db_manager._scoped_session().query(cls).filter(*args)
        else:
            return db_manager._scoped_session().query(cls).filter_by(**kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return cls.where(*args, **kwargs).first()

    def save(self):
        session = db_manager._scoped_session()
        session.merge(self)
        session.commit()
        return self

    def delete(self):
        session = db_manager._scoped_session()
        session.delete(self)
        session.commit()
        return self

@Singleton
class DBManager:
    def __init__(self):
        self._engine = create_engine(Config.db_url)
        self._sessionmaker = sessionmaker(bind=self._engine)
        self._scoped_session = scoped_session(self._sessionmaker)
        if not is_running_under_pytest() and \
            ':memory:' in Config.db_url: # pragma: no cover
            logger.warning("Using in-memory database, data will be lost on restart")

    def init_tables(self):
        if is_running_under_pytest():
            Base.metadata.create_all(self._engine)
        else: # pragma: no cover
            logger.error("init_tables should only be called in test environment")
            logger.error("Please use alembic to manage database schema")
            logger.error("Run `alembic upgrade head`")

    @contextmanager
    def scoped_session(self):
        session = self._scoped_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            self._scoped_session.remove()

    @contextmanager
    def session(self):
        session = self._sessionmaker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

db_manager = DBManager()