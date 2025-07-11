# import-future-annotations

Tool that checks presence of import `from __future__ import annotations` in python files and adds it if it's missing.

## Installation

Requires Python >=3.8.

```bash
pip install import-future-annotations
```

## Usage

`import-future-annotations` takes filenames as positional arguments.

Additional options:
- `--check-only`: Don't modify files, only check. If script is applicable to any given file, the exit status code will be 1.
- `--allow-empty`: Add import to empty python files aswell.

## As a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`:
```yaml
-   repo: https://github.com/mbroton/import-future-annotations
    rev: v0.1.0
    hooks:
    -   id: import-future-annotations
```


## How does it work?

### Files without docstrings
`file.py` before:
```python
import os
import sys

...
```
Run pre-commit hook or execute command:
```bash
> import-future-annotations file.py
Adding annotations import to file.py
```
`file.py` after:
```diff
+ from __future__ import annotations
import os
import sys
```

### Files with docstrings
`file.py` before:
```python
"""
This is a module docstring.
"""
import os
import sys

...
```
Run pre-commit hook or execute command:
```bash
> import-future-annotations file.py
Adding annotations import to file.py
```
`file.py` after:
```diff
"""
This is a module docstring.
"""
+ from __future__ import annotations
import os
import sys
```

The import is placed **after** the module docstring (if present) or at the beginning of the file (if no docstring).

### Files with syntax errors
Files containing syntax errors are automatically skipped with a warning message:
```bash
> import-future-annotations broken_file.py
Skipping broken_file.py: file contains syntax errors
```

### Notes
- It won't add any blank lines, so I suggest to use/place it before [`reorder_python_imports`](https://github.com/asottile/reorder_python_imports) hook or other hooks that may complain about it.
