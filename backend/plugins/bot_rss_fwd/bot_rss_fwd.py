import time
import logging
import datetime
import feedparser
from sqlalchemy import Column, String, Integer, DateTime, Index
from sqlalchemy.sql import func
from feedparser.util import FeedParserDict
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import Optional

from .markdown_converter import render_md
from ...db import Base
from ...db import db_manager as DBManager
from ...model import Post
from ...bot_action import BotAction, scheduled
from ...bot_account_manager import account_manager as AccountManager

logger = logging.getLogger(__name__)

class RssFwdRecord(Base):
    __tablename__ = 'rss_fwd_record'

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, nullable=False)
    guid = Column(String, nullable=False)
    created_time = Column(DateTime, default=func.now())
    topic_id = Column(Integer, nullable=True)
    post_id = Column(Integer, nullable=True)

    __table_args__ = (
        Index('idx_task_guid', 'task_id', 'guid', unique=True),
    )

class BotRssFwdConfig(BaseModel):
    enabled: bool
    rsshub_url: str
    tasks: list['RssFwdTaskConfig']

class RssFwdTaskConfig(BaseModel):
    endpoint: str
    enabled: bool = True
    new_topic: bool = True
    category_id: Optional[int] = None
    title_prefix: Optional[str] = None
    topic_id: Optional[int] = None
    forward_username: Optional[str] = None

    @property
    def task_key(self):
        return f"{self.endpoint}_{self.category_id}_{self.topic_id}"
    
    @property
    def is_new_task(self):
        return RssFwdRecord.where(task_id=self.task_key).count() == 0

    def __init__(self, **data):
        super().__init__(**data)
        if not self.enabled:
            return
        if self.new_topic:
            if not self.category_id:
                logger.error(f"RSS forward task {self.endpoint} is configured to create new topic but no category_id is provided.")
                self.enabled = False
            if self.topic_id is not None:
                logger.warning(f"RSS forward task {self.endpoint} is configured to create new topic but topic_id is provided, topic_id will be ignored.")
        else:
            if not self.topic_id:
                logger.error(f"RSS forward task {self.endpoint} is configured to post on existing topic but no topic_id is provided.")
                self.enabled = False
            if self.category_id is not None:
                logger.warning(f"RSS forward task {self.endpoint} is configured to update existing topic but category_id is provided, category_id will be ignored.")


class BotRssFwd(BotAction):
    action_name = "BotRssFwd"

    def __init__(self):
        super().__init__()
        self.config: BotRssFwdConfig = BotRssFwdConfig(**self.config)
        self.base_url = self.config.rsshub_url

    @staticmethod
    def feed_time_to_local_timezone(feed_time: time.struct_time) -> time.struct_time:
        utc_dt = datetime.datetime(*feed_time[:6], tzinfo=datetime.timezone.utc)
        return utc_dt.astimezone().timetuple()

    @classmethod
    def render_feed(cls, feed: FeedParserDict) -> str:
        element = BeautifulSoup(feed.summary, 'lxml')
        return render_md(element)
    
    def record_feed(self, task: RssFwdTaskConfig, feed: FeedParserDict, post: Optional[Post] = None):
        record = RssFwdRecord(task_id=task.task_key, guid=feed.guid)
        if post is not None:
            record.topic_id = post.topic_id
            record.post_id = post.id
        record.save()

    def filter_feed(self, feeds: list[FeedParserDict], task: RssFwdTaskConfig) -> list[FeedParserDict]:
        filtered_feeds = []
        for feed in feeds:
            if RssFwdRecord.find(task_id=task.task_key, guid=feed.guid) is None:
                filtered_feeds.append(feed)
        filtered_feeds.sort(key=lambda feed: feed.published_parsed)
        return filtered_feeds

    def create_post_or_topic(self, task: RssFwdTaskConfig, title: str, content: str):
        api = self.api if task.forward_username is None else AccountManager.get_bot_client(task.forward_username)
        if task.new_topic:
            result = api.create_topic(
                title=title,
                raw=content,
                category=task.category_id,
                skip_validations=True,
            )
        else:
            result = api.create_post(
                topic_id=task.topic_id,
                raw=content,
                skip_validations=True,
            )
        return Post(**result)

    def process_task(self, task: RssFwdTaskConfig):
        if not task.enabled:
            logger.debug(f"RSS forward task {task.endpoint} is disabled.")
            return
        feed_url = urljoin(self.base_url, task.endpoint)
        rss_response = feedparser.parse(feed_url)
        if rss_response.bozo:
            logger.warning(f"Failed to parse RSS feed {feed_url}.")
            return
        if not task.is_new_task:
            feeds = self.filter_feed(rss_response.entries, task)
            if len(feeds) == 0:
                logger.debug(f"No new feed in {feed_url}.")
                return
            for feed in feeds:
                title = feed.title if task.title_prefix is None else f"{task.title_prefix} {feed.title}"
                link = feed.link
                feed_content_md = self.render_feed(feed)
                post_content = f"{link}\n\n{feed_content_md}"
                post = self.create_post_or_topic(task, title, post_content)
                self.record_feed(task, feed, post)
        else:
            # new task, record all existing feeds
            # we only forward new feeds in the future
            logger.debug(f"RSS forward task {task.endpoint} is a new task, no feed will be processed.")
            for feed in rss_response.entries:
                self.record_feed(task, feed)

    @scheduled('interval', minutes=5, next_run_time=datetime.datetime.now())
    def on_scheduled(self):
        with DBManager.scoped_session():
            for task in self.config.tasks:
                try:
                    self.process_task(task)
                except Exception:
                    logger.exception(f"Failed to process RSS forward task {task.endpoint}.")
