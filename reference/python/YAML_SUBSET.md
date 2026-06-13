# YAML Subset

The P1 reference CLI uses a deliberately small YAML-like subset so Nollm can remain dependency-free.

## Supported Constructs

- Top-level mappings.
- Scalar strings, numbers, `null`, and empty lists.
- Lists of scalars.
- Lists of shallow dictionaries.
- Nested dictionaries and lists already used by the reference parser.

## Non-Goals

- YAML anchors or aliases in YAML syntax.
- Multiline block scalars.
- Complex quoting rules.
- Treating comments as data.
- Arbitrary YAML tags.
- Full YAML specification compatibility.

This subset is intended for Nollm source files generated or maintained in the project style. It is not a general-purpose YAML parser.

