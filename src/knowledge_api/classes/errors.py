from pydantic import BaseModel

class ProblemDetails(BaseModel):
  type: str
  title: str
  status: int
  detail: str