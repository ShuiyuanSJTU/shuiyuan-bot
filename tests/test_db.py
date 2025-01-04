import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(autouse=True)
def auto_patch(patch_bot_config):
    yield

def test_db_manager_initialization(patch_bot_config):
    from backend.db import DBManager
    db_manager = DBManager()
    assert db_manager.engine.url == create_engine(patch_bot_config.db_url).url
    assert isinstance(db_manager.sessionmaker, sessionmaker)

def test_session_commit():
    from backend.db import DBManager, Base
    db_manager = DBManager()
    db_manager.sessionmaker = MagicMock(return_value=MagicMock())
    with db_manager.session() as session:
        session.add(MagicMock())
    session.commit.assert_called_once()

def test_session_rollback():
    from backend.db import DBManager
    db_manager = DBManager()
    db_manager.sessionmaker = MagicMock(return_value=MagicMock())
    with pytest.raises(Exception):
        with db_manager.session() as session:
            session.add(MagicMock())
            raise Exception("Test Exception")
    session.rollback.assert_called_once()

def test_init_tables():
    from backend.db import DBManager, Base
    from sqlalchemy import String, Integer, Column, inspect
    class TestTable(Base):
        __tablename__ = 'test_table'
        id = Column(Integer, primary_key=True)
        name = Column(String)
    db_manager = DBManager()
    db_manager.init_tables()
    assert 'test_table' in inspect(db_manager.engine).get_table_names()