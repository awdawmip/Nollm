# GRF Source Window Prototype

`SourceWindowRecord` names an explicit physical or validation window that a host
chooses to expose to GRF capture.

Supported prototype kinds:

- `session`
- `file`
- `tool_output`
- `task`
- `import_batch`
- `validation_fixture`

Window ids remain protocol ids. File paths are derived through GRF safe object
path encoding and never by writing the id directly into the filename.
