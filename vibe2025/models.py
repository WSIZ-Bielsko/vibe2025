from pydantic import BaseModel, Field


class ConversionResponse(BaseModel):
    """Currency conversion result."""
    result: float = Field(..., description="Converted amount")

    class Config:
        json_schema_extra = {
            "example": {
                "result": 110.25
            }
        }
