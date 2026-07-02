# BA1 Batch Admission Scope

```text
Explicit candidate IDs + explicit decisions + explicit DA1 requests
                         |
                         v
              BA1 all-member preflight
                         |
                         v
          serial independent DA1 admission calls
                         |
                         v
      independent AdmissionRecords + narrow batch receipt
```

BA1 does not choose; it coordinates.

BA1 does not place; DA1 verifies placement.

BA1 does not merge; members remain separate.

BA1 does not assemble; DF1 remains later.

BA1 is not a queue, folder, parent node, global Field, recall surface, runtime
workflow, or persistent batch store. It only coordinates host-selected
`DeferredAdmissionCandidate` values into complete, independent DA1
`AdmissionRequest` values after all-member zero-write preflight.
