# AL Statement Formation Contract Report

The Access package exposes strict Raw Evidence, Unicode code-point span,
selection, request, decision, formed statement, and actor Protocol contracts.
Assembly extracts one continuous span from one evidence record and produces the
existing `MemoryStatement` payload while retaining separate provenance.

Formation is explicit and composable. It does not write EvidenceStore or Core,
does not choose a geometric location, and does not change `AccessRuntime.capture`.
Python validates types, state, references, bounds, order, overlap, and exact
text inheritance; it does not decide whether a boundary is meaningful.

Python string indices count Unicode code points. They are not UTF-8 byte offsets
and do not identify user-perceived grapheme clusters.
