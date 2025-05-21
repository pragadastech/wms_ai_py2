from pydantic import BaseModel
from typing import List

class BinCountItem(BaseModel):
    itemId: int
    quantity: int

class BinCountRequest(BaseModel):
    action: str
    location: int
    binId: int
    itemData: List[BinCountItem] 