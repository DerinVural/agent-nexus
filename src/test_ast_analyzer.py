"""
AST Analyzer Unit Tests - NexusPilotAgent tarafından eklendi
Bu modül ast_analyzer.py için kapsamlı unit testler içerir.

🧪 Test Coverage:
- Fonksiyon ekleme/silme tespiti
- Class ekleme/silme tespiti
- Method değişiklik takibi
- Import analizi
- Async fonksiyon desteği
- Decorator analizi (v2.2 - NexusPilotAgent)
- Edge case'ler
"""
import unittest
import ast
from ast_analyzer import (
    analyze_python_changes,
    get_code_summary,
    get_class_method_changes,
    get_decorator_changes,
    _extract_functions,
    _extract_classes,
    _extract_imports,
    _extract_class_methods,
    _extract_decorators,
)


class TestFunctionExtraction(unittest.TestCase):
    """Fonksiyon çıkarma testleri"""
    
    def test_simple_function(self):
        code = "def hello(): pass"
        tree = ast.parse(code)
        funcs = _extract_functions(tree)
        self.assertEqual(funcs, {"hello"})
    
    def test_multiple_functions(self):
        code = """
def foo(): pass
def bar(): pass
def baz(): pass
"""
        tree = ast.parse(code)
        funcs = _extract_functions(tree)
        self.assertEqual(funcs, {"foo", "bar", "baz"})
    
    def test_async_function(self):
        code = "async def async_hello(): pass"
        tree = ast.parse(code)
        funcs = _extract_functions(tree)
        self.assertEqual(funcs, {"async_hello"})
    
    def test_mixed_functions(self):
        code = """
def sync_func(): pass
async def async_func(): pass
"""
        tree = ast.parse(code)
        funcs = _extract_functions(tree)
        self.assertEqual(funcs, {"sync_func", "async_func"})
    
    def test_nested_functions(self):
        code = """
def outer():
    def inner(): pass
    return inner
"""
        tree = ast.parse(code)
        funcs = _extract_functions(tree)
        self.assertIn("outer", funcs)
        self.assertIn("inner", funcs)


class TestClassExtraction(unittest.TestCase):
    """Class çıkarma testleri"""
    
    def test_simple_class(self):
        code = "class MyClass: pass"
        tree = ast.parse(code)
        classes = _extract_classes(tree)
        self.assertEqual(classes, {"MyClass"})
    
    def test_multiple_classes(self):
        code = """
class Foo: pass
class Bar: pass
"""
        tree = ast.parse(code)
        classes = _extract_classes(tree)
        self.assertEqual(classes, {"Foo", "Bar"})
    
    def test_inherited_class(self):
        code = """
class Base: pass
class Derived(Base): pass
"""
        tree = ast.parse(code)
        classes = _extract_classes(tree)
        self.assertEqual(classes, {"Base", "Derived"})


class TestImportExtraction(unittest.TestCase):
    """Import çıkarma testleri"""
    
    def test_simple_import(self):
        code = "import os"
        tree = ast.parse(code)
        imports = _extract_imports(tree)
        self.assertEqual(imports, {"os"})
    
    def test_multiple_imports(self):
        code = """
import os
import sys
import ast
"""
        tree = ast.parse(code)
        imports = _extract_imports(tree)
        self.assertEqual(imports, {"os", "sys", "ast"})
    
    def test_from_import(self):
        code = "from typing import Dict, List"
        tree = ast.parse(code)
        imports = _extract_imports(tree)
        self.assertIn("typing.Dict", imports)
        self.assertIn("typing.List", imports)
    
    def test_mixed_imports(self):
        code = """
import json
from pathlib import Path
from os import path
"""
        tree = ast.parse(code)
        imports = _extract_imports(tree)
        self.assertIn("json", imports)
        self.assertIn("pathlib.Path", imports)
        self.assertIn("os.path", imports)


class TestClassMethodExtraction(unittest.TestCase):
    """Class method çıkarma testleri"""
    
    def test_class_with_methods(self):
        code = """
class MyClass:
    def __init__(self): pass
    def method_one(self): pass
    def method_two(self): pass
"""
        tree = ast.parse(code)
        methods = _extract_class_methods(tree)
        self.assertEqual(methods["MyClass"], {"__init__", "method_one", "method_two"})
    
    def test_async_methods(self):
        code = """
class Agent:
    async def run(self): pass
    async def stop(self): pass
"""
        tree = ast.parse(code)
        methods = _extract_class_methods(tree)
        self.assertEqual(methods["Agent"], {"run", "stop"})
    
    def test_multiple_classes_with_methods(self):
        code = """
class Alpha:
    def a(self): pass
class Beta:
    def b(self): pass
"""
        tree = ast.parse(code)
        methods = _extract_class_methods(tree)
        self.assertEqual(methods["Alpha"], {"a"})
        self.assertEqual(methods["Beta"], {"b"})


class TestGetClassMethodChanges(unittest.TestCase):
    """Class method değişiklik tespiti testleri"""
    
    def test_added_method(self):
        old_code = """
class WatcherState:
    def __init__(self): pass
"""
        new_code = """
class WatcherState:
    def __init__(self): pass
    def update_head(self): pass
"""
        old_tree = ast.parse(old_code)
        new_tree = ast.parse(new_code)
        changes = get_class_method_changes(old_tree, new_tree)
        
        self.assertIn("WatcherState", changes)
        self.assertIn("update_head", changes["WatcherState"]["added"])
    
    def test_removed_method(self):
        old_code = """
class Agent:
    def run(self): pass
    def deprecated_method(self): pass
"""
        new_code = """
class Agent:
    def run(self): pass
"""
        old_tree = ast.parse(old_code)
        new_tree = ast.parse(new_code)
        changes = get_class_method_changes(old_tree, new_tree)
        
        self.assertIn("Agent", changes)
        self.assertIn("deprecated_method", changes["Agent"]["removed"])
    
    def test_no_changes(self):
        code = """
class NoChange:
    def method(self): pass
"""
        tree = ast.parse(code)
        changes = get_class_method_changes(tree, tree)
        
        # Değişiklik yoksa class'ı eklememeli
        self.assertNotIn("NoChange", changes)


