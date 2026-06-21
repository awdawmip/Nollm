# Read Write Policy

Nollm separates reading, inference, and durable writing.

## Read

Cortex may read Core records by anchor field, address, or ledger trail. Read results should preserve source addresses.

The P2 reference read path is:

`orient -> surface -> focus -> recall_digest`

`orient` identifies active anchor fields. `surface` reads current-scale cards influenced by those fields. `focus` selects sufficient-scale cards. Full card bodies are excluded by default.

Conceptually, read is scale scan, not tree descent. Cortex re-evaluates at each layer, shifts laterally if another anchor field becomes stronger, and stops when sufficient scale is reached.

## Infer

Cortex may reason over recalled material, but inference is not memory until written as a card and ledgered.

## Write

Cortex may propose a write when:

- The memory is durable.
- The source or decision is clear.
- The proposed card has anchors.
- The change can be ledgered.

Core accepts only structured, auditable writes. It does not perform autonomous memory improvement.

Cortex read actions must not create anchors, confirm cards, or rewrite memory.

Cortex must not use anchors as folders, search a tree, or look for a leaf node.
# MT1 Read / Write Boundary

MT1 archive and legacy import never write `MEMORY.md`, `DREAMS.md`, or `memory/*.md`. Archive is provenance, not active recall fallback. Imported shards are conservative native records with source refs and loose operational state.
