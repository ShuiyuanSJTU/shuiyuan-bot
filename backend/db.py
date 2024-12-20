import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

from .bot_config import config as Config
from .utils import is_running_under_pytest
from .utils.singleton import Singleton

logger = logging.getLogger(__name__)

Base = declarative_base()

@Singleton
class DBManager:
    def __init__(self):
        self.engine = create_engine(Config.db_url)
        self.sessionmaker = sessionmaker(bind=self.engine)
        if not is_running_under_pytest() and \
            ':memory:' in Config.db_url: # pragma: no cover
            logger.warning("Using in-memory database, data will be lost on restart")

    def init_tables(self):
        Base.metadata.create_all(self.engine)

    @contextmanager
    def session(self):
        session = self.sessionmaker()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

db_manager = DBManager()