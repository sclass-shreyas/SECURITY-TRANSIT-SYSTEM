from pydantic import BaseModel, ConfigDict


class ZoneIn(BaseModel):
    zone_name: str
    polygon_points_json: list[list[int]]


class ZoneOut(BaseModel):
    id: int
    zone_name: str
    polygon_points_json: list[list[int]]

    model_config = ConfigDict(from_attributes=True)
