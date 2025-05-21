from pydantic import BaseModel
from typing import Dict, Any

class DataResponse(BaseModel):
    status: int = 200
    message: str
    total_records: int
    data: Dict[str, Any]
    progress: Dict[str, Any] = None