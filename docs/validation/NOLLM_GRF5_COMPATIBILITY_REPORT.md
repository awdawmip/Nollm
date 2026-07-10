# NOLLM GRF5 Compatibility Report

`grf_host_v1` remains executable and is classified
`supported_deprecated`; `grf_host_v2` is current. Tests run full product
capture, place, admit, and recall flows under both versions and obtain
equivalent Core result mappings.

Migration preserves the original payload, evidence identity, placement
identity, admission identity, and Host request ID. Unknown versions are
rejected. Existing File and declared adapter families continue to pass their
GRF3R/GRF4R conformance tests.
