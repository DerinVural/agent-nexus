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

🔧 NexusPilotAgent tarafından genişletildi (v2.2):
- Decorator analizi eklendi (@property, @staticmethod, @classmethod vb.)
- get_decorator_changes() fonksiyonu eklendi
- analyze_python_changes() artık decorator_changes içeriyor

🔧 OpusAgent tarafından genişletildi (v2.3):
- Docstring analizi eklendi
- get_docstring_changes() fonksiyonu eklendi
- analyze_python_changes() artık docstring_changes içeriyor
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


def _extract_decorators(tree: ast.AST) -> Dict[str, List[str]]:
    """
    Fonksiyon ve class başına decorator listesi döndürür.
    NexusPilotAgent tarafından eklendi.
    
    Returns: {"func_name": ["@property", "@staticmethod"], ...}
    """
    decorators = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.decorator_list:
                decs = []
                for d in node.decorator_list:
                    try:
                        decs.append(f"@{ast.unparse(d)}")
                    except:
                        # Fallback for older Python versions
                        if isinstance(d, ast.Name):
                            decs.append(f"@{d.id}")
                        elif isinstance(d, ast.Attribute):
                            decs.append(f"@{d.attr}")
                        else:
                            decs.append("@<unknown>")
                if decs:
                    decorators[node.name] = decs
    return decorators


def get_decorator_changes(old_tree: ast.AST, new_tree: ast.AST) -> Dict[str, Dict[str, List[str]]]:
    """
    Fonksiyon/class bazlı decorator değişikliklerini döndürür.
    NexusPilotAgent tarafından eklendi.
    
    Returns: {"func_name": {"added": ["@property"], "removed": ["@deprecated"]}}
    
    Örnek:
        old_code: def foo(): pass
        new_code: @property
                  def foo(): pass
        result: {"foo": {"added": ["@property"], "removed": []}}
    """
    old_decs = _extract_decorators(old_tree)
    new_decs = _extract_decorators(new_tree)
    
    all_names = set(old_decs.keys()) | set(new_decs.keys())
    decorator_changes = {}
    
    for name in all_names:
        old_d = set(old_decs.get(name, []))
        new_d = set(new_decs.get(name, []))
        
        added = new_d - old_d
        removed = old_d - new_d
        
        if added or removed:
            decorator_changes[name] = {
                "added": list(added),
                "removed": list(removed)
            }
    
    return decorator_changes


def _extract_docstrings(tree: ast.AST) -> Dict[str, Optional[str]]:
    """
    Fonksiyon, class ve modül başına docstring döndürür.
    OpusAgent tarafından eklendi (v2.3).
    
    Returns: {"func_name": "Docstring içeriği", ...}
    """
    docstrings = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            docstring = ast.get_docstring(node)
            if docstring:
                docstrings[node.name] = docstring
        elif isinstance(node, ast.Module):
            docstring = ast.get_docstring(node)
            if docstring:
                docstrings["__module__"] = docstring
    return docstrings


def get_docstring_changes(old_tree: ast.AST, new_tree: ast.AST) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Fonksiyon/class bazlı docstring değişikliklerini döndürür.
    OpusAgent tarafından eklendi (v2.3).
    
    Returns: {"func_name": {"old": "Eski docstring", "new": "Yeni docstring"}}
    
    Örnek:
        old_code: def foo(): pass
        new_code: def foo():
                    '''Yeni docstring'''
                    pass
        result: {"foo": {"old": None, "new": "Yeni docstring"}}
    """
    old_docs = _extract_docstrings(old_tree)
    new_docs = _extract_docstrings(new_tree)
    
    all_names = set(old_docs.keys()) | set(new_docs.keys())
    docstring_changes = {}
    
    for name in all_names:
        old_doc = old_docs.get(name)
        new_doc = new_docs.get(name)
        
        if old_doc != new_doc:
            docstring_changes[name] = {
                "old": old_doc,
                "new": new_doc
            }
    
    return docstring_changes


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
        
        # Decorator değişiklikleri - NexusPilotAgent tarafından eklendi (v2.2)
        decorator_changes = get_decorator_changes(old_tree, new_tree)
        
        # Docstring değişiklikleri - OpusAgent tarafından eklendi (v2.3)
        docstring_changes = get_docstring_changes(old_tree, new_tree)
        
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
            # Decorator Değişiklikleri - NexusPilotAgent (v2.2)
            "decorator_changes": decorator_changes,
            # Docstring Değişiklikleri - OpusAgent (v2.3)
            "docstring_changes": docstring_changes,
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
            "decorators": _extract_decorators(tree),  # NexusPilotAgent tarafından eklendi
            "docstrings": _extract_docstrings(tree),  # OpusAgent tarafından eklendi (v2.3)
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
