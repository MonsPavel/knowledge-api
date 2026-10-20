from fastapi import FastAPI, Response, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from knowledge_api.db import SessionLocal, NoteDB
from sqlalchemy import select, or_

from knowledge_api.errors import AppError, NotFoundError, ConflictError
from knowledge_api.classes.note import NoteIn, Note, NoteUpdate
from knowledge_api.classes.errors import ProblemDetails

import logging
app = FastAPI(
  title="Knowledge API",
  version="0.1.0",
    responses = {
      500: {
        "model": ProblemDetails,
        "description": "Внутренняя ошибка сервера"
      }
    }
)

logger = logging.getLogger(__name__)

def note_to_schema(item: NoteDB) -> Note:
  return Note(
    id=item.id,
    title=item.title,
    content=item.content,
    pinned=item.pinned,
    tags=item.tags
  )

@app.exception_handler(AppError)
def error_handler(request: Request, exc: AppError) -> Response:
  logger.warning("%r", exc)

  content = {
    "type": exc.error_type,
    "title": exc.title,
    "status": exc.status,
    "detail": exc.detail
  }

  return JSONResponse(
    status_code = exc.status,
    content = content,
    media_type = "application/problem+json"
  )

@app.exception_handler(Exception)
def exception_handler(request: Request, exc: Exception) -> Response:
  logger.exception("Неожиданная ошибка при обработке %s", request.url.path)

  content = {
    "type": "https://knowledge-api.dev/errors/server-error",
    "title": "Internal Server Error",
    "status": 500,
    "detail": "Произошла ошибка на сервере"
  }

  return JSONResponse(
    status_code=500,
    content=content,
    media_type="application/problem+json"
  )

@app.exception_handler(RequestValidationError)
def validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> Response:
    content = {
        "type": "https://knowledge-api.dev/errors/validation",
        "title": "Unprocessable Content",
        "status": 422,
        "detail": "Ошибка валидации запроса"
    }

    return JSONResponse(
      status_code = content["status"],
      content = content,
      media_type = "application/problem+json"
    )

@app.get("/health")
def health() -> dict:
  return {"status": "ok"}

@app.get(
  "/notes",
  responses= {
    422: {
      "model": ProblemDetails,
      "description": "Ошибка валидации запроса"
    }
  }
)

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


@app.get(
  "/notes/{note_id}",
  responses= {
    404: {
      "model": ProblemDetails,
      "description": "Заметка не найдена"
    },
    422: {
      "model": ProblemDetails,
      "description": "Ошибка валидации запроса"
    }
  }
)

def get_note_by_id(note_id: int) -> Note:
  with SessionLocal() as session:
    item = session.get(NoteDB, note_id)

    if item is None:
      raise NotFoundError(f"Заметка {note_id} не найдена")

    return note_to_schema(item)

@app.get(
  "/notes/{note_id}/related",
  responses= {
    404: {
      "model": ProblemDetails,
      "description": "Заметка не найдена"
    },
    422: {
      "model": ProblemDetails,
      "description": "Ошибка валидации запроса"
    }
  }
)
def get_related_notes(note_id: int) -> list[Note]:
  stmt = select(NoteDB)

  stmt = stmt.where(NoteDB.id != note_id)

  with SessionLocal() as session:
    item = session.get(NoteDB, note_id)

    if item is None:
      raise NotFoundError(f"Заметка {note_id} не найдена")

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

@app.post(
  "/notes",
  status_code=201,
  response_model=Note,
  responses= {
    409: {
      "model": ProblemDetails,
      "description": "Заметка с таким названием уже существует"
    },
    422: {
      "model": ProblemDetails,
      "description": "Ошибка валидации запроса"
    }
  }
)
def create_note(note: NoteIn) -> Note:
  stmt = select(NoteDB)
  stmt = stmt.where(NoteDB.title == note.title)

  with SessionLocal() as session:
    result = session.scalar(stmt)

    if result:
      raise ConflictError()

    else:
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



@app.delete(
  "/notes/{note_id}",
  status_code=204,
  responses= {
    404: {
      "model": ProblemDetails,
      "description": "Заметка не найдена"
    },
    422: {
      "model": ProblemDetails,
      "description": "Ошибка валидации запроса"
    }
  }
)

def delete_note(note_id: int) -> Response:
  with SessionLocal() as session:
    item = session.get(NoteDB, note_id)
    if item is not None:
      session.delete(item)
      session.commit()
      return Response(status_code=204)

  raise NotFoundError(f"Заметка {note_id} не найдена")

@app.patch(
"/notes/{note_id}",
  responses= {
    404: {
      "model": ProblemDetails,
      "description": "Заметка не найдена"
    },
    422: {
      "model": ProblemDetails,
      "description": "Ошибка валидации запроса"
    }
  }
)

def update_note(note_id: int, update: NoteUpdate) -> Note:
  with SessionLocal() as session:
    item = session.get(NoteDB, note_id)

    if item is None:
      raise NotFoundError(f"Заметка {note_id} не найдена")

    changes = update.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(item, field, value)

    session.commit()
    session.refresh(item)

    return note_to_schema(item)
