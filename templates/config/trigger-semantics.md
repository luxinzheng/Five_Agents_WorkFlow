# Trigger semantics

## Fixed trigger phrase

- `交部议`

## Meaning

When the user says `交部议`, force the five-agent workflow:
- 枢密院受理
- 中书省规划
- 尚书省执行
- 门下省验收
- 都察院终审

## Scope

- This is a workflow command, not casual prose.
- It should trigger even if the task might otherwise be answerable directly.
- Do not silently broaden it to fuzzy paraphrases unless the operator explicitly edits the rule.

## Migration rule

- Preserve this phrase when moving the pack to another OpenClaw instance.
- Keep the meaning stable across channels.
