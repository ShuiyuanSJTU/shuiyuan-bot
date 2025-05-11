from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from .user import BasicUser

class Topic(BaseModel):
    id: int
    title: str
    created_at: str
    user_id: int
    fancy_title: Optional[str] = None
    posts_count: Optional[int] = None
    views: Optional[int] = None
    reply_count: Optional[int] = None
    like_count: Optional[int] = None
    last_posted_at: Optional[str] = None
    visible: Optional[bool] = None
    closed: Optional[bool] = None
    archived: Optional[bool] = None
    archetype: Optional[str] = None
    slug: Optional[str] = None
    category_id: Optional[int] = None
    word_count: Optional[int] = None
    deleted_at: Optional[str] = None
    pinned_globally: Optional[bool] = None
    pinned_at: Optional[str] = None
    pinned_until: Optional[str] = None
    unpinned: Optional[bool] = None
    pinned: Optional[bool] = None
    highest_post_number: Optional[int] = None
    deleted_by: Optional[int] = None
    has_deleted: Optional[bool] = None
    bookmarked: Optional[bool] = None
    participant_count: Optional[int] = None
    queued_posts_count: Optional[int] = None
    thumbnails: Optional[list] = None
    created_by: Optional[BasicUser] = None
    last_poster: Optional[BasicUser] = None
    summarizable: Optional[bool] = None
    pending_posts: Optional[List[Any]] = None
    tags: Optional[List[str]] = None
    tags_descriptions: Optional[Dict[str, str]] = None
