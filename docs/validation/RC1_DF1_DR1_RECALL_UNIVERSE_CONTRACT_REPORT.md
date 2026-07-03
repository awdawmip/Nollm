# RC1 DF1 to DR1 RecallUniverse Contract Report

- root_baseline_head: `1def9e0d4d2b0deb2ab2ad9db74f6d01d4a3dbf7`
- rc1_c1_input_baseline_head: `30c0c06782d47d324406800f68e21ea7aa58deb3`
- validation_head: `fbe44575c7e1d4d87e3b7c221655f74e2a57de64`
- command: `python validation/rc1/run_df1_dr1_recall_universe_contract.py --output docs/validation/RC1_DF1_DR1_RECALL_UNIVERSE_CONTRACT_REPORT.md`
- production_fix_path: `reference/python/nollm/dream_geometry/assembly/builder.py`

## Evidence

- rc1_01_single_admission_df1_to_dr1: `pass`
- rc1_02_snapshot_universe_view_split: `pass`
- rc1_03_multi_admission_determinism: `pass`
- rc1_04_public_reconstruction_path: `pass`
- rc1_05_fail_closed_binding: `pass`

## Contract

- `FiniteFieldSnapshot.coarse_covers` remains the DG2 local view with `CellRef` support cells.
- `RecallUniverse.covers` is the DR1 executable view with `HexCell` support cells bound from all same-call support traces.
- Every declared support trace id must be present and every support trace cell must match the cover cell identity.
- RC1-C1 does not complete DX2; DX2 remains paused.
