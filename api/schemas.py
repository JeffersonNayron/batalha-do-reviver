from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Annotated

class OrgOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str
    name: str
    description: str
    instagram: str

class OrgIn(BaseModel):
    slug: str = Field(min_length=2, max_length=120, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    name: str = Field(min_length=2, max_length=160)
    description: str = Field(default='', max_length=4000)
    instagram: str = Field(default='', max_length=255)

class EventIn(BaseModel):
    slug: str = Field(min_length=3, max_length=160, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    organization_id: int
    title: str = Field(min_length=3, max_length=200)
    start_at: datetime
    venue: str = Field(min_length=3, max_length=200)
    city: str = Field(default='São Luís', max_length=100)
    state: str = Field(default='MA', min_length=2, max_length=2)
    description: str = Field(default='', max_length=5000)
    capacity: int | None = Field(default=None, ge=1, le=100000)
    champion_prize: int | None = Field(default=None, ge=0)
    runner_up_prize: int | None = Field(default=None, ge=0)
    registration: str = Field(default='', max_length=160)
    free: bool = True
    published: bool = False
    cover_url: str = Field(default='', max_length=512)
    @field_validator('cover_url')
    @classmethod
    def validate_cover(cls, value):
        if value and not (value.startswith('https://') or value.startswith('/assets/')):
            raise ValueError('A imagem deve usar HTTPS ou o diretório de assets')
        return value

class EventOut(EventIn):
    model_config = ConfigDict(from_attributes=True)
    id: int
    organization: OrgOut

class MCIn(BaseModel):
    slug: str = Field(min_length=2, max_length=160, pattern=r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
    stage_name: str = Field(min_length=2, max_length=140)
    bio: str = Field(default='', max_length=5000)
    instagram: str = Field(default='', max_length=255)
    photo_url: str = Field(default='', max_length=512)
    city: str = Field(default='São Luís', max_length=100)
    published: bool = False
    @field_validator('photo_url')
    @classmethod
    def validate_photo(cls, value):
        if value and not (value.startswith('https://') or value.startswith('/assets/')):
            raise ValueError('A foto deve usar HTTPS ou o diretório de assets')
        return value

class MCOut(MCIn):
    model_config = ConfigDict(from_attributes=True)
    id: int

class Login(BaseModel):
    username: str = Field(default="", max_length=255)
    password: str = Field(min_length=1, max_length=256)

class ResetRequest(BaseModel):
    username: str = Field(min_length=1,max_length=255)

class ResetConfirm(BaseModel):
    token: str = Field(min_length=20,max_length=128)
    password: str = Field(min_length=12,max_length=256)
