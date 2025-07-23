import pytest
import tempfile
import os
import subprocess
import sys
from pathlib import Path
from nb4llm.cli import main


class TestCLI:
    def test_help(self):
        """Test that help is displayed correctly"""
        result = subprocess.run([sys.executable, "-m", "nb4llm.cli", "--help"], 
                              capture_output=True, text=True)
        assert result.returncode == 0
        assert "Convert Jupyter notebooks" in result.stdout
        assert "Examples:" in result.stdout
    
    def test_missing_input_file(self):
        """Test error handling for missing input file"""
        result = subprocess.run([sys.executable, "-m", "nb4llm.cli", "nonexistent.ipynb"], 
                              capture_output=True, text=True)
        assert result.returncode == 1
        assert "does not exist" in result.stderr
    
    def test_basic_ipynb_to_txt(self):
        """Test basic ipynb to txt conversion"""
        # Create a simple test notebook
        notebook_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": "# Test"
                },
                {
                    "cell_type": "code",
                    "metadata": {},
                    "outputs": [],
                    "source": "print('test')"
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
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            txt_path = f.name
        
        try:
            result = subprocess.run([sys.executable, "-m", "nb4llm.cli", ipynb_path, txt_path], 
                                  capture_output=True, text=True)
            
            assert result.returncode == 0
            assert "Successfully converted" in result.stdout
            
            # Check the output file
            with open(txt_path, 'r') as f:
                content = f.read()
                assert "# test_notebook.ipynb" in content
                assert "```markdown" in content
                assert "```python" in content
                
        finally:
            for path in [ipynb_path, txt_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_basic_txt_to_ipynb(self):
        """Test basic txt to ipynb conversion"""
        txt_content = """# test_notebook.ipynb

```markdown
# Test
```

```python
print('test')
```"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(txt_content)
            txt_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.ipynb', delete=False) as f:
            ipynb_path = f.name
        
        try:
            result = subprocess.run([sys.executable, "-m", "nb4llm.cli", "--reverse", txt_path, ipynb_path], 
                                  capture_output=True, text=True)
            
            assert result.returncode == 0
            assert "Successfully converted" in result.stdout
            
            # Check the output file is a valid notebook
            import nbformat
            nb = nbformat.read(ipynb_path, as_version=4)
            assert len(nb.cells) == 2
            assert nb.cells[0].cell_type == "markdown"
            assert nb.cells[1].cell_type == "code"
                
        finally:
            for path in [txt_path, ipynb_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_auto_output_filename(self):
        """Test automatic output filename generation"""
        notebook_content = {
            "cells": [{"cell_type": "markdown", "metadata": {}, "source": "# Test"}],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            import json
            json.dump(notebook_content, f)
            ipynb_path = f.name
        
        try:
            result = subprocess.run([sys.executable, "-m", "nb4llm.cli", ipynb_path], 
                                  capture_output=True, text=True)
            
            assert result.returncode == 0
            assert "Successfully converted" in result.stdout
            
            # Check that .txt file was created
            expected_txt = Path(ipynb_path).with_suffix('.txt')
            assert expected_txt.exists()
            expected_txt.unlink()
                
        finally:
            if os.path.exists(ipynb_path):
                os.unlink(ipynb_path)
    
    def test_verbose_output(self):
        """Test verbose output flag"""
        notebook_content = {
            "cells": [{"cell_type": "markdown", "metadata": {}, "source": "# Test"}],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            import json
            json.dump(notebook_content, f)
            ipynb_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            txt_path = f.name
        
        try:
            result = subprocess.run([sys.executable, "-m", "nb4llm.cli", "-v", ipynb_path, txt_path], 
                                  capture_output=True, text=True)
            
            assert result.returncode == 0
            assert "Converting" in result.stdout
            
        finally:
            for path in [ipynb_path, txt_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_wrong_extension_warning(self):
        """Test warning for wrong file extension"""
        # Create a .txt file but try to convert it as .ipynb
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is not a notebook")
            txt_path = f.name
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            output_path = f.name
        
        try:
            result = subprocess.run([sys.executable, "-m", "nb4llm.cli", txt_path, output_path], 
                                  capture_output=True, text=True)
            
            assert result.returncode == 1  # Should fail because it's not a valid notebook
            assert "doesn't have .ipynb extension" in result.stderr
            
        finally:
            for path in [txt_path, output_path]:
                if os.path.exists(path):
                    os.unlink(path)


if __name__ == "__main__":
    pytest.main([__file__]) 