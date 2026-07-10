# GRF V2 Adapter Skeleton

This directory declares a replaceable host boundary only. It contains no
legacy memory provider, native store, recall implementation, or automatic
admission path. A future OpenClaw integration maps requests to the versioned
GRF host contract through `integrations/adapters/grf_file_adapter.py`.
