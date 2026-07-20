# Backend Security and Migration Repair Design

## Objective

Repair the urgent backend authorization, file isolation, secret handling, and
database startup problems while preserving all existing production MySQL data.
The same migration code must support Docker deployments and non-Docker local
development.

## Constraints

- Production data must be migrated in place. No table resets or data deletion.
- Existing JWTs may be invalidated; users and administrators will log in again.
- Existing plaintext administrator passwords must remain usable during a
  one-time transition to password hashes.
- Local development uses `python run.py` and may use SQLite or MySQL.
- Existing user changes in `backend/.env` and
  `backend/app/script/init_db.py` must be preserved.

## Selected Approach

Use a compatibility Alembic baseline followed by normal incremental revisions.
Retain revision ID `4f90bb3344d2` as the recognized baseline so databases that
were previously stamped with that local revision remain valid. Replace its
unsafe generated ALTER-only behavior with a complete empty-database schema.

For an existing database with application tables but no usable Alembic version,
the startup migrator will verify a required set of legacy tables and then stamp
the compatibility baseline without executing baseline DDL. It will then apply
later incremental revisions. Unknown or structurally incomplete databases stop
startup with an actionable error.

## Application Startup

`create_app()` will configure Flask and extensions only. It will not initialize,
migrate, or seed a database.

`migrate_startup.py` will expose a reusable migration function and a command-line
entry point. Its flow is:

1. Inspect the configured database.
2. Apply the baseline normally when the database is empty.
3. Validate and stamp the baseline when legacy application tables exist without
   a recognized revision, including an empty `alembic_version` table created by
   the old SQL dump.
4. Reject unknown Alembic revisions or incomplete legacy schemas.
5. Upgrade to the current head.
6. Run idempotent seed operations after successful schema migration.

Docker will use an entrypoint that runs this process synchronously before
starting MCP and Gunicorn. A migration or seed failure prevents both services
from starting.

When `run.py` is executed directly, it will run the same migration function
before starting Flask. Importing `run:app` from Gunicorn will not trigger a
second migration. Developers may also run `python migrate_startup.py` alone.

## Authentication And Authorization

User login tokens will contain `role=user`; administrator login tokens will
contain `role=admin`. A shared `admin_required` decorator will first validate the
JWT and then require the administrator role. Tokens without a role are rejected,
which intentionally invalidates existing sessions.

Every `/api/admin/*` operation will require `admin_required`, including system
settings, storage operations, downloads, batch deletion, statistics, and task
restart. Ordinary authenticated resources continue to use `jwt_required`.

Administrator passwords will use Werkzeug password hashes. Login will support a
legacy plaintext value only when the stored value is not a recognized password
hash and exactly matches the submitted password. A successful legacy login will
immediately replace the stored value with a hash. Administrator and customer
password columns will be expanded to 255 characters by an incremental migration.

## Resource Ownership

User translation download, deletion, and start operations will query records by
both record identifier and the JWT customer identity. A user cannot read,
modify, start, or delete another user's translation record. Administrative
access remains available only through role-protected admin resources.

Storage accounting changes will be committed in the same transaction as record
changes and clamped against negative values where legacy data is inconsistent.

## File And URL Safety

Upload helpers will separate the display filename from the stored filename.
Input filenames containing absolute paths, path separators, NUL bytes, `.` or
`..` path components will be rejected. Stored names will include a UUID-derived
component to avoid same-day overwrite collisions while retaining a safe suffix.

Translation output paths will be derived from trusted stored names rather than
request-provided paths.

MCP URL input will allow only HTTP and HTTPS. DNS results will be checked before
each request and redirect so loopback, private, link-local, multicast, reserved,
and unspecified addresses are rejected. Downloads will stream with a configured
maximum size instead of reading an unbounded response into memory.

## Migration And Seed Data

The tracked Alembic directory will be explicitly unignored. The compatibility
baseline will create all tables required by current models on an empty database.
A subsequent revision will make only proven, data-preserving changes such as
password column expansion.

The old `init.sql` dump will no longer execute during startup. It will not be a
source of default users, example translation records, filesystem paths, or API
keys. Required settings and prompts will be inserted by idempotent seed code.
No default administrator password will be silently created in production.

`backend/.env` will remain on disk but stop being tracked by Git. Existing
credentials that have entered the repository or working tree must be rotated;
code changes cannot revoke external credentials.

## Error Handling

- Migration errors are fatal and include the database state and expected action.
- SQL errors are never treated as successful initialization.
- Authorization failures return 401 for missing/invalid authentication and 403
  for an authenticated token with the wrong role or resource owner.
- File validation errors return 400 without exposing server filesystem paths.
- External download failures return a bounded error without returning secrets.

## Tests

Focused tests will cover:

- user and administrator token claims;
- rejection of old role-less tokens;
- ordinary users being denied all sampled admin endpoints;
- public and cross-user translation download/delete/start denial;
- legacy administrator password upgrade;
- filename traversal, collision handling, and MCP private-address rejection;
- empty database baseline creation;
- legacy database baseline stamping and incremental upgrade;
- rejection of incomplete or unknown database states;
- direct local startup calling migration exactly once.

Static Python parsing and the project test suite will run after implementation.
Docker configuration will be validated without connecting to the production
database.

## Rollout

Before production deployment, create a database backup and rotate every exposed
API, email, JWT, and database credential. Deploy the migration-enabled image once
with application traffic stopped, verify the Alembic head and row counts, then
start normal traffic. All users and administrators must log in again.
