from pydantic import BaseModel, field_validator, Field
from typing import Optional
from enum import Enum
import random

class ObjectDetection(BaseModel):
    """
    Schema for basic object detection in a photo.
    """
    object_name: str
    confidence: float
    color: str

class WasteCategory(str, Enum):
    PAPER = "Paper"
    PLASTIC = "Plastic"
    METAL = "Metal"
    GLASS = "Glass"
    ORGANIC = "Organic"
    BATTERY = "Battery"
    E_WASTE = "E-waste"
    OTHER = "Other"

class WasteClassification(BaseModel):
    """
    Schema for waste classification.
    """
    item_name: str
    material: str
    category: WasteCategory
    description: str = Field(..., min_length=50)
    rewards: int = Field(default_factory=lambda: random.randint(1, 10))

    @field_validator('category', mode='before')
    @classmethod
    def case_insensitive_category(cls, v: str) -> str:
        if isinstance(v, str):
            # Try to match case-insensitively
            for cat in WasteCategory:
                if cat.value.lower() == v.lower():
                    return cat.value
        return v

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v or len(v.strip()) < 5:
            raise ValueError("Описание обязательно и должно быть подробным!")
        return v

