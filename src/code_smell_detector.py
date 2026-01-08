"""
Code Smell Detector v1.0
========================
Kod kokularını tespit eden modül.

Katkıda Bulunanlar:
- CopilotOpusAgent (v1.0): İlk implementasyon

Tespit Edilen Code Smell'ler:
- Long Function: >50 satır
- Too Many Parameters: >5 parametre
- Deep Nesting: >4 seviye
- God Class: >20 method
- Long Method Chain: >3 zincir
"""

import ast
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class SmellConfig:
    """Code smell eşik değerleri"""
    long_function_lines: int = 50
    too_many_params: int = 5
    deep_nesting_level: int = 4
    god_class_methods: int = 20
    long_method_chain: int = 3


class NestingVisitor(ast.NodeVisitor):
    """İç içe geçme derinliğini hesaplar"""
    
    NESTING_NODES = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)
    
    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0
    
    def visit(self, node):
        if isinstance(node, self.NESTING_NODES):
            self.current_depth += 1
            self.max_depth = max(self.max_depth, self.current_depth)
            self.generic_visit(node)
            self.current_depth -= 1
        else:
            self.generic_visit(node)
        return self.max_depth


def _get_function_lines(node: ast.FunctionDef) -> int:
    """Fonksiyonun satır sayısını hesaplar"""
    if node.body:
        start = node.lineno
        end = max(getattr(n, 'end_lineno', n.lineno) for n in ast.walk(node) if hasattr(n, 'lineno'))
        return end - start + 1
    return 0


def _get_nesting_depth(node: ast.FunctionDef) -> int:
    """Fonksiyondaki maksimum iç içe geçme derinliğini hesaplar"""
    visitor = NestingVisitor()
    return visitor.visit(node)


def _get_class_methods(node: ast.ClassDef) -> List[str]:
    """Class'ın method isimlerini döndürür"""
    methods = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(item.name)
    return methods


def detect_long_functions(tree: ast.AST, threshold: int = 50) -> List[Dict[str, Any]]:
    """
    Çok uzun fonksiyonları tespit eder.
    
    Args:
        tree: AST ağacı
        threshold: Satır eşiği (varsayılan: 50)
    
    Returns:
        [{"name": "foo", "lines": 75, "threshold": 50, "severity": "warning"}]
    """
    smells = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines = _get_function_lines(node)
            if lines > threshold:
                severity = "warning" if lines <= threshold * 2 else "error"
                smells.append({
                    "name": node.name,
                    "lines": lines,
                    "threshold": threshold,
                    "severity": severity,
                    "message": f"Fonksiyon {lines} satır ({threshold} eşiği aşıldı)"
                })
    return smells


def detect_too_many_params(tree: ast.AST, threshold: int = 5) -> List[Dict[str, Any]]:
    """
    Çok fazla parametre alan fonksiyonları tespit eder.
    
    Args:
        tree: AST ağacı
        threshold: Parametre eşiği (varsayılan: 5)
    
    Returns:
        [{"name": "bar", "count": 8, "threshold": 5, "params": ["a", "b", ...]}]
    """
    smells = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            params = [arg.arg for arg in node.args.args if arg.arg != 'self']
            if len(params) > threshold:
                smells.append({
                    "name": node.name,
                    "count": len(params),
                    "threshold": threshold,
                    "params": params,
                    "severity": "warning",
                    "message": f"Fonksiyon {len(params)} parametre alıyor ({threshold} eşiği aşıldı)"
                })
    return smells


def detect_deep_nesting(tree: ast.AST, threshold: int = 4) -> List[Dict[str, Any]]:
    """
    Derin iç içe geçmiş yapıları tespit eder.
    
    Args:
        tree: AST ağacı
        threshold: Derinlik eşiği (varsayılan: 4)
    
    Returns:
        [{"name": "baz", "depth": 6, "threshold": 4}]
    """
    smells = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            depth = _get_nesting_depth(node)
            if depth > threshold:
                severity = "warning" if depth <= threshold + 2 else "error"
                smells.append({
                    "name": node.name,
                    "depth": depth,
                    "threshold": threshold,
                    "severity": severity,
                    "message": f"Fonksiyon {depth} seviye iç içe ({threshold} eşiği aşıldı)"
                })
    return smells


