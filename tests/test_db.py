import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import String, Integer, Column, inspect

@pytest.fixture
def scoped_session():
    from backend.db import db_manager
    with db_manager.scoped_session() as session:
        yield session

@pytest.fixture
def test_table():
    from backend.db import DBManager, Base
    class TestTable(Base):
        __tablename__ = 'test_table'
        id = Column(Integer, primary_key=True)
        name = Column(String, nullable=False)
    db_manager = DBManager()
    db_manager.init_tables()
    yield TestTable

@pytest.fixture(autouse=True)
def auto_patch(patch_bot_config):
    yield

def test_db_manager_initialization(patch_bot_config):
    from backend.db import DBManager
    db_manager = DBManager()
    assert db_manager._engine.url == create_engine(patch_bot_config.db_url).url
    assert isinstance(db_manager._sessionmaker, sessionmaker)

def test_session_commit():
    from backend.db import DBManager
    db_manager = DBManager()
    db_manager._sessionmaker = MagicMock(return_value=MagicMock())
    with db_manager.session() as session:
        session.add(MagicMock())
    session.commit.assert_called_once()

def test_session_rollback():
    from backend.db import DBManager
    db_manager = DBManager()
    db_manager._sessionmaker = MagicMock(return_value=MagicMock())
    with pytest.raises(Exception):
        with db_manager.session() as session:
            session.add(MagicMock())
            raise Exception("Test Exception")
    session.rollback.assert_called_once()

def test_init_tables():
    from backend.db import DBManager, Base
    class TestTable(Base):
        __tablename__ = 'test_table'
        id = Column(Integer, primary_key=True)
        name = Column(String)
    db_manager = DBManager()
    db_manager.init_tables()
    assert 'test_table' in inspect(db_manager._engine).get_table_names()

def test_base_find(test_table, scoped_session):
    from backend.db import db_manager as DBManager
    with DBManager.session() as session:
        session.add(test_table(id=1, name='test'))
    r = test_table.find(id=1)
    assert r.name == 'test'
    assert r.id == 1

def test_base_where(test_table, scoped_session):
    from backend.db import db_manager as DBManager
    with DBManager.session() as session:
        session.add(test_table(id=1, name='test'))
        session.add(test_table(id=2, name='test'))
    q = test_table.where(name='test')
    r = q.all()
    assert q.count() == 2
    assert len(r) == 2
    assert set([i.id for i in r]) == {1, 2}

def test_base_add(test_table, scoped_session):
    t = test_table(id=1, name='test')
    t.save()
    from backend.db import db_manager as DBManager
    with DBManager.session() as session:
        assert session.query(test_table).filter_by(id=1).first().name == 'test'

def test_base_update(test_table, scoped_session):
    from backend.db import db_manager as DBManager
    with DBManager.session() as session:
        session.add(test_table(id=1, name='test'))
    t = test_table.find(id=1)
    t.name = 'test2'
    t.save()
    with DBManager.session() as session:
        assert session.query(test_table).filter_by(id=1).first().name == 'test2'

def test_base_delete(test_table, scoped_session):
    from backend.db import db_manager as DBManager
    with DBManager.session() as session:
        session.add(test_table(id=1, name='test'))
    t = test_table.find(id=1)
    t.delete()
    with DBManager.session() as session:
        assert session.query(test_table).filter_by(id=1).first() is None

def test_scoped_session_rollback(test_table, scoped_session):
    from backend.db import db_manager as DBManager
    t1 = test_table(id=1, name=None)
    t2 = test_table(id=2, name='test')
    with pytest.raises(Exception):
        with DBManager.scoped_session() as session:
            t2.save()
            t1.save()
    with DBManager.session() as session:
        assert session.query(test_table).filter_by(id=1).first() is None
        assert session.query(test_table).filter_by(id=2).first().name == 'test'