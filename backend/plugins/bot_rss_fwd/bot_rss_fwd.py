import time
import logging
import datetime
import feedparser
from feedparser.util import FeedParserDict
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import Optional

from .markdown_converter import render_md
from ...bot_action import BotAction, scheduled
from ...bot_kv_storage import storage as Storage
from ...bot_account_manager import account_manager as AccountManager

logger = logging.getLogger(__name__)

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
    task_key: Optional[str] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.enabled:
            return
        self.task_key = f"{self.endpoint}_{self.category_id}_{self.topic_id}"
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
        for task in self.config.tasks:
            if task.enabled:
                task.endpoint = urljoin(self.base_url, task.endpoint)
        self.last_fwd_time: dict = Storage.get("rss_fwd_time", {})
        for task in self.config.tasks:
            if task.enabled and task.task_key not in self.last_fwd_time:
                self.last_fwd_time[task.task_key] = time.time()
        self.save_state()

    def save_state(self):
        Storage.set("rss_fwd_time", self.last_fwd_time)

    @staticmethod
    def feed_time_to_local_timezone(feed_time: time.struct_time) -> time.struct_time:
        utc_dt = datetime.datetime(*feed_time[:6], tzinfo=datetime.timezone.utc)
        return utc_dt.astimezone().timetuple()

    @classmethod
    def render_feed(cls, feed: FeedParserDict) -> str:
        element = BeautifulSoup(feed.summary, 'lxml')
        return render_md(element)

    def filter_feed_with_time(self, feeds: list[FeedParserDict], task: RssFwdTaskConfig) -> list[FeedParserDict]:
        # filter feeds in the future
        current = time.localtime()
        filtered_feeds = [feed for feed in feeds if self.feed_time_to_local_timezone(feed.published_parsed) < current]
        if len(filtered_feeds) < len(feeds):
            logger.warning(f"Ignored {len(feeds) - len(filtered_feeds)} feeds in the future.")
        # filter feeds before last update time
        last_update_time = time.localtime(self.last_fwd_time.get(task.task_key))
        filtered_feeds = [feed for feed in filtered_feeds if self.feed_time_to_local_timezone(feed.published_parsed) > last_update_time]
        filtered_feeds.sort(key=lambda feed: feed.published_parsed)
        return filtered_feeds

    def create_post_or_topic(self, task: RssFwdTaskConfig, title: str, content: str):
        api = self.api if task.forward_username is None else AccountManager.get_bot_client(task.forward_username)
        if task.new_topic:
            api.create_topic(
                title=title,
                raw=content,
                category=task.category_id,
                skip_validations=True,
            )
        else:
            api.create_post(
                topic_id=task.topic_id,
                raw=content,
                skip_validations=True,
            )

    def update_last_fwd_time(self, task: RssFwdTaskConfig, feed: FeedParserDict):
        self.last_fwd_time[task.task_key] = time.mktime(self.feed_time_to_local_timezone(feed.published_parsed))
        self.save_state()

    def process_task(self, task: RssFwdTaskConfig):
        if not task.enabled:
            logger.debug(f"RSS forward task {task.endpoint} is disabled.")
            return
        rss_response = feedparser.parse(task.endpoint)
        if rss_response.bozo:
            logger.warning(f"Failed to parse RSS feed {task.endpoint}.")
            return
        feeds = self.filter_feed_with_time(rss_response.entries, task)
        if len(feeds) == 0:
            logger.debug(f"No new feed in {task.endpoint}.")
            return
        for feed in feeds:
            title = feed.title if task.title_prefix is None else f"{task.title_prefix} {feed.title}"
            link = feed.link
            feed_content_md = self.render_feed(feed)
            post_content = f"{link}\n\n{feed_content_md}"
            self.create_post_or_topic(task, title, post_content)
            self.update_last_fwd_time(task, feed)

    @scheduled('interval', minutes=5, next_run_time=datetime.datetime.now())
    def on_scheduled(self):
        for task in self.config.tasks:
            try:
                self.process_task(task)
            except Exception as e:
                logger.exception(f"Failed to process RSS forward task {task.endpoint}.")
            finally:
                self.save_state()
