from pydantic import BaseModel


class UserOut(BaseModel):
    id: int
    username: str
    role: str


class UserIn(BaseModel):
    username: str
    password: str
