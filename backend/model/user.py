from dataclasses import dataclass
import dataclasses
from typing import Optional
from pydantic import BaseModel


class ReplyToUser(BaseModel):
    username: str
    name: str
    avatar_template: str
