from dataclasses import dataclass
import dataclasses
from typing import Optional
from pydantic import BaseModel


class BasicUser(BaseModel):
    id: Optional[int] = None
    username: str
    name: Optional[str] = None
    avatar_template: Optional[str] = None
