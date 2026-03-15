# Trigger semantics

## Fixed workflow command
`交部议`

## Meaning
Force the five-agent workflow, even if the request might otherwise be answered directly.

## Stable behavior
- treat it as a deterministic command
- keep the meaning stable across migrated installs
- document and test it explicitly
- keep internal five-agent handoffs JSON-formatted for consistency
