import pytest
import tempfile
import os
from pathlib import Path
from nb4llm.converter import convert_ipynb_to_txt, convert_txt_to_ipynb, get_fence


class TestFenceDetection:
    def test_basic_fence(self):
        assert get_fence("normal text") == "```"
    
    def test_fence_with_backticks(self):
        assert get_fence("text with ``` code block") == "````"
    
    def test_fence_with_many_backticks(self):
        assert get_fence("text with ````` code block") == "``````"
    
    def test_minimum_fence_length(self):
        assert get_fence("", min_length=5) == "`````"


class TestIPYNBtoTXT:
    def test_basic_notebook(self):
        # Create a simple test notebook
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": "# Test Notebook\n\nThis is a test."
                },
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "metadata": {},
                    "outputs": [],
                    "source": "print('Hello, World!')"
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            import json
            json.dump(notebook_content, f)
            ipynb_path = f.name
        
        try:
            result = convert_ipynb_to_txt(ipynb_path, "dummy.txt")
            
            # Check that the result contains expected content
            assert "# test_notebook.ipynb" in result
            assert "```markdown" in result
            assert "# Test Notebook" in result
            assert "```python" in result
            assert "print('Hello, World!')" in result
            
        finally:
            os.unlink(ipynb_path)
    
    def test_notebook_with_different_kernel(self):
        # Test notebook with R kernel
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": "# R Notebook\n\nThis is an R notebook."
                },
                {
                    "cell_type": "code",
                    "execution_count": 1,
                    "metadata": {},
                    "outputs": [],
                    "source": "x <- c(1, 2, 3)\nprint(x)"
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "R",
                    "language": "r",
                    "name": "ir"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            import json
            json.dump(notebook_content, f)
            ipynb_path = f.name
        
        try:
            result = convert_ipynb_to_txt(ipynb_path, "dummy.txt")
            
            # Check that R language is used in the fence
            assert "```r" in result
            assert "x <- c(1, 2, 3)" in result
            assert "print(x)" in result
            
        finally:
            os.unlink(ipynb_path)
    
    def test_notebook_with_fenced_blocks(self):
        # Test notebook with markdown cells containing code blocks
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": "Here's some code:\n\n```python\nx = 1\n```"
                }
            ],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            import json
            json.dump(notebook_content, f)
            ipynb_path = f.name
        
        try:
            result = convert_ipynb_to_txt(ipynb_path, "dummy.txt")
            
            # Should use longer fence for the outer block
            assert "````markdown" in result
            assert "```python" in result  # Inner code block
            assert "x = 1" in result
            
        finally:
            os.unlink(ipynb_path)


class TestTXTtoIPYNB:
    def test_basic_text_conversion(self):
        txt_content = """# test_notebook.ipynb

```markdown
# Test Notebook

This is a test.
```

```python
print('Hello, World!')
```"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(txt_content)
            txt_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.ipynb', delete=False) as f:
            ipynb_path = f.name
        
        try:
            convert_txt_to_ipynb(txt_path, ipynb_path)
            
            # Read back the notebook and verify
            import nbformat
            nb = nbformat.read(ipynb_path, as_version=4)
            
            assert len(nb.cells) == 2
            assert nb.cells[0].cell_type == "markdown"
            assert "# Test Notebook" in nb.cells[0].source
            assert nb.cells[1].cell_type == "code"
            assert "print('Hello, World!')" in nb.cells[1].source
            
        finally:
            os.unlink(txt_path)
            os.unlink(ipynb_path)
    
    def test_text_with_different_language(self):
        txt_content = """# test_notebook.ipynb

```markdown
# R Notebook

This is an R notebook.
```

```r
x <- c(1, 2, 3)
print(x)
```"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(txt_content)
            txt_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.ipynb', delete=False) as f:
            ipynb_path = f.name
        
        try:
            convert_txt_to_ipynb(txt_path, ipynb_path)
            
            import nbformat
            nb = nbformat.read(ipynb_path, as_version=4)
            
            assert len(nb.cells) == 2
            assert nb.cells[0].cell_type == "markdown"
            assert nb.cells[1].cell_type == "code"
            assert "x <- c(1, 2, 3)" in nb.cells[1].source
            
            # Check that kernel metadata was set correctly
            assert nb.metadata["kernelspec"]["language"] == "r"
            assert nb.metadata["kernelspec"]["name"] == "ir"
            assert nb.metadata["kernelspec"]["display_name"] == "R"
            
        finally:
            os.unlink(txt_path)
            os.unlink(ipynb_path)
    
    def test_text_with_dynamic_fences(self):
        txt_content = """# test_notebook.ipynb

````markdown
Here's some code:

```python
x = 1
```
````

```python
print(x)
```"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(txt_content)
            txt_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.ipynb', delete=False) as f:
            ipynb_path = f.name
        
        try:
            convert_txt_to_ipynb(txt_path, ipynb_path)
            
            import nbformat
            nb = nbformat.read(ipynb_path, as_version=4)
            
            assert len(nb.cells) == 2
            assert nb.cells[0].cell_type == "markdown"
            assert "```python" in nb.cells[0].source  # Inner code block
            assert nb.cells[1].cell_type == "code"
            assert "print(x)" in nb.cells[1].source
            
        finally:
            os.unlink(txt_path)
            os.unlink(ipynb_path)


class TestRoundTrip:
    def test_round_trip_conversion(self):
        # Create a complex test notebook
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": "# Complex Test\n\nThis notebook has:\n\n- **Bold text**\n- *Italic text*\n- `inline code`"
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
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            import json
            json.dump(notebook_content, f)
            original_ipynb = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            txt_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.ipynb', delete=False) as f:
            roundtrip_ipynb = f.name
        
        try:
            # Convert ipynb -> txt
            result = convert_ipynb_to_txt(original_ipynb, txt_path)
            with open(txt_path, 'w') as f:
                f.write(result)
            
            # Convert txt -> ipynb
            convert_txt_to_ipynb(txt_path, roundtrip_ipynb)
            
            # Compare the notebooks
            import nbformat
            original = nbformat.read(original_ipynb, as_version=4)
            roundtrip = nbformat.read(roundtrip_ipynb, as_version=4)
            
            assert len(original.cells) == len(roundtrip.cells)
            
            for i, (orig_cell, rt_cell) in enumerate(zip(original.cells, roundtrip.cells)):
                assert orig_cell.cell_type == rt_cell.cell_type
                # Note: We don't compare exact source due to potential whitespace differences
                assert orig_cell.source.strip() == rt_cell.source.strip()
            
        finally:
            for path in [original_ipynb, txt_path, roundtrip_ipynb]:
                if os.path.exists(path):
                    os.unlink(path)


if __name__ == "__main__":
    pytest.main([__file__]) 