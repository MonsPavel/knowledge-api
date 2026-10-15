from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB

DATABASE_URL = (
    "postgresql+psycopg://postgres:dev@localhost:5434/knowledge"
)

engine = create_engine(DATABASE_URL, echo=True)

class Base(DeclarativeBase):
    pass

class NoteDB(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list[str]] = mapped_column(JSONB, default="[]")
    pinned: Mapped[bool] = mapped_column(default=False)

SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(engine)