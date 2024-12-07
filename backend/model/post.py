from typing import Optional, List, Dict, Any
from .user import BasicUser
from pydantic import BaseModel


class Post(BaseModel):
    id: int
    topic_id: int
    name: Optional[str]
    username: str
    avatar_template: str
    created_at: str
    cooked: str
    post_number: int
    post_type: int
    updated_at: str
    reply_count: int
    reply_to_post_number: Optional[int]
    quote_count: int
    incoming_link_count: int
    reads: int
    score: float
    display_username: Optional[str]
    primary_group_name: Optional[str] = None
    flair_name: Optional[str] = None
    flair_group_id: Optional[int] = None
    version: int
    user_title: Optional[str] = None
    reply_to_user: Optional[BasicUser] = None
    raw: str
    moderator: bool
    admin: bool
    staff: bool
    user_id: int
    hidden: bool
    trust_level: int
    deleted_at: Optional[str]
    user_deleted: bool
    edit_reason: Optional[str]
    wiki: bool
    accepted_answer: Optional[bool] = None
    topic_accepted_answer: Optional[bool] = None


class PostAPI(Post):
    actions_summary: List[Dict[str, Any]]
    retorts: List[Dict[str, Any]]
    my_retorts: List[Dict[str, Any]]


class PostWebhook(Post):
    topic_slug: str
    topic_title: str
    topic_posts_count: int
    topic_filtered_posts_count: int
    topic_archetype: str
    category_slug: str
    user_cakedate: str
    user_birthdate: str
    category_id: int
    title_is_group: bool
    reviewable_id: Optional[int]
    reviewable_score_count: int
    reviewable_score_pending_count: int
