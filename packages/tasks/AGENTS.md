# packages/tasks/AGENTS.md

<!-- Per spec §26.9 item 241 -->

**Purpose:** Scoped agent instructions for the tasks package. Per spec §26.9 item 241.

## Scope

This package defines interfaces for background task submission and handling. Workers (the execution layer) are an optional profile. This package must remain importable whether or not the worker profile is enabled.

## Interface Contracts

The Protocol interfaces in interfaces.py define the contract. Implementing code must satisfy the protocol without necessarily inheriting from it (duck typing). Test worker implementations against the interface, not a concrete class.

## Worker Profile Activation

The worker profile adds concrete implementations of TaskInterface (using Celery, ARQ, or RQ). To enable: set BROKER_URL in .env and enable the workers profile. Until then, InMemoryTaskInterface is used for development.

## Testing Without Workers

Use InMemoryTaskInterface in tests — it runs tasks synchronously without a broker. This allows service layer tests to verify task submission without a running broker. Mark integration tests that require a real broker with @pytest.mark.integration.
