import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Enum as SAEnum, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .conversation import Conversation

class MessageRole(str, Enum):
    USER =  "user"
    ASSISTANT = "assistant"

class Message(Base):
    __tablename__ = "messages"

    message_id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default= uuid.uuid4,
    )

    conversation_id : Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "conversations.conversation_id",
            ondelete="CASCADE",
        ),
         nullable=False,
        index=True,
    )

    role : Mapped[MessageRole] = mapped_column(
        SAEnum(
            MessageRole,
            values_callable= lambda enum: [member.value for member in enum],
        ),
        nullable=False,
    )

    content : Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default= func.now(),
    )

    updated_at : Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default= func.now(),
        onupdate= func.now(),
    )

    conversation : Mapped["Conversation"] = relationship(
        back_populates= "messages",
    )