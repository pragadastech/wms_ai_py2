from pydantic import BaseModel, Field
from typing import List

class ItemData(BaseModel):
    itemId: int = Field(..., description="The ID of the item")
    quantity: int = Field(..., description="The quantity of the item", ge=0)

class BinCountRequest(BaseModel):
    action: str = Field(..., description="The action to perform", pattern="^binCount$")
    location: int = Field(..., description="The location ID")
    binId: int = Field(..., description="The bin ID")
    itemData: List[ItemData] = Field(..., description="List of items and their quantities")

    class Config:
        json_schema_extra = {
            "example": {
                "action": "binCount",
                "location": 10,
                "binId": 1234,
                "itemData": [
                    {
                        "itemId": 3542,
                        "quantity": 2
                    },
                    {
                        "itemId": 62063,
                        "quantity": 2
                    },
                    {
                        "itemId": 62163,
                        "quantity": 10
                    }
                ]
            }
        } 