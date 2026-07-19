from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar('T')

class UnifiedResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
