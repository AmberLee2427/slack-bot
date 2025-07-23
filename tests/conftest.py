import pytest
import tempfile
import os
import json
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_notebook():
    """Create a sample notebook for testing"""
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": "# Sample Notebook\n\nThis is a sample notebook for testing."
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": "import numpy as np\n\nx = np.array([1, 2, 3])\nprint(x)"
            },
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": "Here's a code example:\n\n```python\ndef hello():\n    return 'world'\n```"
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }


@pytest.fixture
def sample_notebook_file(sample_notebook, temp_dir):
    """Create a sample notebook file"""
    notebook_path = temp_dir / "sample.ipynb"
    with open(notebook_path, 'w') as f:
        json.dump(sample_notebook, f)
    return notebook_path


@pytest.fixture
def sample_text_file(temp_dir):
    """Create a sample text file"""
    text_content = """# sample_notebook.ipynb

```markdown
# Sample Notebook

This is a sample notebook for testing.
```

```python
import numpy as np

x = np.array([1, 2, 3])
print(x)
```

```markdown
Here's a code example:

```python
def hello():
    return 'world'
```
```"""
    
    text_path = temp_dir / "sample.txt"
    with open(text_path, 'w') as f:
        f.write(text_content)
    return text_path


def create_notebook_file(content, path):
    """Helper function to create a notebook file"""
    with open(path, 'w') as f:
        json.dump(content, f)


def cleanup_files(*paths):
    """Helper function to clean up test files"""
    for path in paths:
        if os.path.exists(path):
            os.unlink(path) 