# Architecture

## Overview

DevTask Manager follows a simple layered architecture:

```
CLI Layer (src/cli.py)
    |
    v
Business Logic (src/models.py, src/sorting.py, src/validators.py)
    |
    v
Storage Layer (src/storage.py)
    |
    v
File System (~/.devtask/tasks.json)
```

## Components

### CLI (src/cli.py)
Parses arguments using argparse, routes to command handlers.

### Models (src/models.py)
Task: core data model. Priority enum: low/medium/high/critical. Status enum: todo/in-progress/done.

### Storage (src/storage.py)
TaskStore: JSON file CRUD. Auto-increments task IDs.

### Sorting (src/sorting.py)
sort_by_priority (critical first), sort_by_created (newest first).

### Validation (src/validators.py)
Title validation (non-empty, max 200 chars). Tag validation (alphanumeric + hyphens).

### Formatting (src/formatter.py)
ANSI color output. List and detail views.

## Design Decisions

- **JSON over SQLite**: Simpler, no dependencies. Tradeoff: no concurrent access safety.
- **Enums over strings**: Type safety, prevents invalid states.
- **File-based storage**: Zero config. Tradeoff: not suitable for teams.
