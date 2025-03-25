from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class DatasetMetadata(BaseModel):
    filename: str
    upload_date: datetime
    rows_count: int
    columns: List[str]

class StatisticsResponse(BaseModel):
    count: int
    columns: List[str]
    numeric_stats: Dict[str, Dict[str, float]]
    missing_values: Dict[str, int]

class FilterRequest(BaseModel):
    column: str
    value: Any
    operator: str = "equals"  # equals, greater_than, less_than, contains

class ErrorResponse(BaseModel):
    detail: str
    status_code: int

class SuccessResponse(BaseModel):
    message: str
    data: Optional[Any] = None