from pydantic import BaseModel
from typing import List, Dict

class Color(BaseModel):
    name: str
    hex_code: str

class Typography(BaseModel):
    font_family: str
    font_size: str
    font_weight: str

class DesignTokens(BaseModel):
    colors: List[Color]
    typography: List[Typography]
    spacing: Dict[str, str]
