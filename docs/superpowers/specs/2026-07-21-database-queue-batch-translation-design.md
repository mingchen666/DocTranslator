# Database Queue And Batch Translation Design

Date: 2026-07-21

## Goal

Replace request-owned translation threads with a durable database queue, bound
document concurrency, and add real multi-file and ZIP batch translation. Redis
is not required. Existing single-file APIs remain compatible.

## Delivery Phases

### Phase 1: Durable Single-File Execution

- Enqueue translation work in the database instead of creating a `Thread` in
  the HTTP request.
- Run translation in a dedicated worker process.
- Recover abandoned jobs after a worker or container restart.
- Limit ordinary document concurrency to two and PDF concurrency to one.
- Preserve existing per-document text-block threading, capped at five.

### Phase 2: Batch And ZIP Translation

- Group independently uploaded files into a batch.
- Accept ZIP as a batch input container.
- Create one `Translate` record and one queue job per supported document.
- Aggregate batch progress without coupling child task outcomes.
- Produce a result ZIP with user-facing filenames and safe duplicate handling.

Phase 2 depends on Phase 1. ZIP extraction must not directly create background
threads.

## Queue Storage

The existing `jobs` table is used as the durable queue:

- `queue`: `default` or `pdf`.
- `payload`: JSON containing `translate_id` and optional `batch_id`.
- `attempts`: number of worker claims.
- `reserved_at`: Unix timestamp used as the active lease heartbeat.
- `available_at`: earliest time at which the job can be claimed.
- `created_at`: enqueue timestamp.

Completed jobs are deleted. Jobs that exhaust infrastructure retry attempts are
copied to `failed_jobs` before deletion. Translation-level failures already
handled by document processors are not repeatedly retried as infrastructure
failures.

Queue insertion and the corresponding `Translate` state update occur in one
database transaction. A queued translation remains in the existing `none`
state for API compatibility until a worker claims it; the API response includes
an explicit `queued` flag.

## Worker And Leasing

The worker runs as a separate process from Gunicorn and uses the Flask app
factory. It claims jobs in a short transaction:

1. Select the oldest available, unreserved job in the requested queue.
2. Lock it using `FOR UPDATE SKIP LOCKED` on MySQL.
3. Set `reserved_at` and increment `attempts`.
4. Commit before executing document translation.

SQLite development uses one worker and a normal transactional claim because it
does not provide the same row-lock semantics.

While a document runs, a heartbeat refreshes `reserved_at`. A job with an old
lease is claimable again. The default lease timeout is ten minutes with a
30-second heartbeat; an active heartbeat allows translations to run longer than
the timeout.

The worker calls a synchronous translation-engine method. The HTTP-facing
method only enqueues; it does not spawn a thread. Existing MCP and admin restart
paths also enqueue.

## Concurrency

Concurrency is bounded at two levels:

- Document level: two ordinary documents and one PDF may execute at once.
- Text-block level: each ordinary document may use at most five API threads.

The defaults are configurable through environment variables. A ZIP with 20
documents creates 20 queued jobs but only the configured number execute at the
same time. PDF jobs use their own queue because layout and OCR models have a
larger memory footprint.

## Batch Data

Add a `translate_batch` table:

- `id`: UUID primary key.
- `customer_id`: owner.
- `source_type`: `files` or `zip`.
- `origin_filename`: ZIP display name when applicable.
- `status`: `pending`, `process`, `done`, `partial`, or `failed`.
- `total_count`: accepted document count.
- timestamps for creation, update, and completion.

Add nullable fields to `translate`:

- `batch_id`: owning batch UUID.
- `batch_relative_path`: sanitized relative path used in the result ZIP.

Batch counts are derived from child `Translate` records. A batch is `partial`
when it contains both successful and failed child tasks. A child failure never
cancels other children.

## APIs

Existing single-file upload and translation endpoints remain available.

New or extended APIs:

- `POST /api/translate/batches`: create a batch from existing uploaded
  `translate_id` values and enqueue every child.
- `POST /api/translate/batches/zip`: upload, validate, extract, create the batch,
  and enqueue accepted children using one translation configuration.
- `GET /api/translate/batches/<batch_id>`: return aggregate counts and child
  summaries.
- `GET /api/translate/batches/<batch_id>/download`: download successful results
  as a ZIP once no child is pending or processing.

All batch queries and downloads require `customer_id` ownership.

## ZIP Safety

ZIP is an input container, not a translatable document type. Extraction rules:

- Maximum 20 supported documents per batch.
- Reject encrypted members, nested archives, absolute paths, `..` traversal,
  drive-qualified paths, and symbolic links.
- Ignore directories and common metadata such as `__MACOSX`.
- Reject an archive with no supported documents.
- Enforce per-file size, total uncompressed size, customer storage, and a
  compression-ratio limit before extraction.
- Extract into a batch-specific source directory using sanitized relative
  paths.
- Accept only currently supported modern formats. Legacy `.doc`, `.xls`, and
  `.ppt` conversion remains outside this feature.

The ZIP upload itself is deleted after successful extraction. Customer storage
is charged once for accepted extracted source files.

## Filenames And Results

Each child keeps its original user-facing filename. PDF BabelDOC suffixes are
already treated as intermediate names and are not exposed.

Result ZIP entries use `batch_relative_path`. Duplicate flattened names receive
` (2)`, ` (3)`, and so on before the extension. Internal UUID storage names are
never exposed. Only successful child outputs are included; the batch status API
reports failed children and their reasons.

Result archives are created on disk or with a spooled temporary file, not held
entirely in memory. Temporary archives are removed after the response or a
bounded retention period.

## Deployment

The same backend image starts a dedicated worker service in Docker Compose.
Backend and worker mount the same database and storage volumes. Local
development documents the separate worker command.

Worker shutdown stops claiming new jobs, waits for a bounded grace period, and
then leaves the lease to expire if active work cannot finish.

## Testing

Tests cover:

- Transactional enqueue and single execution under competing worker claims.
- Lease heartbeat, stale lease recovery, and infrastructure retry exhaustion.
- Global default/PDF concurrency bounds.
- Existing single-file API compatibility.
- Batch ownership and aggregate status transitions.
- ZIP traversal, symlink, encryption, nested archive, count, size, and
  compression-ratio rejection.
- Partial batch completion and successful-result download.
- Filename preservation, relative paths, and duplicate-name handling.
- Worker/container restart simulation with queued and leased jobs.

Real translation APIs are mocked in queue tests. Existing document processor
tests continue to run unchanged.
