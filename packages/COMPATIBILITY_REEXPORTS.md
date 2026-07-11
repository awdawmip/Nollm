# Compatibility Re-exports

M0 introduces no compatibility re-export. Existing production modules remain
at their original paths while the new package contracts are established.

M1 also introduces no compatibility re-export. The old
`reference/python/nollm/grf` implementation is a Legacy compatibility baseline,
not an import alias and not an active Bare/Minimal dependency. New package code
does not import it.

Any future compatibility entry must be import-only, be listed here, and include
its M1 or later removal gate. It may not preserve a relation index or semantic
placement implementation.
