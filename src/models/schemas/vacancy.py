import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator

from src.models.file_type import FileType
from src.models.schemas.s3 import PreSignedPostUrl
from src.models.state import VacancyState


class Vacancy(BaseModel):
    id: uuid.UUID
    title: str
    content: str
    poster: uuid.UUID | None
    state: VacancyState
    test_time: int

    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class VacancySmall(BaseModel):
    id: uuid.UUID
    title: str
    poster: uuid.UUID | None
    state: VacancyState

    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class VacancyCreate(BaseModel):
    title: str
    content: str
    state: VacancyState

    @field_validator('content')
    def content_must_be_valid(cls, value):
        if not value:
            raise ValueError("Публикация не может быть пустой")

        if len(value) > 32000:
            raise ValueError("Публикация не может содержать более 32000 символов")
        return value

    @field_validator('title')
    def title_must_be_valid(cls, value):
        if not value:
            raise ValueError("Заголовок не может быть пустым")

        if len(value) > 255:
            raise ValueError("Заголовок не может содержать больше 255 символов")
        return value


class VacancyUpdate(BaseModel):
    title: str = None
    content: str = None
    state: VacancyState = None

    class Config:
        extra = 'ignore'

    @field_validator('content')
    def content_must_be_valid(cls, value):
        if value and len(value) > 32000:
            raise ValueError("Публикация не может содержать больше 32000 символов")
        return value

    @field_validator('title')
    def title_must_be_valid(cls, value):
        if value and len(value) > 255:
            raise ValueError("Заголовок не может содержать больше 255 символов")
        return value


class VacancyFile(BaseModel):
    id: uuid.UUID
    filename: str
    vacancy_id: uuid.UUID
    content_type: str
    is_uploaded: bool

    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True


class VacancyFileItem(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    url: str

    created_at: datetime
    updated_at: datetime | None


class VacancyFileCreate(BaseModel):
    filename: str
    content_type: FileType


class VacancyFileUpload(BaseModel):
    file_id: uuid.UUID
    upload_url: PreSignedPostUrl
