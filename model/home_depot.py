import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

from utility.utils import Websites


class Identifier(BaseModel):
    storeSkuNumber: Optional[str]
    canonicalUrl: str
    brandName: Optional[str]
    itemId: str
    productLabel: str
    productType: str


class Image(BaseModel):
    url: str
    type: str
    subType: str


class Media(BaseModel):
    images: List[Image]


class Promotion(BaseModel):
    type: Optional[str] = None
    description: Optional[str] = None
    dollarOff: Optional[float] = 0.0
    percentageOff: Optional[float] = 0.0
    promotionTag: Optional[str] = None
    savingsCenter: Optional[str] = None
    savingsCenterPromos: Optional[str] = None
    specialBuySavings: Optional[float] = None
    specialBuyDollarOff: Optional[float] = None
    specialBuyPercentageOff: Optional[float] = None
    dates: Optional[str] = None
    __typename: Optional[str] = None


class Pricing(BaseModel):
    value: Optional[float] = None
    original: Optional[float] = None
    promotion: Optional[Promotion] = None


class RatingsReviews(BaseModel):
    averageRating: Optional[str] = None
    totalReviews: Optional[str] = None


class Reviews(BaseModel):
    ratingsReviews: RatingsReviews


class Inventory(BaseModel):
    isOutOfStock: bool
    isInStock: bool
    isLimitedQuantity: bool
    isUnavailable: bool
    quantity: int
    maxAllowedBopisQty: Optional[int] = None
    minAllowedBopisQty: Optional[int] = None
    __typename: Optional[str] = None


class Location(BaseModel):
    curbsidePickupFlag: Optional[bool] = None
    isBuyInStoreCheckNearBy: Optional[bool] = None
    distance: Optional[float] = None
    inventory: Inventory
    isAnchor: bool
    locationId: str
    state: Optional[str] = None
    storeName: Optional[str] = None
    storePhone: Optional[str] = None
    type: str
    __typename: Optional[str] = None


class Service(BaseModel):
    deliveryTimeline: Optional[str] = None
    deliveryDates: Optional[str] = None
    deliveryCharge: Optional[float] = None
    dynamicEta: Optional[str] = None
    hasFreeShipping: bool
    freeDeliveryThreshold: Optional[float] = None
    locations: List[Location]
    type: str
    totalCharge: Optional[float] = None
    deliveryMessage: Optional[str] = None
    __typename: Optional[str] = None


class FulfillmentOption(BaseModel):
    type: str
    fulfillable: bool
    services: List[Service]
    __typename: Optional[str] = None


class Fulfillment(BaseModel):
    anchorStoreStatus: bool
    anchorStoreStatusType: str
    backordered: bool
    backorderedShipDate: Optional[str] = None
    bossExcludedShipStates: Optional[str] = None
    excludedShipStates: Optional[str] = None
    seasonStatusEligible: Optional[bool] = None
    fulfillmentOptions: Optional[List[FulfillmentOption]] = None
    __typename: Optional[str] = None


class GlobalCustomConfigurator(BaseModel):
    customExperience: str
    __typename: str


class ProductSubType(BaseModel):
    name: str
    link: Optional[str] = None
    __typename: Optional[str] = None


class Swatch(BaseModel):
    isSelected: bool
    itemId: str
    label: str
    swatchImgUrl: str
    url: str
    value: str
    __typename: str


class SponsoredMetadata(BaseModel):
    campaignId: str
    campaignName: str
    adGroupId: str
    adGroupName: str
    adId: str
    adName: str
    __typename: str


class SponsoredBeacon(BaseModel):
    onClickBeacon: str
    __typename: str


class Info(BaseModel):
    sponsoredMetadata: Optional[dict] = None
    sponsoredBeacon: Optional[dict] = None
    swatches: List[Swatch] = []
    hidePrice: bool = False
    ecoRebate: bool = False
    quantityLimit: Optional[int] = None
    categoryHierarchy: Optional[List[str]] = []
    sskMin: Optional[float] = None
    sskMax: Optional[float] = None
    unitOfMeasureCoverage: Optional[str] = None
    wasMaxPriceRange: Optional[float] = None
    wasMinPriceRange: Optional[float] = None
    productSubType: Optional[ProductSubType] = None
    customerSignal: Optional[str] = None
    isBuryProduct: Optional[bool] = None
    isGenericProduct: Optional[bool] = None
    returnable: Optional[str] = None
    isLiveGoodsProduct: bool = False
    isSponsored: Optional[bool] = None
    globalCustomConfigurator: Optional[GlobalCustomConfigurator] = None
    augmentedReality: bool = False
    hasSubscription: bool = False
    samplesAvailable: bool = False
    totalNumberOfOptions: Optional[int] = None
    classNumber: Optional[str] = None
    productDepartment: Optional[str] = None
    __typename: Optional[str] = None


class HomeDepotItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    identifiers: Identifier
    media: Media
    info: Info
    pricing: Optional[Pricing]
    reviews: Reviews
    fulfillment: Fulfillment
    website: Websites = Field(default=Websites.HOME_DEPOT)

    @property
    def search_query(self) -> str:
        return f"site:amazon.com, {self.identifiers.brandName} {self.identifiers.productLabel}"


class HomeDepotItemList(BaseModel):
    items: List[HomeDepotItem]
