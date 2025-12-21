from pydantic import BaseModel
from typing import List, Optional

class Component(BaseModel):
    name: str
    type: str
    properties: dict

class Page(BaseModel):
    title: str
    path: str
    components: List[Component]

class SiteStructure(BaseModel):
    pages: List[Page]
    navigation: List[dict]
