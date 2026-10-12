from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI(title="Knowledge API", version="0.1.0")

class NoteIn(BaseModel):
  title: str = Field(min_length=1, max_length=200)
  content: str = ""

class Note(BaseModel):
  id: int
  title: str
  content: str = ""

notes: list[dict] = [
  {
    "id": 1,
    "title": "Note 1"
  },
  {
    "id": 2,
    "title": "Note 2"
  }
]

@app.get("/health")
def health() -> dict:
  return {"status": "ok"}

@app.get("/notes")
def list_notes(search: str | None = None) -> list[dict]:
  if search is None:
    return notes

  result = []

  for note in notes:
    text = note["title"] + " " + note["content"]

    if search.lower() in text.lower():
      result.append(note)

  return result


@app.post("/notes", status_code=201)
def create_note(note: NoteIn) -> dict:
  item = {
    "id": len(notes) + 1,
    **note.model_dump()
  }
  notes.append(item)
  return item

@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int) -> Response:
  for note in notes:
    if note["id"] == note_id:
      notes.remove(note)
      return Response(status_code=204)

  raise HTTPException(status_code=404, detail="Note not found")

class NoteUpdate(BaseModel):
  title: str | None = None
  content: str | None = None

@app.patch("/notes/{note_id}")
def update_note(note_id: int, update: NoteUpdate) -> dict:
  for note in notes:
    if note["id"] == note_id:
      changes = update.model_dump(exclude_unset=True)
      note.update(changes)
      return note

  raise HTTPException(status_code=404, detail="Note not found")
