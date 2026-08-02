from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int


class PageParams(BaseModel):
    page: int = 1
    page_size: int = 20


class ListResponse(BaseModel, Generic[T]):
    data: list[T]
    meta: PageMeta


class ItemResponse(BaseModel, Generic[T]):
    data: T


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
