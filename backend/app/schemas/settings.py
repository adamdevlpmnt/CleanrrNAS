from pydantic import BaseModel, ConfigDict
from datetime import datetime

class SettingsResponse(BaseModel):
    key: str
    value: str
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SettingsUpdateRequest(BaseModel):
    value: str
