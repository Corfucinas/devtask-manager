# DevTask Manager

A lightweight CLI task manager for developers. Track your work without leaving the terminal.

## Features

- Create, list, update, delete tasks
- Priority levels (low, medium, high, critical)
- Tag-based organization
- Status filtering (todo, in-progress, done)
- JSON file storage (no database required)
- Clean CLI interface with colors

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Add a task
devtask add "Fix login bug" --priority high --tag backend

# List all tasks
devtask list

# List by status
devtask list --status in-progress

# Update a task
devtask update 1 --status in-progress

# Complete a task
devtask done 1

# Delete a task
devtask delete 1

# Search by tag
devtask list --tag backend
```

## Configuration

Tasks are stored in `~/.devtask/tasks.json` by default. Override with `--storage` flag.

## License

MIT