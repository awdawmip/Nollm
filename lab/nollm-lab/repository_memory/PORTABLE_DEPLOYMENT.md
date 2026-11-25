# Independent field deployment

An explicit deployment directory packages the existing native runtime, a settled
field and fixed original source files. It does not install an account skill or
change another repository's ordinary entry. Use Python 3.11 or newer.

```sh
python3 lab/nollm-lab/repository_memory/build_deployment.py \
  --dest /path/to/new-deployment --field /path/to/field \
  --snapshot /path/to/source-snapshot --runtime-commit FULL_NOLLM_COMMIT
```

The field must have finished its writes. Reopen a field with pending local
reorganization to complete recovery before exporting it. Existing deployment
destinations are preserved; select a new destination for a changed version.

The resulting directory can be relocated. From another working directory:

```sh
python3 /path/to/deployment/run.py encounter --cursor-file /tmp/nollm-session.json
python3 /path/to/deployment/run.py show OBSERVED_STATEMENT_ID
python3 /path/to/deployment/run.py source --id OBSERVED_STATEMENT_ID --number 1
```

Use the candidates and IDs actually displayed by `encounter`. The launcher supplies
its own field and snapshot paths. For a separate test copy, put `--field PATH`
before the command. New or revised judgments use the usual `--cite` and stdin
body; their snapshot source windows are checked before writing. An explicit
`--repo PATH` or `--snapshot PATH` selects a different source provider.

The bundled `run.py local-p8 --input request.json` is the explicit Lab evaluation
tool. It computes coverage or pressure without changing the field's Q40 geometry.
The installed runtime also exposes `memory.py aux local-p8 --input request.json`.

## Fixed source snapshot

Place `snapshot.json` beside `files/<original repository path>`. Preserve each
source file's original bytes, including UTF-8 encoding and line endings.

```json
{
  "schema": "nollm_source_snapshot_v1",
  "repository": "owner/repository",
  "commit": "1234567890abcdef1234567890abcdef12345678",
  "files": {
    "notes/policy.md": {
      "blob_sha": "THE_EXISTING_40_CHARACTER_GIT_BLOB_SHA",
      "size": 123
    }
  }
}
```

`files` is an evidence inventory. It does not choose an entry, place judgments or
participate in native recall. `source` opens only the known statement's selected
`COMMIT:path#Lfirst-Llast` reference. It checks the exact file against its existing
Git blob identity when read, then prints the pinned source and original line
numbers. A different commit, missing file, altered bytes or invalid line window
fails explicitly. No Git checkout or network access is needed for a materialized
file. `--rev HEAD` with a snapshot resolves to that snapshot's fixed commit.

A snapshot may inventory more original files than were materialized locally.
The builder records declared and materialized file counts and whether this copy
is complete in `deployment.json`; it does not claim absent files were read.
When publishing inside the source repository, a publisher may preserve the full
frozen source tree by reusing its existing Git tree object. Update the deployment
materialization receipt to the actual published state; retain the fixed source
commit and distinguish publication from the sources used in an individual test.

The direct native CLI accepts the same provider explicitly:

```sh
python3 /path/to/runtime/scripts/memory.py project --field /path/to/field \
  source --id OBSERVED_STATEMENT_ID --snapshot /path/to/source-snapshot
```
