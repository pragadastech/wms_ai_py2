from pydantic import BaseModel
from typing import List

class BinCountItem(BaseModel):
    itemId: int
    itemName: str
    quantity: int

class BinCountRequest(BaseModel):
    action: str
    location: int
    binId: int
    binName: str
    locationName: str
    userName: str
    itemData: List[BinCountItem] 