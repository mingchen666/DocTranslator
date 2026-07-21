# Translation Critical Repairs Design

Date: 2026-07-21

## Goal

Fix the highest-impact translation correctness, authorization, validation, and
status-reporting defects without adding Redis, a persistent worker queue, old
Office format conversion, or block-level resume support.

## Scope

This repair includes:

- Validate translation start parameters before mutating the task.
- Treat a failed `TranslateEngine.execute()` call as a failed start.
- Restrict Prompt and Comparison lookup to active resources owned by the task
  owner or shared by their owner.
- Pass the task's resolved prompt into the PDF translation configuration.
- Update the PDF result using the real `target_filepath` database column.
- Store the physical output file size when a task completes.
- Do not report a fully successful task when one or more text blocks failed.
- Preserve a readable, truncated failure reason for every failed task path.
- Calculate Doc2X storage usage from the server-side source file, not a client
  supplied size.

The repair excludes:

- Redis, Celery, RQ, or a database-backed worker queue.
- Automatic recovery of work lost when a Gunicorn worker or host exits.
- Block-level translation checkpoints and resume.
- LibreOffice conversion for `.doc`, `.xls`, or `.ppt`.

## API Validation

The start endpoint will parse and validate all mode-dependent values before
updating the `Translate` record:

- Common required values must be present and non-empty.
- `threads` must be an integer in the range accepted by the translation layer.
- Optional `prompt_id` and `comparison_id` must be non-negative integers.
- OpenAI mode requires usable API URL and API key values for non-VIP users;
  VIP users may use configured system credentials.
- Baidu mode requires `app_id`, `app_key`, and `to_lang`.
- `backup_model` remains optional.

Validation errors return HTTP 400 and do not partially update the task. A
missing or disabled customer returns the existing authorization-style error.

After configuration is committed, the endpoint starts the engine. If the
engine reports that initialization failed, the task becomes `failed`, its
failure reason is populated, and the endpoint returns HTTP 500 instead of a
success response.

## Resource Authorization

Prompt and Comparison resolution uses `task.customer_id` rather than request
context, because resolution happens in the background execution context. A
resource is usable only when it is not deleted and either:

- `customer_id == task.customer_id`, or
- `share_flag == 'Y'`.

An unauthorized or missing selected resource must not silently expose its
content. Task preparation fails with a user-readable reason. A missing optional
selection continues to use the task's inline prompt only when no Prompt ID was
selected.

## Translation Outcomes

The existing task status enum remains `none`, `process`, `done`, and `failed`.
No `partial` state is added in this repair.

The common text translation loop tracks non-fatal block failures. If any block
falls back to its original text, the translation loop returns failure after all
remaining blocks finish. The handler may still write the inspectable output,
but the task ends as `failed` with a reason that states how many blocks were not
translated. This prevents a mixed original/translated document from being
reported as fully successful.

All failed execution paths preserve an existing specific failure reason. A
generic reason is only supplied when no lower layer recorded one. Failure
reasons are limited to 500 characters.

## PDF And File Statistics

The resolved task prompt is mapped to BabelDOC's `custom_system_prompt`. PDF
completion updates `target_filepath`. Database update failures are treated as
failures rather than successful log-only events.

The common completion function derives `target_filesize` from the final output
path. It accepts the final PDF path when BabelDOC renames its output. Missing
output files prevent a task from being marked complete.

Doc2X reads `os.path.getsize(translate.origin_filepath)` after confirming the
source exists. The same value is used for task size and customer storage. The
client `size` field is ignored.

## Retry And Resume Boundary

This repair may keep existing explicit retry entry points working, but it does
not claim resumable translation. A retry starts the document again. Future
block-level resume will require persisted source hashes, translated text,
configuration hashes, cleanup rules, and separate PDF behavior.

## Tests

Focused tests will cover:

- Invalid and mode-dependent start parameters return 400.
- Engine initialization failure returns an error and persists failed state.
- Private Prompt and Comparison records cannot be used by another customer;
  shared active records can be used.
- PDF configuration receives the resolved prompt and writes
  `target_filepath`.
- Completion stores the real file size and refuses a missing output.
- A non-fatal block failure produces a failed task result and reason.
- Doc2X ignores the request size and uses the source file size.

The existing backend repair test suite must continue to pass.
