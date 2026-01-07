"""
AST Analyzer Module - CopilotAgent tarafından eklendi
Bu modül kod değişikliklerini AST seviyesinde analiz eder.

🔧 OpusAgent tarafından genişletildi:
- Class değişikliği analizi eklendi
- Import analizi eklendi
- AsyncFunctionDef desteği eklendi

🔧 CopilotAgent tarafından genişletildi (v2.1):
- get_class_method_changes() eklendi - Class bazlı method değişikliklerini izler
- analyze_python_changes() artık method_changes içeriyor
"""
import ast
from typing import Dict, List, Set, Optional, Any


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


def _extract_class_methods(tree: ast.AST) -> Dict[str, Set[str]]:
    """Her class için method isimlerini döndürür."""
    class_methods = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = set()
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.add(item.name)
            class_methods[node.name] = methods
    return class_methods


def get_class_method_changes(old_tree: ast.AST, new_tree: ast.AST) -> Dict[str, Dict[str, List[str]]]:
    """
    Her class için method değişikliklerini döndürür.
    Returns: {"ClassName": {"added": [...], "removed": [...]}}
    
    Örnek çıktı:
    {
        "WatcherState": {"added": ["update_head", "reset"], "removed": []},
        "Agent": {"added": ["stop"], "removed": ["pause"]}
    }
    """
    old_methods = _extract_class_methods(old_tree)
    new_methods = _extract_class_methods(new_tree)
    
    all_classes = set(old_methods.keys()) | set(new_methods.keys())
    method_changes = {}
    
    for cls_name in all_classes:
        old_m = old_methods.get(cls_name, set())
        new_m = new_methods.get(cls_name, set())
        
        added = new_m - old_m
        removed = old_m - new_m
        
        # Sadece değişiklik varsa ekle
        if added or removed:
            method_changes[cls_name] = {
                "added": list(added),
                "removed": list(removed)
            }
    
    return method_changes


def analyze_python_changes(old_code: str, new_code: str) -> Optional[Dict[str, Any]]:
    """İki Python kodu arasındaki fonksiyon, class, method ve import değişikliklerini tespit eder."""
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
        
        # Class method değişiklikleri (YENİ!)
        method_changes = get_class_method_changes(old_tree, new_tree)
        
        return {
            # Fonksiyonlar
            "added_functions": list(new_funcs - old_funcs),
            "removed_functions": list(old_funcs - new_funcs),
            "modified_functions": list(old_funcs & new_funcs),
            # Classlar
            "added_classes": list(new_classes - old_classes),
            "removed_classes": list(old_classes - new_classes),
            "modified_classes": list(old_classes & new_classes),
            # Class Method Değişiklikleri (YENİ!)
            "method_changes": method_changes,
            # Importlar
            "added_imports": list(new_imports - old_imports),
            "removed_imports": list(old_imports - new_imports),
        }
    except SyntaxError:
        return None


def get_code_summary(code: str) -> Optional[Dict[str, Any]]:
    """Tek bir Python kodunun özetini çıkarır."""
    try:
        tree = ast.parse(code)
        return {
            "functions": list(_extract_functions(tree)),
            "classes": list(_extract_classes(tree)),
            "class_methods": {k: list(v) for k, v in _extract_class_methods(tree).items()},
            "imports": list(_extract_imports(tree)),
        }
    except SyntaxError:
        return None


if __name__ == "__main__":
    # Test - CopilotAgent & OpusAgent ortak çalışması
    print("=" * 50)
    print("AST Analyzer v2.1 - Test Suite")
    print("=" * 50)
    
    # Test 1: Fonksiyon ve class değişiklikleri
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
    def wave(self): pass
class World:
    def spin(self): pass
def hello(): pass
def world(): pass
async def async_func(): pass
"""
    result = analyze_python_changes(old, new)
    
    print("\n📊 Test 1: Temel Analiz")
    print(f"  Eklenen fonksiyonlar: {result['added_functions']}")
    print(f"  Eklenen classlar: {result['added_classes']}")
    print(f"  Eklenen importlar: {result['added_imports']}")
    
    print("\n🔧 Test 2: Class Method Değişiklikleri")
    print(f"  Method değişiklikleri: {result['method_changes']}")
    
    # Test 3: WatcherState benzeri senaryo
    print("\n⚡ Test 3: WatcherState Senaryosu")
    old_watcher = """
class WatcherState:
    def __init__(self): pass
    def check(self): pass
"""
    new_watcher = """
class WatcherState:
    def __init__(self): pass
    def check(self): pass
    def update_head(self): pass
    def reset(self): pass
"""
    watcher_result = analyze_python_changes(old_watcher, new_watcher)
    print(f"  WatcherState değişiklikleri: {watcher_result['method_changes']}")
    
    print("\n📋 Test 4: Kod Özeti")
    summary = get_code_summary(new)
    print(f"  Fonksiyonlar: {summary['functions']}")
    print(f"  Classlar: {summary['classes']}")
    print(f"  Class methodları: {summary['class_methods']}")
    print(f"  Importlar: {summary['imports']}")
    
    print("\n✅ Tüm testler tamamlandı!")
