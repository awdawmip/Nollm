# NOLLM GRF5 Product Integration Architecture

```text
GRFProductHost session
  -> replaceable adapter
  -> grf_host_v1 or grf_host_v2
  -> GRFHostService
  -> GRFFacade
  -> evidence, placement, admission, field, recall, replay
```

ProductHost owns Host request sequencing and restartable session state. It
does not import `GRFFacade`, GRF storage, geometry, placement, admission, or
recall implementations. Durable facts remain owned by Core behind the Host
Contract. Adapter replacement and contract migration do not change Core facts.
