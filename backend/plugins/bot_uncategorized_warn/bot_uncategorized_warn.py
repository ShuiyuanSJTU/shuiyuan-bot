from ...bot_action import BotAction, on, scheduled
from ...model.topic import Topic
from ...db import db_manager as DBManager
from ...db import Base

from sqlalchemy import Column, Integer, DateTime, Enum
from sqlalchemy.sql import func
from enum import Enum as PyEnum
import datetime

class WarningStatus(PyEnum):
    PENDING = "pending"
    REMOVED = "removed"
    EXPIRED = "expired"

class UncategorizedTopicWarningRecord(Base):
    __tablename__ = "uncategorized_topic_warning_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, nullable=False)
    post_id = Column(Integer, nullable=False)
    status = Column(Enum(WarningStatus), default=WarningStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

UNCATEGORIZED_WARN_MESSAGE = "请勿选择未分类，也请不要随意发在聊聊水源，发帖前仔细阅读分类描述后选择。"

class BotUncategorizedWarn(BotAction):
    action_name = "BotUncategorizedWarn"

    @on("topic_created")
    def on_topic_created(self, topic: Topic):
        if topic.category_id == 1:
            post = self.api.create_post(UNCATEGORIZED_WARN_MESSAGE, topic.id, skip_validations=True)
            with DBManager.scoped_session():
                record = UncategorizedTopicWarningRecord(topic_id=topic.id, post_id=post['id'])
                record.save()

    @scheduled('interval', minutes=10, next_run_time=datetime.datetime.now())
    def check_warnings(self):
        with DBManager.scoped_session():
            records = UncategorizedTopicWarningRecord.where(status=WarningStatus.PENDING).all()

            for record in records:
                topic = Topic(**self.api.get_topic_by_id(record.topic_id))
                if topic.category_id != 1:
                    record.status = WarningStatus.REMOVED
                    self.api.delete_post(record.post_id)
                    record.save()
                else:
                    if record.created_at < datetime.datetime.now() - datetime.timedelta(minutes=30):
                        record.status = WarningStatus.EXPIRED
                        self.api.close_topic(topic.id)
                        record.save()

