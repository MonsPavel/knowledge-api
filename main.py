from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI(title="Knowledge API", version="0.1.0")

class NoteIn(BaseModel):
  title: str = Field(min_length=1, max_length=200)
  content: str = ""
  tags: list[str] = Field(default_factory=list)
  pinned: bool = False

class Note(NoteIn):
  id: int

notes: list[Note] = [
  Note(id=1, title="Python", tags=["python", "ml"], pinned=False),
  Note(id=2, title="FastAPI", tags=["python"], pinned=True),
  Note(id=3, title="RAG", tags=["ml", "ai"], pinned=True),
  Note(id=4, title="Vue", tags=["frontend"], pinned=False),
]

@app.get("/health")
def health() -> dict:
  return {"status": "ok"}

@app.get("/notes")
def list_notes(
    search: str | None = None,
    tag: str | None = None,
    sort: str = "created"
) -> list[Note]:
  result = notes.copy()

  if search is not None:
    result = [
      n for n in result
      if search.lower() in (n.title + " " + n.content).lower()
   ]

  if tag is not None:
    result = [ n for n in result if tag in n.tags ]

  if sort == "pinned":
    result = sorted(
      result,
      key=lambda n:(not n.pinned, n.id)
    )

  return result

@app.get("/notes/{note_id}/related")
def get_related_notes(note_id: int) -> list[Note]:
  result = []
  found = False

  for note in notes:
    if note.id == note_id:
      note_tags = note.tags
      found = True
      result = [n for n in notes if n.id != note_id]
      result = [n for n in result if set(n.tags) & set(note_tags)]

  if not found:
    raise HTTPException(status_code=404, detail="Note not found")

  return result

@app.post("/notes", status_code=201, response_model=Note)
def create_note(note: NoteIn) -> Note:
  item = Note(
    id = len(notes) + 1,
    ** note.model_dump()
  )
  notes.append(item)
  return item

@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int) -> Response:
  for note in notes:
    if note.id == note_id:
      notes.remove(note)
      return Response(status_code=204)

  raise HTTPException(status_code=404, detail="Note not found")

class NoteUpdate(BaseModel):
  title: str | None = Field(default=None, min_length=1, max_length=200)
  content: str | None = None

@app.patch("/notes/{note_id}")
def update_note(note_id: int, update: NoteUpdate) -> Note:
  for index, note in enumerate(notes):
    if note.id == note_id:
      changes = update.model_dump(exclude_unset=True)
      updated_note = note.model_copy(update=changes)
      notes[index] = updated_note
      return updated_note

  raise HTTPException(status_code=404, detail="Note not found")
