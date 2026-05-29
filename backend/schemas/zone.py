from pydantic import BaseModel, ConfigDict, Field


class ZoneIn(BaseModel):
    zone_name: str = Field(min_length=1, max_length=120)
    polygon_points_json: list[list[int]] = Field(min_length=3)


class ZoneOut(BaseModel):
    id: int
    zone_name: str
    polygon_points_json: list[list[int]]

    model_config = ConfigDict(from_attributes=True)
