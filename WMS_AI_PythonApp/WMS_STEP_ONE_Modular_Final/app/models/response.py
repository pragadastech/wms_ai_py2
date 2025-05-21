from pydantic import BaseModel
from typing import Any, Optional

class DataResponse(BaseModel):
    status: int = 200
    message: str
    total_records: int
    data: Any
    progress: Optional[Any] = None