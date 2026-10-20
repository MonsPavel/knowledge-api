from pydantic import BaseModel, Field, ConfigDict, model_validator

class NoteIn(BaseModel):
  title: str = Field(min_length=1, max_length=200)
  content: str = ""
  tags: list[str] = Field(default_factory=list)
  pinned: bool = False

class Note(NoteIn):
  model_config = ConfigDict(from_attributes=True)

  id: int

class NoteUpdate(BaseModel):
  title: str | None = None
  content: str | None = None
  tags: list[str] | None = None
  pinned: bool | None = None

  @model_validator(mode="after")
  def reject_nulls(self):
    for field in self.model_fields_set:
      if getattr(self, field) is None:
        raise ValueError(f"{field} cannot be null")
    return self