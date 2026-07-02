# RC1 DF1 to DR1 RecallUniverse Contract Report

- baseline_head: `1def9e0d4d2b0deb2ab2ad9db74f6d01d4a3dbf7`
- validation_head: `561e8b9ce32dba0d15e4d1a3f3ff81ca6950f9a3`
- command: `python validation/rc1/run_df1_dr1_recall_universe_contract.py --output docs/validation/RC1_DF1_DR1_RECALL_UNIVERSE_CONTRACT_REPORT.md`
- production_fix_path: `reference/python/nollm/dream_geometry/assembly/builder.py`

## Evidence

- rc1_01_single_admission_df1_to_dr1: `pass`
- rc1_02_snapshot_universe_view_split: `pass`
- rc1_03_multi_admission_determinism: `pass`
- rc1_04_public_reconstruction_path: `pass`

## Contract

- `FiniteFieldSnapshot.coarse_covers` remains the DG2 local view with `CellRef` support cells.
- `RecallUniverse.covers` is the DR1 executable view with `HexCell` support cells bound from same-call replay traces.
- RC1 does not complete DX2; DX2 must restart from the RC1 delivery head after independent acceptance.
