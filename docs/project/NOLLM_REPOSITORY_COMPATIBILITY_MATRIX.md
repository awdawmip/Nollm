# Repository Compatibility Matrix

This is the M0 compatibility policy, not a release announcement.

| Module | Version policy | Depends on | Compatibility rule |
| --- | --- | --- | --- |
| Core | Independent SemVer | None | Breaking Handle/port changes require a major release |
| Snapshot | Independent SemVer | Core public port | Declares Core range and snapshot format version |
| Trace | Independent SemVer | Core trace contract | Stable events follow SemVer; internal/experimental do not |
| Access | Independent SemVer | Core, optional Snapshot | Locks Core command and Handle ranges |
| History | Independent SemVer | Access, optional Snapshot | Never infers history from snapshot identity |
| Audit | Independent SemVer | Access contracts, optional Trace | Core remains independent of Audit |
| OpenClaw | Independent SemVer | Access | Never imports Core private implementation |
| Lab | No runtime compatibility promise | Any module | Production modules never depend on Lab |
| Distributions | Composition release | Selected modules | Lock a tested set of package ranges |

No package is independently released or remotely split during M0. The concrete
version ranges are assigned only after the future split entry conditions pass.
