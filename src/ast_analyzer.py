"""
AST Analyzer Module - CopilotAgent tarafından eklendi
Bu modül kod değişikliklerini AST seviyesinde analiz eder.

🔧 OpusAgent tarafından genişletildi:
- Class değişikliği analizi eklendi
- Import analizi eklendi
- AsyncFunctionDef desteği eklendi
"""
import ast
from typing import Dict, List, Set, Optional


def _extract_imports(tree: ast.AST) -> Set[str]:
    """AST ağacından tüm import'ları çıkarır."""
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.add(f"{module}.{alias.name}" if module else alias.name)
    return imports


def _extract_classes(tree: ast.AST) -> Set[str]:
    """AST ağacından tüm class isimlerini çıkarır."""
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)}


def _extract_functions(tree: ast.AST) -> Set[str]:
    """AST ağacından tüm fonksiyon isimlerini çıkarır (async dahil)."""
    funcs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs.add(node.name)
    return funcs


def analyze_python_changes(old_code: str, new_code: str) -> Optional[Dict[str, List[str]]]:
    """İki Python kodu arasındaki fonksiyon, class ve import değişikliklerini tespit eder."""
    try:
        old_tree = ast.parse(old_code)
        new_tree = ast.parse(new_code)
        
        # Fonksiyon analizi
        old_funcs = _extract_functions(old_tree)
        new_funcs = _extract_functions(new_tree)
        
        # Class analizi
        old_classes = _extract_classes(old_tree)
        new_classes = _extract_classes(new_tree)
        
        # Import analizi
        old_imports = _extract_imports(old_tree)
        new_imports = _extract_imports(new_tree)
        
        return {
            # Fonksiyonlar
            "added_functions": list(new_funcs - old_funcs),
            "removed_functions": list(old_funcs - new_funcs),
            "modified_functions": list(old_funcs & new_funcs),
            # Classlar
            "added_classes": list(new_classes - old_classes),
            "removed_classes": list(old_classes - new_classes),
            "modified_classes": list(old_classes & new_classes),
            # Importlar
            "added_imports": list(new_imports - old_imports),
            "removed_imports": list(old_imports - new_imports),
        }
    except SyntaxError:
        return None


def get_code_summary(code: str) -> Optional[Dict[str, List[str]]]:
    """Tek bir Python kodunun özetini çıkarır."""
    try:
        tree = ast.parse(code)
        return {
            "functions": list(_extract_functions(tree)),
            "classes": list(_extract_classes(tree)),
            "imports": list(_extract_imports(tree)),
        }
    except SyntaxError:
        return None


if __name__ == "__main__":
    # Test - OpusAgent tarafından genişletildi
    old = """
import os
class Hello:
    def greet(self): pass
def hello(): pass
"""
    new = """
import os
import sys
class Hello:
    def greet(self): pass
class World:
    pass
def hello(): pass
def world(): pass
async def async_func(): pass
"""
    result = analyze_python_changes(old, new)
    print("=== AST Analysis Result ===")
    print(f"Added functions: {result['added_functions']}")
    print(f"Removed functions: {result['removed_functions']}")
    print(f"Added classes: {result['added_classes']}")
    print(f"Removed classes: {result['removed_classes']}")
    print(f"Added imports: {result['added_imports']}")
    print(f"Removed imports: {result['removed_imports']}")
    
    print("\n=== Code Summary ===")
    summary = get_code_summary(new)
    print(f"Functions: {summary['functions']}")
    print(f"Classes: {summary['classes']}")
    print(f"Imports: {summary['imports']}")
