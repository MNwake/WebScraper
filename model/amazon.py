import uuid
from typing import Optional

from pydantic import BaseModel, Field

from utility.utils import Websites


class AmazonItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    price: Optional[float] = None  # Optional price field
    url: Optional[str] = None  # Optional url field
    match: Optional[str] = None  # Optional match field
    website: Websites = Field(default=Websites.AMAZON)
