#!/usr/bin/env python3
"""
Tests for ast_analyzer.py
CopilotOpusAgent - Test Suite v1.0
"""

import pytest
import ast

from ast_analyzer import (
    _extract_imports,
    _extract_classes,
    _extract_functions,
    _extract_class_methods,
    _extract_decorators,
    _extract_docstrings,
    get_decorator_changes,
    get_docstring_changes,
    get_class_method_changes,
    get_type_annotation_changes,
    get_complexity_report,
    get_complexity_changes,
    get_function_complexity,
    analyze_python_changes,
    get_code_summary,
)


class TestExtractImports:
    """Test _extract_imports function"""
    
    def test_simple_import(self):
        """Test simple import extraction"""
        code = "import os"
        tree = ast.parse(code)
        imports = _extract_imports(tree)
        assert "os" in imports
    
    def test_from_import(self):
        """Test from...import extraction"""
        code = "from os import path"
        tree = ast.parse(code)
        imports = _extract_imports(tree)
        assert "os.path" in imports
    
    def test_multiple_imports(self):
        """Test multiple imports"""
        code = """
import os
import sys
from typing import List, Dict
"""
        tree = ast.parse(code)
        imports = _extract_imports(tree)
        assert "os" in imports
        assert "sys" in imports
        assert "typing.List" in imports
        assert "typing.Dict" in imports
    
    def test_no_imports(self):
        """Test code with no imports"""
        code = "x = 1"
        tree = ast.parse(code)
        imports = _extract_imports(tree)
        assert len(imports) == 0


class TestExtractClasses:
    """Test _extract_classes function"""
    
    def test_single_class(self):
        """Test single class extraction"""
        code = "class MyClass:\n    pass"
        tree = ast.parse(code)
        classes = _extract_classes(tree)
        assert "MyClass" in classes
    
    def test_multiple_classes(self):
        """Test multiple classes"""
        code = """
class ClassA:
    pass

class ClassB:
    pass
"""
        tree = ast.parse(code)
        classes = _extract_classes(tree)
        assert "ClassA" in classes
        assert "ClassB" in classes
    
    def test_no_classes(self):
        """Test code with no classes"""
        code = "def func(): pass"
        tree = ast.parse(code)
        classes = _extract_classes(tree)
        assert len(classes) == 0


class TestExtractFunctions:
    """Test _extract_functions function"""
    
    def test_single_function(self):
        """Test single function extraction"""
        code = "def my_func():\n    pass"
        tree = ast.parse(code)
        funcs = _extract_functions(tree)
        assert "my_func" in funcs
    
    def test_async_function(self):
        """Test async function extraction"""
        code = "async def async_func():\n    pass"
        tree = ast.parse(code)
        funcs = _extract_functions(tree)
        assert "async_func" in funcs
    
    def test_mixed_functions(self):
        """Test mix of sync and async functions"""
        code = """
def sync_func():
    pass

async def async_func():
    pass
"""
        tree = ast.parse(code)
        funcs = _extract_functions(tree)
        assert "sync_func" in funcs
        assert "async_func" in funcs


class TestExtractClassMethods:
    """Test _extract_class_methods function"""
    
    def test_class_with_methods(self):
        """Test class method extraction"""
        code = """
class MyClass:
    def method1(self):
        pass
    
    def method2(self):
        pass
"""
        tree = ast.parse(code)
        class_methods = _extract_class_methods(tree)
        assert "MyClass" in class_methods
        assert "method1" in class_methods["MyClass"]
        assert "method2" in class_methods["MyClass"]
    
    def test_class_with_async_methods(self):
        """Test class with async methods"""
        code = """
class MyClass:
    async def async_method(self):
        pass
"""
        tree = ast.parse(code)
        class_methods = _extract_class_methods(tree)
        assert "async_method" in class_methods["MyClass"]


class TestExtractDecorators:
    """Test _extract_decorators function"""
    
    def test_property_decorator(self):
        """Test property decorator extraction"""
        code = """
class MyClass:
    @property
    def name(self):
        return self._name
"""
        tree = ast.parse(code)
        decorators = _extract_decorators(tree)
        assert "name" in decorators
        assert "@property" in decorators["name"]
    
    def test_multiple_decorators(self):
        """Test multiple decorators"""
        code = """
@decorator1
@decorator2
def my_func():
    pass
"""
        tree = ast.parse(code)
        decorators = _extract_decorators(tree)
        assert "my_func" in decorators
        assert len(decorators["my_func"]) == 2


class TestExtractDocstrings:
    """Test _extract_docstrings function"""
    
    def test_function_docstring(self):
        """Test function docstring extraction"""
        code = '''
def my_func():
    """This is a docstring."""
    pass
'''
        tree = ast.parse(code)
        docstrings = _extract_docstrings(tree)
        assert "my_func" in docstrings
        assert "docstring" in docstrings["my_func"].lower()
    
    def test_class_docstring(self):
        """Test class docstring extraction"""
        code = '''
class MyClass:
    """Class docstring."""
    pass
'''
        tree = ast.parse(code)
        docstrings = _extract_docstrings(tree)
        assert "MyClass" in docstrings


class TestGetComplexityReport:
    """Test get_complexity_report function"""
    
    def test_simple_function_complexity(self):
        """Test complexity of simple function"""
        code = """
def simple_func():
    return 1
"""
        tree = ast.parse(code)
        report = get_complexity_report(tree)
        assert "simple_func" in report
        assert report["simple_func"]["complexity"] == 1
    
    def test_conditional_complexity(self):
        """Test complexity with conditionals"""
        code = """
def complex_func(x):
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0
"""
        tree = ast.parse(code)
        report = get_complexity_report(tree)
        assert "complex_func" in report
        # if + elif = 2 additional branches
        assert report["complex_func"]["complexity"] >= 3


class TestAnalyzePythonChanges:
    """Test main analyze_python_changes function"""
    
    def test_full_analysis(self):
        """Test full analysis output"""
        old_code = """
import os

class OldClass:
    def old_method(self):
        pass
"""
        new_code = """
import os
import sys

class OldClass:
    def old_method(self):
        pass
    
    def new_method(self):
        pass

class NewClass:
    pass

def new_function():
    pass
"""
        result = analyze_python_changes(old_code, new_code)
        
        assert result is not None
        assert "added_functions" in result
        assert "added_classes" in result
        assert "added_imports" in result
    
    def test_syntax_error_handling(self):
        """Test handling of syntax errors"""
        old_code = "x = 1"
        new_code = "def invalid("  # Syntax error
        result = analyze_python_changes(old_code, new_code)
        
        # Should return None for syntax errors
        assert result is None


class TestGetCodeSummary:
    """Test get_code_summary function"""
    
    def test_basic_summary(self):
        """Test basic code summary"""
        code = """
import os

class MyClass:
    def method(self):
        pass

def my_func():
    pass
"""
        result = get_code_summary(code)
        
        assert result is not None
        assert "imports" in result
        assert "classes" in result
        assert "functions" in result
    
    def test_empty_code(self):
        """Test summary of empty code"""
        result = get_code_summary("")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
