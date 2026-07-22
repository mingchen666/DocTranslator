# Configurable Translation Queue Backend Design

Date: 2026-07-22

## Goal

Allow a deployment administrator to choose between the existing database
translation queue and Celery with Redis. Single-machine deployments must not
require Redis. Multi-user deployments may enable Celery without changing the
translation APIs, task records, batch behavior, or frontend.

This is a deployment-level setting. End users cannot choose a queue backend,
and the backend cannot be changed at runtime without restarting the services.

## Configuration

Add one required-choice setting with a backwards-compatible default:

```env
TRANSLATION_QUEUE_BACKEND=database
```

Supported values are:

- `database`: use the existing `jobs` table and `python worker.py`.
- `celery`: publish translation tasks to Redis and execute them with Celery.

Celery mode also requires:

```env
CELERY_BROKER_URL=redis://redis:6379/0
```

The application fails at startup when the queue backend value is invalid, or
when Celery mode is selected without a broker URL. Database mode does not
import Celery during normal application startup and does not connect to Redis.

Celery results are not stored in Redis. The existing `translate` and
`translate_batch` tables remain the source of truth, so Celery tasks use
`ignore_result` behavior.

## Queue Interface

Keep `enqueue_translation(task_id, batch_id=None, commit=True)` as the common
application entry point. It selects an implementation from
`TRANSLATION_QUEUE_BACKEND`:

- The database implementation preserves the current durable `jobs` table
  behavior.
- The Celery implementation sends a task containing `translate_id` and the
  optional `batch_id` to the appropriate Celery queue.

Single-file, batch, ZIP, MCP, restart, and admin code continue calling the same
function. They do not import or call Celery directly.

Queue selection remains based on the source extension:

- Ordinary documents use the `translation.default` queue.
- PDF documents use the `translation.pdf` queue.

Every Celery message uses a deterministic task identifier based on the
translation ID. Before execution, the task reloads the `Translate` record and
returns without translating when it is already `done`, `failed`, deleted, or
missing. A normal duplicate delivery also returns when the record is already
`process`. A broker-redelivered message may reclaim `process` after Celery has
cancelled the previous execution because its connection or worker was lost.

## Celery Execution

Celery tasks call the existing synchronous `TranslateEngine.run()` method.
They do not duplicate document translation logic.

Required Celery reliability settings:

- acknowledge tasks after execution;
- reject and requeue work when a worker process is lost;
- cancel long-running tasks when the broker connection is lost;
- prefetch one task per worker slot;
- use a Redis visibility timeout longer than the maximum supported document
  translation time;
- cap infrastructure retries and preserve the final failure reason in the
  `Translate` record.

Run ordinary documents with concurrency two and PDF documents with concurrency
one. These limits are enforced by workers consuming their respective queues.
Deployments that start additional worker replicas intentionally increase total
concurrency and must account for model-provider limits and available memory.

## Failure Behavior

In database mode, enqueue and task configuration retain their current database
transaction behavior.

In Celery mode, task configuration is committed before publishing to Redis so
a fast worker cannot read uncommitted configuration. If Redis is unavailable
or publishing fails, the API returns an enqueue error and records the
translation as `failed` with a retryable failure reason. The user can restart
the task after Redis is available. Batch publishing handles each child
independently and marks only children that could not be published as failed.

The simplified direct-publish design does not add a transactional outbox. A
web process that terminates in the small interval after the database commit
and before Redis accepts the message can leave a task in `none`. Such a task is
visible and can be restarted by the user or administrator. Eliminating this
window would require a separate outbox/dispatcher design and is intentionally
outside this version.

Celery may redeliver a message after a worker crash. The task-state guard
prevents a completed task from being translated again. A redelivered message
may reset a task left in `process` only after Celery has cancelled the previous
execution. The Redis visibility timeout must exceed the longest supported
translation so an active long-running task is not redelivered merely because
it exceeded the broker timeout.

Switching queue backends requires stopping the old worker type first. Pending
database jobs are not silently moved to Redis, and Redis messages are not
silently moved into the database queue. Deployment documentation must require
administrators to let pending work finish or explicitly restart those tasks
after switching.

## Deployment

Docker Compose is optional. It provides convenient service definitions but is
not part of the runtime contract.

Database mode runs:

```text
backend container
database worker container: python worker.py
```

Celery mode runs:

```text
backend container
Redis container or external Redis
ordinary Celery worker consuming translation.default
PDF Celery worker consuming translation.pdf
```

Independent Docker users run the same backend image, pass the same environment
file, and override the container command for each worker. No container-role
environment variable is introduced.

The backend and all workers must use the same application database and mount
the same `/app/storage` directory. A named Docker volume is sufficient on one
host. Deployments spanning multiple hosts require a shared filesystem because
the current translation handlers operate on filesystem paths.

## Compatibility

- `database` is the default, preserving existing installations.
- Existing API routes and response structures remain unchanged.
- Existing database worker commands remain valid.
- The shared backend image may include the Celery Python packages, but database
  mode does not import them and does not require a Redis service.
- Batch children remain independent tasks in either mode.
- Original filenames and result ZIP behavior do not change.
- Legacy Office conversion and block-level resume remain out of scope.

## Testing

Tests cover:

- default selection of the database backend;
- explicit Celery backend selection;
- rejection of invalid backend values and missing broker configuration;
- no Celery import or Redis connection in database mode;
- routing ordinary documents and PDFs to separate Celery queues;
- deterministic Celery task identifiers and duplicate-delivery guards;
- broker-redelivery recovery for a task left in `process`;
- Celery publish failure persisted as a failed translation;
- Celery task execution calling `TranslateEngine.run()`;
- deleted, missing, processing, failed, and completed task behavior;
- existing database queue tests remaining unchanged;
- batch and ZIP children using the configured backend;
- Compose and independent Docker command documentation.
