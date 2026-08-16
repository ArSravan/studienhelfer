# ADR 0003: Schema Design Decisions

* **Status:** Accepted
* **Date:** 2026-08-16

## Context

The application stores users, conversations belonging to users, and messages belonging to conversations.

The schema needs to support private user-owned conversation data, predictable application behavior around timestamps and message roles, and account deletion without leaving dependent conversation data behind.

The main schema decisions concern primary key design, message roles, timestamps, message ordering, and deletion behavior.

## Decisions

### 1. UUID primary keys

All primary keys use PostgreSQL UUIDs generated with UUID4.

We chose UUIDs instead of sequential integer IDs because identifiers may be exposed through API endpoints and UUIDs make simple identifier enumeration substantially harder.

UUIDs are not considered an authorization mechanism. API endpoints must still verify that the authenticated user owns the requested resource.

**Tradeoff:** UUIDs are larger and less human-readable than integer IDs, but the reduced predictability is useful for externally exposed resource identifiers.

### 2. Enum for message roles

Messages use a `MessageRole` enum with two values:

* `user`
* `assistant`

The database stores the enum values rather than the Python enum member names.

This prevents arbitrary strings from being used as message roles and makes the allowed message states explicit.

**Tradeoff:** Adding or changing roles requires a schema/application change rather than simply accepting another string.

### 3. Timezone-aware timestamps and UTC

All creation and update timestamps use timezone-aware PostgreSQL timestamps (`TIMESTAMPTZ` semantics).

The application treats UTC as the canonical time representation. User-local time is handled at the presentation layer.

This avoids ambiguity when users or services operate across different time zones.

**Tradeoff:** Developers must use timezone-aware datetimes consistently rather than mixing naive and timezone-aware values.

### 4. Message ordering by `created_at`

Messages are ordered using their `created_at` timestamp rather than maintaining a separate per-conversation sequence column.

This avoids maintaining redundant ordering state and is sufficient for the initial application requirements.

If deterministic ordering is required when timestamps are equal, `message_id` can be used as a secondary ordering key.

**Tradeoff:** Timestamp ordering requires care around equal timestamps and does not provide an explicit logical sequence number.

### 5. Cascading deletion of user-owned data

A user owns conversations, and a conversation owns messages.

Foreign keys therefore use database-level `ON DELETE CASCADE`:

```text
User
  ↓ CASCADE
Conversation
  ↓ CASCADE
Message
```

The SQLAlchemy relationships also use ORM cascade configuration, with `passive_deletes=True` so the ORM can defer unloaded child deletion to PostgreSQL.

This design supports an account deletion operation in which deleting the user removes their associated private conversations and messages.

The decision is appropriate for the application's current requirement that user-owned conversational data be erased with the account.

**Tradeoff:** Deletion is destructive and cannot be recovered through the database after it has occurred. If a future requirement introduces a grace period or recoverable account deletion, a soft-delete approach such as `deleted_at` followed by scheduled hard deletion can be introduced.

Database cascading is considered part of the data-integrity design, but GDPR compliance is not guaranteed by cascading alone. Backup retention, logs, external processors, and other data stores must be addressed separately.

## Consequences

The resulting ownership model is:

```text
User
 └── Conversation
      └── Message
```

The database enforces required relationships and cascading deletion, while the ORM represents the same ownership model in Python.

The schema is intentionally simple for the initial application. More advanced requirements such as soft deletion, message revisions, archival, or strict logical sequencing can be introduced later as separate design decisions.
