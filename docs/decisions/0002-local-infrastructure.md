# ADR 0002: Local Infrastructure

## Status

Accepted

## Context

During local development, PostgreSQL and Qdrant are containerised with Docker Compose, while the application itself runs natively on the developer's machine.

This setup intentionally separates the application development loop from its infrastructure dependencies. Running the application natively provides a fast feedback loop: code changes can be made and tested without rebuilding or restarting the application container.

At the same time, containerising PostgreSQL and Qdrant provides reproducible infrastructure. Every developer can run the same database and vector-database versions and configuration through Docker Compose rather than installing and configuring those dependencies manually.

The trade-off is therefore between **feedback-loop speed** and **infrastructure reproducibility**. We prioritise a fast native application feedback loop during development while using containers for reproducible infrastructure dependencies.

## Decision

For local development:

* PostgreSQL runs in Docker.
* Qdrant runs in Docker.
* The application runs natively on the developer's machine.
* Docker Compose manages the infrastructure dependencies, ports, and persistent volumes.
* Local secrets remain in `.env` and are not committed; `.env.example` documents the required variables.

## Future Plan

At M10, we plan to containerise the application itself.

At that point the development/runtime architecture will move toward:

```text
Application container
        │
        ├── PostgreSQL container
        │
        └── Qdrant container
```

The application will communicate with the infrastructure services through the Docker Compose network using service names rather than `localhost`.

The current native-application approach is therefore a deliberate development-stage decision, not the intended final deployment architecture.
