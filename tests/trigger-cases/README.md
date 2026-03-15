# Trigger test cases

## Positive
- `交部议 生成接近参考仓库水平的五院制github发布版`
- `请调研一下油价上升对中国房地产市场的影响，交部议。`

## Negative
- `交一下`
- `部门会议纪要`
- `这个问题你直接回答就行`

## Expected behavior
- Positive cases force the five-agent workflow.
- Negative cases do not trigger the workflow phrase by string match alone.
