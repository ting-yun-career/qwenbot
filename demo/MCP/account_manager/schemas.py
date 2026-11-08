from pydantic import BaseModel


class Account(BaseModel):
    id: str
    name: str
    active: bool
