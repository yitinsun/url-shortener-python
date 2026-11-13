"""Frozen HTTP bodies. Field names on the wire are camelCase."""

from pydantic import BaseModel, ConfigDict, Field


class ShortenRequest(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)
    long_url: str = Field(alias="longUrl")
    ttl_in_days: int | None = Field(default=None, alias="ttlInDays")


class ShortenResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)
    long_url: str = Field(alias="longUrl")
    short_url: str = Field(alias="shortUrl")
    short_code: str = Field(alias="shortCode")
    expires_at: str = Field(alias="expiresAt")


class ErrorResponse(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True)
    status: int
    error: str
    message: str
    short_code: str | None = Field(default=None, alias="shortCode")
