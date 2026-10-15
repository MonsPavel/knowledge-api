from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field, ConfigDict, model_validator

from knowledge_api.db import SessionLocal, NoteDB
from sqlalchemy import select, or_

app = FastAPI(title="Knowledge API", version="0.1.0")

class NoteIn(BaseModel):
  title: str = Field(min_length=1, max_length=200)
  content: str = ""
  tags: list[str] = Field(default_factory=list)
  pinned: bool = False

class Note(NoteIn):
  model_config = ConfigDict(from_attributes=True)

  id: int

def note_to_schema(item: NoteDB) -> Note:
  return Note(
    id=item.id,
    title=item.title,
    content=item.content,
    pinned=item.pinned,
    tags=item.tags
  )

@app.get("/health")
def health() -> dict:
  return {"status": "ok"}

@app.get("/notes")
def list_notes(
    search: str | None = None,
    tag: str | None = None,
    sort: str = "created"
) -> list[Note]:
  stmt = select(NoteDB)

  if search:
    stmt = stmt.where(NoteDB.title.ilike(f"%{search}%") | (NoteDB.content.ilike(f"%{search}%")))

  if sort == "pinned":
    stmt = stmt.order_by(NoteDB.pinned.desc(), NoteDB.id)
  elif sort == "created":
    stmt = stmt.order_by(NoteDB.id)

  if tag:
    stmt = stmt.where(NoteDB.tags.contains([tag]))

  with SessionLocal() as session:
    result = session.scalars(stmt).all()

    return [ note_to_schema(r) for r in result ]


@app.get("/notes/{note_id}")
def get_note_by_id(note_id: int) -> Note:
  with SessionLocal() as session:
    item = session.get(NoteDB, note_id)

    if item is None:
      raise HTTPException(status_code=404, detail="Note not found")

    return note_to_schema(item)

@app.get("/notes/{note_id}/related")
def get_related_notes(note_id: int) -> list[Note]:
  stmt = select(NoteDB)

  stmt = stmt.where(NoteDB.id != note_id)

  with SessionLocal() as session:
    item = session.get(NoteDB, note_id)

    if item is None:
      raise HTTPException(status_code=404, detail="Note not found")

    conditions = []

    if not item.tags:
      return  []

    for tag in item.tags:
      conditions.append(NoteDB.tags.contains([tag]))

    stmt = stmt.where(or_(*conditions))

    all_notes = session.scalars(stmt).all()

    return [
      note_to_schema(r)
      for r in all_notes
    ]

@app.post("/notes", status_code=201, response_model=Note)
def create_note(note: NoteIn) -> Note:
  with SessionLocal() as session:
    item = NoteDB(
      title=note.title,
      content=note.content,
      pinned=note.pinned,
      tags=note.tags
    )

    session.add(item)
    session.commit()
    session.refresh(item)

  return note_to_schema(item)

@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int) -> Response:
  with SessionLocal() as session:
    item = session.get(NoteDB, note_id)
    if item is not None:
      session.delete(item)
      session.commit()
      return Response(status_code=204)

  raise HTTPException(status_code=404, detail="Note not found")

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

@app.patch("/notes/{note_id}")
def update_note(note_id: int, update: NoteUpdate) -> Note:
  with SessionLocal() as session:
    item = session.get(NoteDB, note_id)

    if item is None:
      raise HTTPException(status_code=404, detail="Note not found")

    changes = update.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(item, field, value)

    session.commit()
    session.refresh(item)

    return note_to_schema(item)
