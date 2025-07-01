from .db import Base
from .db import db_manager as DBManager
from .utils.singleton import Singleton
from sqlalchemy import Column, JSON, String

class KVStorageItem(Base):
    __tablename__ = 'kv_storage'

    key = Column(String, primary_key=True)
    value = Column(JSON)

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self): # pragma: no cover
        return f"<KVStorageItem(key={self.key}, value={self.value})>"

@Singleton
class BotKVStorage:
    def get(self, key: str, default=None):
        with DBManager.session() as session:
            item = session.query(KVStorageItem).filter_by(key=key).first()
            if item is None:
                return default
            return item.value
    
    def set(self, key: str, value):
        with DBManager.session() as session:
            item = session.query(KVStorageItem).filter_by(key=key).first()
            if item is None:
                item = KVStorageItem(key, value)
                session.add(item)
            else:
                item.value = value

    def delete(self, key: str):
        with DBManager.session() as session:
            item = session.query(KVStorageItem).filter_by(key=key).first()
            if item is not None:
                session.delete(item)

storage = BotKVStorage()