# Usage Guide

## Getting Started

Install DevTask Manager:

```bash
pip install -e .
```

## Common Workflows

### Morning Planning
```bash
devtask add "Review PR" --priority high --tag review
devtask add "Write tests" --priority medium --tag testing
devtask list
```

### During the Day
```bash
devtask update 1 --status in-progress
devtask done 1
```

## Tips
- Use tags to group related tasks
- Set critical priority for blocking issues
- Update status as you work
