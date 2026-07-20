# Core Translation P0 Repair Design

## Objective

Remove the two critical cross-task and cross-environment risks in the core
translation pipeline without redesigning the task execution architecture.

## Scope

This repair covers only:

- selecting the correct MySQL database for development and production;
- preventing concurrent translation jobs from sharing OpenAI credentials or
  endpoints;
- removing logs that expose translation credentials and private prompts;
- documenting all currently known P1/P2 translation issues in
  `bug相关文档.md` for later work.

Task queues, durable recovery, legacy Office formats, PDF behavior, request
validation, and storage accounting are explicitly deferred.

## Database Selection

The existing translation status helper remains in place to minimize changes to
all format handlers. Its database URL selection becomes explicit:

- `FLASK_ENV=development` uses `DEV_DATABASE_URL`;
- `FLASK_ENV=production` uses `PROD_DATABASE_URL`;
- an unsupported or missing environment/database URL fails loudly instead of
  falling back to another environment.

Both local development and production use MySQL. SQLite placeholder adaptation
is retained only where useful for isolated tests; production behavior remains
MySQL-specific.

The helper must never choose `PROD_DATABASE_URL` while Flask is configured for
development. Tests will set distinct sentinel development and production URLs
and assert the selected value.

## OpenAI Client Isolation

The core pipeline will stop assigning module-level `openai.api_key`,
`openai.base_url`, or `openai.api_base` values.

At the start of each OpenAI-backed translation job, the job configuration will
receive one `OpenAI` client constructed from that job's API key and normalized
base URL. All block-level worker threads for that job may share only that client.
Different jobs always have different client instances, so concurrent jobs
cannot overwrite each other's configuration.

The Baidu path remains unchanged and does not create an OpenAI client. The
existing model retry behavior will call the task client rather than the module
proxy.

## Logging

The pipeline will remove prints of the complete translation configuration and
the complete final prompt. Normal logs may include task ID, model name, attempt
number, status, and progress, but never API keys, endpoint credentials, document
content, prompt text, or terminology content.

## Error Handling

Missing API URL or API key for an OpenAI job will fail task initialization with
a clear error. It will not use a previously configured global client.

Database configuration errors will identify the missing variable without
including connection passwords in logs.

## Tests

Focused tests will verify:

- development selects `DEV_DATABASE_URL` even when a production URL exists;
- production selects `PROD_DATABASE_URL`;
- missing URLs fail without cross-environment fallback;
- two simulated jobs construct distinct clients with their own keys and URLs;
- block translation calls the client stored on its own task configuration;
- credential and prompt values are not emitted by the modified logging paths;
- the existing backend regression suite still passes.

No real LLM request or production database connection is part of the tests.