class TestAnalyzePythonChanges(unittest.TestCase):
    """analyze_python_changes entegrasyon testleri"""
    
    def test_full_analysis(self):
        old_code = """
import os
class Hello:
    def greet(self): pass
def hello(): pass
"""
        new_code = """
import os
import sys
class Hello:
    def greet(self): pass
    def wave(self): pass
class World:
    def spin(self): pass
def hello(): pass
def world(): pass
"""
        result = analyze_python_changes(old_code, new_code)
        
        self.assertIsNotNone(result)
        self.assertIn("world", result["added_functions"])
        self.assertIn("World", result["added_classes"])
        self.assertIn("sys", result["added_imports"])
        self.assertIn("Hello", result["method_changes"])
    
    def test_syntax_error_handling(self):
        invalid_code = "def broken("
        result = analyze_python_changes("def valid(): pass", invalid_code)
        self.assertIsNone(result)
    
    def test_empty_code(self):
        result = analyze_python_changes("", "")
        self.assertIsNotNone(result)
        self.assertEqual(result["added_functions"], [])


class TestGetCodeSummary(unittest.TestCase):
    """get_code_summary testleri"""
    
    def test_summary(self):
        code = """
import json
class Parser:
    def parse(self): pass
def main(): pass
"""
        summary = get_code_summary(code)
        
        self.assertIsNotNone(summary)
        self.assertIn("main", summary["functions"])
        self.assertIn("Parser", summary["classes"])
        self.assertIn("json", summary["imports"])
        self.assertEqual(summary["class_methods"]["Parser"], ["parse"])
    
    def test_invalid_code(self):
        summary = get_code_summary("def broken(")
        self.assertIsNone(summary)


class TestDecoratorExtraction(unittest.TestCase):
    """Decorator çıkarma testleri - NexusPilotAgent tarafından eklendi (v2.2)"""
    
    def test_simple_decorator(self):
        code = "@property\ndef name(self): pass"
        tree = ast.parse(code)
        decorators = _extract_decorators(tree)
        self.assertIn("name", decorators)
        self.assertIn("@property", decorators["name"])
    
    def test_multiple_decorators(self):
        code = """
@decorator1
@decorator2
def func(): pass
"""
        tree = ast.parse(code)
        decorators = _extract_decorators(tree)
        self.assertEqual(len(decorators["func"]), 2)
    
    def test_class_decorator(self):
        code = "@dataclass\nclass MyClass: pass"
        tree = ast.parse(code)
        decorators = _extract_decorators(tree)
        self.assertIn("MyClass", decorators)
        self.assertIn("@dataclass", decorators["MyClass"])
    
    def test_no_decorators(self):
        code = "def plain(): pass"
        tree = ast.parse(code)
        decorators = _extract_decorators(tree)
        self.assertNotIn("plain", decorators)


class TestDecoratorChanges(unittest.TestCase):
    """Decorator değişiklik tespiti testleri - NexusPilotAgent (v2.2)"""
    
    def test_added_decorator(self):
        old_code = "def foo(): pass"
        new_code = "@property\ndef foo(self): pass"
        old_tree = ast.parse(old_code)
        new_tree = ast.parse(new_code)
        changes = get_decorator_changes(old_tree, new_tree)
        
        self.assertIn("foo", changes)
        self.assertIn("@property", changes["foo"]["added"])
    
    def test_removed_decorator(self):
        old_code = "@deprecated\ndef old_func(): pass"
        new_code = "def old_func(): pass"
        old_tree = ast.parse(old_code)
        new_tree = ast.parse(new_code)
        changes = get_decorator_changes(old_tree, new_tree)
        
        self.assertIn("old_func", changes)
        self.assertIn("@deprecated", changes["old_func"]["removed"])
    
    def test_no_decorator_changes(self):
        code = "@staticmethod\ndef helper(): pass"
        tree = ast.parse(code)
        changes = get_decorator_changes(tree, tree)
        self.assertEqual(changes, {})
    
    def test_decorator_swap(self):
        old_code = "@classmethod\ndef method(cls): pass"
        new_code = "@staticmethod\ndef method(): pass"
        old_tree = ast.parse(old_code)
        new_tree = ast.parse(new_code)
        changes = get_decorator_changes(old_tree, new_tree)
        
        self.assertIn("method", changes)
        self.assertIn("@staticmethod", changes["method"]["added"])
        self.assertIn("@classmethod", changes["method"]["removed"])


class TestAnalyzePythonChangesWithDecorators(unittest.TestCase):
    """analyze_python_changes decorator entegrasyon testleri"""
    
    def test_decorator_changes_in_analysis(self):
        old_code = "def foo(): pass"
        new_code = "@property\ndef foo(self): pass"
        result = analyze_python_changes(old_code, new_code)
        
        self.assertIn("decorator_changes", result)
        self.assertIn("foo", result["decorator_changes"])


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 AST Analyzer Unit Tests - NexusPilotAgent")
    print("=" * 60)
    unittest.main(verbosity=2)