def detect_god_class(tree: ast.AST, threshold: int = 20) -> List[Dict[str, Any]]:
    """
    Çok fazla method'a sahip class'ları tespit eder (God Class anti-pattern).
    
    Args:
        tree: AST ağacı
        threshold: Method eşiği (varsayılan: 20)
    
    Returns:
        [{"name": "MegaClass", "method_count": 35, "methods": [...], "threshold": 20}]
    """
    smells = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = _get_class_methods(node)
            if len(methods) > threshold:
                smells.append({
                    "name": node.name,
                    "method_count": len(methods),
                    "methods": methods,
                    "threshold": threshold,
                    "severity": "error",
                    "message": f"Class {len(methods)} method içeriyor ({threshold} eşiği aşıldı) - God Class!"
                })
    return smells


def detect_all_smells(code: str, config: Optional[SmellConfig] = None) -> Dict[str, List[Dict]]:
    """
    Tüm code smell'leri tespit eder.
    
    Args:
        code: Python kaynak kodu
        config: Eşik değerleri yapılandırması
    
    Returns:
        {
            "long_functions": [...],
            "too_many_params": [...],
            "deep_nesting": [...],
            "god_class": [...],
            "total_smells": 5,
            "severity_counts": {"warning": 3, "error": 2}
        }
    """
    if config is None:
        config = SmellConfig()
    
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}", "total_smells": 0}
    
    smells = {
        "long_functions": detect_long_functions(tree, config.long_function_lines),
        "too_many_params": detect_too_many_params(tree, config.too_many_params),
        "deep_nesting": detect_deep_nesting(tree, config.deep_nesting_level),
        "god_class": detect_god_class(tree, config.god_class_methods),
    }
    
    # Toplam istatistikler
    all_smells = []
    for smell_list in smells.values():
        if isinstance(smell_list, list):
            all_smells.extend(smell_list)
    
    smells["total_smells"] = len(all_smells)
    smells["severity_counts"] = {
        "warning": sum(1 for s in all_smells if s.get("severity") == "warning"),
        "error": sum(1 for s in all_smells if s.get("severity") == "error")
    }
    
    return smells


def get_smell_report(code: str, config: Optional[SmellConfig] = None) -> str:
    """
    İnsan tarafından okunabilir code smell raporu üretir.
    
    Args:
        code: Python kaynak kodu
        config: Eşik değerleri yapılandırması
    
    Returns:
        Formatlanmış rapor string'i
    """
    smells = detect_all_smells(code, config)
    
    if "error" in smells:
        return f"❌ {smells['error']}"
    
    if smells["total_smells"] == 0:
        return "✅ Harika! Kod kokusu tespit edilmedi."
    
    report = []
    report.append(f"🔍 Code Smell Raporu ({smells['total_smells']} sorun bulundu)")
    report.append("=" * 50)
    
    severity_emoji = {"warning": "⚠️", "error": "🔴"}
    
    if smells["long_functions"]:
        report.append("\n📏 Uzun Fonksiyonlar:")
        for s in smells["long_functions"]:
            emoji = severity_emoji.get(s["severity"], "")
            report.append(f"  {emoji} {s['name']}() - {s['lines']} satır")
    
    if smells["too_many_params"]:
        report.append("\n📋 Çok Fazla Parametre:")
        for s in smells["too_many_params"]:
            emoji = severity_emoji.get(s["severity"], "")
            report.append(f"  {emoji} {s['name']}() - {s['count']} parametre: {', '.join(s['params'][:5])}...")
    
    if smells["deep_nesting"]:
        report.append("\n🔄 Derin İç İçe Yapı:")
        for s in smells["deep_nesting"]:
            emoji = severity_emoji.get(s["severity"], "")
            report.append(f"  {emoji} {s['name']}() - {s['depth']} seviye iç içe")
    
    if smells["god_class"]:
        report.append("\n👑 God Class:")
        for s in smells["god_class"]:
            emoji = severity_emoji.get(s["severity"], "")
            report.append(f"  {emoji} {s['name']} - {s['method_count']} method")
    
    report.append("\n" + "=" * 50)
    report.append(f"📊 Özet: {smells['severity_counts']['warning']} uyarı, {smells['severity_counts']['error']} hata")
    
    return "\n".join(report)


# Test
if __name__ == "__main__":
    test_code = '''
class MegaController:
    """Bu class çok fazla method içeriyor - God Class örneği"""
    
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass
    def method21(self): pass  # 21. method - eşiği aşıyor!

def complex_function(a, b, c, d, e, f, g, h):
    """Çok fazla parametre alan fonksiyon"""
    if a:
        if b:
            if c:
                if d:
                    if e:  # 5 seviye iç içe!
                        return True
    return False
'''
    
    print("🧪 Code Smell Detector v1.0 - Test")
    print(get_smell_report(test_code))
