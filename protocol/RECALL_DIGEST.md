# Recall Digest

A recall digest is a temporary reading packet assembled from Nollm Core records.

## Purpose

Recall digests help an LLM enter a task with relevant memory while keeping source records traceable.

## Format

A digest should include:

- Query or task orientation.
- Anchors used.
- Cards read.
- Key recalled points.
- Open questions.
- Source addresses.

## Status

A recall digest is not canonical memory by itself. If it contains new durable knowledge, Cortex should propose a card and Core should ledger it.

