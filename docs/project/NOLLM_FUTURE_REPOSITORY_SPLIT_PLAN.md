# Future Repository Split Plan

M0 does not create remote repositories, rewrite history, or push a split. The
future targets are `nollm-core`, `nollm-snapshot`, `nollm-trace`, `nollm-access`,
`nollm-openclaw`, `nollm-lab`, and `nollm-distributions`; `nollm-history` and
`nollm-audit` are optional targets.

## Entry Conditions

- Core Handle API, Snapshot Port, and TraceSink API are stable.
- Access-to-Core command mapping is stable.
- The module graph is acyclic and each package has an independent test gate.
- At least one separately authorized OpenClaw end-to-end run passes.
- The compatibility matrix has exact supported package ranges.

## Windows History-Preserving Procedure

Run only under a separately approved split task. From a disposable Windows
clone, either use `git filter-repo`:

```powershell
git clone --no-local C:\Users\chaos\nollm C:\Users\chaos\split-nollm-core
Set-Location C:\Users\chaos\split-nollm-core
git filter-repo --path packages/nollm-core --path-rename packages/nollm-core/:
git fsck --no-reflogs --connectivity-only
```

or create a component branch without modifying the source branch:

```powershell
git subtree split --prefix packages/nollm-core -b split/nollm-core
git bundle create C:\Users\chaos\nollm-core-history.bundle split/nollm-core
git bundle verify C:\Users\chaos\nollm-core-history.bundle
```

Before any remote action, compare file inventory, tags, public imports, tests,
and commit provenance against the monorepo. Remote creation and push require
separate authorization.

## Versioning

Each repository uses independent SemVer. Distributions lock compatible package
ranges. Breaking Core APIs require an Access migration release before dependent
distribution promotion. Snapshot formats carry an explicit format version.
Stable Trace events follow SemVer; internal and experimental events may change
without compatibility guarantees.
