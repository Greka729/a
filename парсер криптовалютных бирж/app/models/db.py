from datetime import datetime
from typing import Optional

from sqlalchemy import create_engine, String, DateTime, Numeric
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.utils.config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass

class Price(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    symbol: Mapped[str] = mapped_column(String(16), index=True)
    price: Mapped[Optional[float]] = mapped_column(Numeric(20, 8))
    volume_24h: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    market_cap: Mapped[Optional[float]] = mapped_column(Numeric(24, 2), nullable=True)
    source: Mapped[str] = mapped_column(String(64))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


