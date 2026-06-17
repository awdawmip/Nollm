# RETURN_VECTOR Protocol

> Status: V1 placeholder  
> Role: visible route home from drifted content to entry well

---

## 1. Definition

A Return Vector tells the model how it may return to the entry Gravity Well if it chooses.

It is not a command.

---

## 2. Minimal Schema

```yaml
return_vector:
  nearest_projection_layer: 5
  nearest_projection_cell:
    q: 18
    r: -9
  ring_distance: 4
  suggested_anchor_back:
    - anchor_a
    - anchor_c
```

---

## 3. Non-Meanings

A Return Vector is not:

```text
a forced return command
a rejection gate
a trust/status mapper
a parent-child link
```

---

## 4. V1 Status

Return Vector may remain null in the first gravity implementation.

It becomes active in ablation condition:

```text
N3 = Vector RAG + gravity report + return vector
```
