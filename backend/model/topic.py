from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from .user import BasicUser

class Topic(BaseModel):
    id: int
    title: str
    fancy_title: str
    posts_count: int
    created_at: str
    views: int
    reply_count: int
    like_count: int
    last_posted_at: str
    visible: bool
    closed: bool
    archived: bool
    archetype: str
    slug: str
    category_id: int
    word_count: int
    deleted_at: Optional[str]
    user_id: int
    pinned_globally: bool
    pinned_at: Optional[str]
    pinned_until: Optional[str]
    unpinned: Optional[bool]
    pinned: bool
    highest_post_number: int
    deleted_by: Optional[int]
    has_deleted: bool
    bookmarked: bool
    participant_count: int
    queued_posts_count: int
    thumbnails: Optional[str]
    created_by: BasicUser
    last_poster: Optional[BasicUser] = None
    summarizable: bool
    pending_posts: List[Any]
    tags: List[str]
    tags_descriptions: Dict[str, str]
