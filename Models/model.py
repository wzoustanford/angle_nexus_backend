from pydantic import BaseModel

class APIData(BaseModel):
    name: str
    Key: str
    description: str
    api: str
class APIModel(BaseModel):
    company_profile_data: APIData
    another_topic: APIData