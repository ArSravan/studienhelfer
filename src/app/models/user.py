import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid= True),
        primary_key= True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        unique = True,
        index = True,
        nullable = False,
    )

    passwor_hash : Mapped[str] = mapped_column(
        nullable = False
    )

    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    updated_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    conversations : Mapped[list["Conversation"]] = relationship(
        back_populates="user",
    )