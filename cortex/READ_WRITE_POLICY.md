# Read Write Policy

Nollm separates reading, inference, and durable writing.

## Read

Cortex may read Core records by anchor, address, or ledger trail. Read results should preserve source addresses.

## Infer

Cortex may reason over recalled material, but inference is not memory until written as a card and ledgered.

## Write

Cortex may propose a write when:

- The memory is durable.
- The source or decision is clear.
- The proposed card has anchors.
- The change can be ledgered.

Core accepts only structured, auditable writes. It does not perform autonomous memory improvement.

