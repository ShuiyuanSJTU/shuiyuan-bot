from dataclasses import dataclass
import dataclasses
from typing import Optional, Union, get_args
from .user import ReplyToUser
"""
{
    "id": 3512599,
    "name": "二酱让我走吧😭",
    "username": "包图第一鸽王",
    "avatar_template": "/user_avatar/shuiyuan.sjtu.edu.cn/包图第一鸽王/{size}/722775_2.png",
    "created_at": "2024-03-30T14:23:26.523Z",
    "cooked": "<p>建议看看系统解剖学突击一下 <img src=\"//shuiyuan.s3.jcloud.sjtu.edu.cn/original/4X/d/f/9/df999bace486e7cbeeb50c9fb48e6aaf0d5dd9e5.png?v=12\" title=\":huaji:\" class=\"emoji emoji-custom\" alt=\":huaji:\" loading=\"lazy\" width=\"20\" height=\"20\"></p>",
    "post_number": 12,
    "post_type": 1,
    "updated_at": "2024-03-30T14:23:26.523Z",
    "reply_count": 0,
    "reply_to_post_number": null,
    "quote_count": 0,
    "incoming_link_count": 0,
    "reads": 0,
    "score": 0,
    "topic_id": 253423,
    "topic_slug": "topic",
    "topic_title": "人体解剖生理学推荐选修吗",
    "category_id": 90,
    "display_username": "二酱让我走吧😭",
    "primary_group_name": null,
    "flair_name": null,
    "flair_group_id": null,
    "version": 1,
    "user_title": "谈笑风生",
    "title_is_group": false,
    "bookmarked": false,
    "raw": "建议看看系统解剖学突击一下 :huaji:",
    "moderator": false,
    "admin": false,
    "staff": false,
    "user_id": 72587,
    "hidden": false,
    "trust_level": 3,
    "deleted_at": null,
    "user_deleted": false,
    "edit_reason": null,
    "wiki": false,
    "reviewable_id": null,
    "reviewable_score_count": 0,
    "reviewable_score_pending_count": 0,
    "topic_posts_count": 12,
    "topic_filtered_posts_count": 12,
    "topic_archetype": "regular",
    "category_slug": "exam-experience",
    "user_cakedate": "2023-07-29",
    "user_birthdate": "1904-03-17",
    "can_accept_answer": true,
    "can_unaccept_answer": false,
    "accepted_answer": false,
    "topic_accepted_answer": false
  }
"""


@dataclass(init=False)
class Post:
    id: int
    name: str
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
    score: int
    topic_id: int
    topic_slug: str
    topic_title: str
    category_id: int
    display_username: str
    primary_group_name: Optional[str]
    flair_name: Optional[str]
    flair_group_id: Optional[int]
    version: int
    user_title: str
    title_is_group: bool
    reply_to_user: Optional[ReplyToUser]
    # bookmarked: bool
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
    reviewable_id: Optional[int]
    reviewable_score_count: int
    reviewable_score_pending_count: int
    topic_posts_count: int
    topic_filtered_posts_count: int
    topic_archetype: str
    category_slug: str
    user_cakedate: str
    user_birthdate: str
    # can_accept_answer: bool
    # can_unaccept_answer: bool
    accepted_answer: bool
    topic_accepted_answer: bool

    def __init__(self, **kwargs):
        for field in dataclasses.fields(self):
            value = kwargs.get(field.name)
            if value is not None and isinstance(value, dict):
                print(field)
                if dataclasses.is_dataclass(field.type):
                    setattr(self, field.name, field.type(**value))
                if getattr(field.type, '__origin__', None) is Union \
                        and dataclasses.is_dataclass(get_args(field.type)[0]):
                    setattr(self, field.name, get_args(field.type)[0](**value))
                else:
                    setattr(self, field.name, value)
            else:
                setattr(self, field.name, None)
