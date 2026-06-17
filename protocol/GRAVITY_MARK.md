# GRAVITY_MARK Protocol

> Status: V1 protocol stub  
> Role: content-side geometry and anchor record

---

## 1. Definition

A Gravity Mark is attached to a recalled content item or persistent shard/card.

It records where the item sits in geometry and what anchor vector it carries.

---

## 2. Minimal Schema

```yaml
gravity_mark:
  content_id: shard_001
  chart_id: chart_alpha
  layer: 5
  q: 31
  r: -18
  geometry_profile: default_dream
  anchor_vector:
    anchor_a: 0.62
    anchor_d: 0.88
  provenance:
    mark_source: geometry_projection | imported | experiment
```

---

## 3. Recall Digest Items

A recall digest item may carry a copied or derived Gravity Mark for display and drift reporting.

This does not make the digest item a new persistent memory object unless an explicit write operation creates it.

---

## 4. Non-Meanings

A Gravity Mark is not:

```text
a parent assignment
an ownership marker
a folder/tag
a trust/status mapper
a write permission
```
