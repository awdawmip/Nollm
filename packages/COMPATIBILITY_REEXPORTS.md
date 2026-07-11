# Compatibility Re-exports

M0 introduces no compatibility re-export. Existing production modules remain
at their original paths while the new package contracts are established.

Any future compatibility entry must be import-only, be listed here, and include
its M1 or later removal gate. It may not preserve a relation index or semantic
placement implementation.
