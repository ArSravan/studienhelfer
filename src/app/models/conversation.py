import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from .base import Base

if TYPE_CHECKING:
    from .message import Message
    from .user import User

class Conversation(Base):
    __tablename__ = "conversations"

    Conversation_id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id"),
        index = True,
    ) 

    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

    updated_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True)
    )

    user: Mapped["User"] = relationship(
        back_populates= "conversations",
    )

    messages : Mapped[list["Message"]] = relationship(
        back_populates= "conversation",
    )