# V2 Legacy Boundary

V2 is the active Nollm architecture. V1, MT1, and pre-V2 prototype material is
retired history unless a later task explicitly authorizes migration work.

## Physical Presence Is Not Active

Historical source files, examples, reports, and protocol drafts may remain in
the repository for auditability. Their presence does not make them active API,
active runtime, active architecture, or an allowed dependency source for V2
Core work.

## OpenClaw Boundary

OpenClaw material is a frozen migration asset. It may inform future L5 Host
Adapter or L6 Terminal work only after an explicit task authorizes that
migration. OpenClaw must not be imported by L0-L3 V2 Core code and must not be
treated as the current Nollm runtime.

## Adapter and Terminal Boundary

HCG is an accepted L5 File Capture Adapter. HAG1-C1R is an accepted but
unpromoted L5 File Admission Adapter candidate. Adapter source may translate
host inputs through L4 contracts; it may not own Core facts.

Terminal or product work belongs to L6 and must pass through L5/L4. No terminal
surface may call Core workflow as a private shortcut.

## Retired Source Boundary

Retired V1 and MT1 material must not be deleted or moved by V2L0. Future
cleanup, migration, or removal requires a separate task with explicit scope.
