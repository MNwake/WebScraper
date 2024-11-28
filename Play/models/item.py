from typing import Optional

from pydantic import BaseModel, Field

from Play.models.amazon import AmazonItem
from Utility.utils import Websites


class Product(BaseModel):
    id: str
    website: Websites = Field()
    brand: str
    name: str
    original_price: Optional[float]
    current_price: Optional[float]
    dollar_off: Optional[float] = 0.0
    percentage_off: Optional[float] = 0.0
    department: Optional[str]
    image_url: str
    url: str
    amazon: Optional[AmazonItem] = None

    @property
    def search_query(self) -> str:
        return f"{self.brand} {self.name}"
