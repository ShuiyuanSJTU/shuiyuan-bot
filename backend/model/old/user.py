from dataclasses import dataclass
import dataclasses
from typing import Optional


@dataclass(init=False)
class ReplyToUser:
    username: str
    name: str
    avatar_template: str

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
