from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    preferred_subreddit: Optional[str] = "learnprogramming"

    class Config:
        from_attributes = True


class SubredditUpdate(BaseModel):
    subreddit: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class SourceBase(BaseModel):
    name: str
    url: str
    feed_type: str
    category: str
    icon: Optional[str] = None

class SourceCreate(SourceBase):
    pass

class SourceResponse(SourceBase):
    id: int

    class Config:
        from_attributes = True


class FeedItemResponse(BaseModel):
    title: str
    link: Optional[str] = None
    source: Optional[str] = None
    published: Optional[str] = None
    summary: Optional[str] = None
    extra: Optional[dict] = None

    class Config:
        from_attributes = True


class FavoriteCreate(BaseModel):
    feed_link: str
    feed_title: str
    feed_source: str
    feed_published: Optional[str] = None
    feed_summary: Optional[str] = None


class FavoriteResponse(BaseModel):
    id: int
    user_id: int
    feed_link: str
    feed_title: str
    feed_source: str
    feed_published: Optional[str] = None
    feed_summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
