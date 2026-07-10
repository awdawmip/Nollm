# GRF Contract Evolution

The contract registry exposes `grf_host_v2` as current and `grf_host_v1` as
supported-deprecated. Envelope migration deep-copies the original request,
changes only `contract_version`, and records migration metadata. Payload and
typed identity values remain unchanged.

Unknown versions and migration targets are rejected. Deprecated support does
not activate retired terminal or legacy provider code.
