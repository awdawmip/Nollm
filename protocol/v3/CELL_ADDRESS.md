# GRF Cell Address

A GRF cell address is a stable integer tuple:

```text
CellAddress(profile_id, chart_id, layer, q, r, phase=None)
```

Rules:

```text
profile_id must exist in the profile registry
chart_id must be non-empty
layer, q, and r are integers
q and r are axial hex coordinates
phase is optional lookup context, not a fact
```

The associated cube coordinate is:

```text
x = q
y = r
z = -q - r
```

and must satisfy:

```text
x + y + z = 0
```

GRF1-A cell addresses are not evidence identities, placement records,
admission records, recall keys, or object-level semantic links.
