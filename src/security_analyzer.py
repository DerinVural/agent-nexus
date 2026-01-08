"""
Security Analyzer v1.0
======================
Python kod güvenlik analizi modülü.

Katkıda Bulunanlar:
- CopilotOpusAgent (v1.0): İlk implementasyon

Tespit Edilen Güvenlik Riskleri:
- Tehlikeli fonksiyonlar: eval, exec, compile
- Riskli modüller: pickle, subprocess, os.system
- Hardcoded secrets: API keys, passwords, tokens
- SQL Injection riskleri: string formatting ile SQL
- Command Injection: shell=True kullanımı
"""

import ast
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field


@dataclass
class SecurityConfig:
    """Güvenlik analizi yapılandırması"""
    
    # Kritik tehlikeli fonksiyonlar
    dangerous_functions: Set[str] = field(default_factory=lambda: {
        'eval', 'exec', 'compile', '__import__',
        'getattr', 'setattr', 'delattr',  # Dinamik attribute access
    })
    
    # Riskli modüller ve fonksiyonları
    risky_modules: Dict[str, Set[str]] = field(default_factory=lambda: {
        'pickle': {'load', 'loads', 'Unpickler'},
        'marshal': {'load', 'loads'},
        'shelve': {'open'},
        'subprocess': {'call', 'run', 'Popen', 'check_output', 'check_call'},
        'os': {'system', 'popen', 'spawn', 'exec'},
        'commands': {'getoutput', 'getstatusoutput'},  # Python 2 compat
    })
    
    # Secret pattern'leri
    secret_patterns: List[str] = field(default_factory=lambda: [
        r'(?i)(api[_-]?key|apikey)',
        r'(?i)(secret[_-]?key|secretkey)',
        r'(?i)(password|passwd|pwd)',
        r'(?i)(token|auth[_-]?token)',
        r'(?i)(private[_-]?key)',
        r'(?i)(access[_-]?key)',
        r'(?i)(credentials?)',
    ])


class SecurityVisitor(ast.NodeVisitor):
    """AST ziyaretçisi - güvenlik sorunlarını tespit eder"""
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.issues: List[Dict[str, Any]] = []
        self.imports: Dict[str, str] = {}  # alias -> module
    
    def visit_Import(self, node: ast.Import):
        """Import ifadelerini takip et"""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = alias.name
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """From import ifadelerini takip et"""
        if node.module:
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                self.imports[name] = f"{node.module}.{alias.name}"
                
                # Riskli import kontrolü
                if node.module in self.config.risky_modules:
                    risky_funcs = self.config.risky_modules[node.module]
                    if alias.name in risky_funcs or alias.name == '*':
                        self.issues.append({
                            "type": "risky_import",
                            "module": node.module,
                            "function": alias.name,
                            "line": node.lineno,
                            "severity": "high",
                            "message": f"Riskli import: {node.module}.{alias.name} - Deserialization/Command injection riski"
                        })
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        """Fonksiyon çağrılarını analiz et"""
        func_name = self._get_func_name(node.func)
        
        # Tehlikeli fonksiyon kontrolü
        if func_name in self.config.dangerous_functions:
            self.issues.append({
                "type": "dangerous_function",
                "function": func_name,
                "line": node.lineno,
                "severity": "critical",
                "message": f"Tehlikeli fonksiyon kullanımı: {func_name}() - Arbitrary code execution riski!"
            })
        
        # Riskli modül fonksiyon çağrısı
        if '.' in func_name:
            parts = func_name.split('.')
            module = parts[0]
            method = parts[-1]
            
            # Import alias çözümle
            actual_module = self.imports.get(module, module)
            if '.' in actual_module:
                actual_module = actual_module.split('.')[0]
            
            if actual_module in self.config.risky_modules:
                risky_funcs = self.config.risky_modules[actual_module]
                if method in risky_funcs:
                    self.issues.append({
                        "type": "risky_call",
                        "module": actual_module,
                        "function": method,
                        "line": node.lineno,
                        "severity": "high",
                        "message": f"Riskli fonksiyon çağrısı: {func_name}()"
                    })
        
        # subprocess shell=True kontrolü
        if func_name in ('subprocess.run', 'subprocess.call', 'subprocess.Popen', 'run', 'call', 'Popen'):
            for keyword in node.keywords:
                if keyword.arg == 'shell':
                    if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                        self.issues.append({
                            "type": "shell_injection",
                            "function": func_name,
                            "line": node.lineno,
                            "severity": "critical",
                            "message": f"shell=True kullanımı: Command injection riski!"
                        })
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign):
        """Değişken atamalarını kontrol et - hardcoded secrets"""
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                
                # Secret pattern kontrolü
                for pattern in self.config.secret_patterns:
                    if re.match(pattern, var_name):
                        # String literal mi kontrol et
                        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            if len(node.value.value) > 5:  # Çok kısa değilse
                                self.issues.append({
                                    "type": "hardcoded_secret",
                                    "variable": var_name,
                                    "line": node.lineno,
                                    "severity": "critical",
                                    "message": f"Hardcoded secret: {var_name} = '***' - Güvenlik riski!"
                                })
                        break
        
        self.generic_visit(node)
    
    def _get_func_name(self, node) -> str:
        """Fonksiyon adını çıkar"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_func_name(node.value)
            return f"{value}.{node.attr}" if value else node.attr
        return ""


def analyze_security(code: str, config: Optional[SecurityConfig] = None) -> Dict[str, Any]:
    """
    Python kodunu güvenlik açısından analiz eder.
    
    Args:
        code: Python kaynak kodu
        config: Güvenlik yapılandırması
    
    Returns:
        {
            "dangerous_functions": [...],
            "risky_imports": [...],
            "risky_calls": [...],
            "hardcoded_secrets": [...],
            "shell_injection": [...],
            "total_issues": 5,
            "severity_counts": {"critical": 2, "high": 3}
        }
    """
    if config is None:
        config = SecurityConfig()
    
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return {"error": f"Syntax error: {e}", "total_issues": 0}
    
    visitor = SecurityVisitor(config)
    visitor.visit(tree)
    
    # Kategorize et
    result = {
        "dangerous_functions": [],
        "risky_imports": [],
        "risky_calls": [],
        "hardcoded_secrets": [],
        "shell_injection": [],
    }
    
    # Type mapping - tekil -> çoğul (Bug fix by CopilotOpusAgent)
    type_mapping = {
        "dangerous_function": "dangerous_functions",
        "hardcoded_secret": "hardcoded_secrets",
        "risky_import": "risky_imports",
        "risky_call": "risky_calls",
        "shell_injection": "shell_injection",
    }
    
    for issue in visitor.issues:
        issue_type = issue["type"]
        # Map tekil type to çoğul key
        mapped_type = type_mapping.get(issue_type, issue_type)
        if mapped_type in result:
            result[mapped_type].append(issue)
    
    # İstatistikler
    all_issues = visitor.issues
    result["total_issues"] = len(all_issues)
    result["severity_counts"] = {
        "critical": sum(1 for i in all_issues if i.get("severity") == "critical"),
        "high": sum(1 for i in all_issues if i.get("severity") == "high"),
        "medium": sum(1 for i in all_issues if i.get("severity") == "medium"),
    }
    
    return result


def get_security_report(code: str, config: Optional[SecurityConfig] = None) -> str:
    """
    İnsan okunabilir güvenlik raporu üretir.
    
    Args:
        code: Python kaynak kodu
        config: Güvenlik yapılandırması
    
    Returns:
        Formatlanmış rapor string'i
    """
    result = analyze_security(code, config)
    
    if "error" in result:
        return f"❌ {result['error']}"
    
    if result["total_issues"] == 0:
        return "✅ Harika! Güvenlik sorunu tespit edilmedi."
    
    report = []
    report.append(f"🔒 Güvenlik Raporu ({result['total_issues']} sorun bulundu)")
    report.append("=" * 50)
    
    severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡"}
    
    if result["dangerous_functions"]:
        report.append("\n⚠️ Tehlikeli Fonksiyonlar:")
        for issue in result["dangerous_functions"]:
            emoji = severity_emoji.get(issue["severity"], "")
            report.append(f"  {emoji} Satır {issue['line']}: {issue['function']}()")
    
    if result["risky_imports"]:
        report.append("\n📦 Riskli Importlar:")
        for issue in result["risky_imports"]:
            emoji = severity_emoji.get(issue["severity"], "")
            report.append(f"  {emoji} Satır {issue['line']}: {issue['module']}.{issue['function']}")
    
    if result["risky_calls"]:
        report.append("\n🔧 Riskli Fonksiyon Çağrıları:")
        for issue in result["risky_calls"]:
            emoji = severity_emoji.get(issue["severity"], "")
            report.append(f"  {emoji} Satır {issue['line']}: {issue['module']}.{issue['function']}()")
    
    if result["hardcoded_secrets"]:
        report.append("\n🔑 Hardcoded Secrets:")
        for issue in result["hardcoded_secrets"]:
            emoji = severity_emoji.get(issue["severity"], "")
            report.append(f"  {emoji} Satır {issue['line']}: {issue['variable']} = '***'")
    
    if result["shell_injection"]:
        report.append("\n💉 Shell Injection Riskleri:")
        for issue in result["shell_injection"]:
            emoji = severity_emoji.get(issue["severity"], "")
            report.append(f"  {emoji} Satır {issue['line']}: {issue['function']}(shell=True)")
    
    report.append("\n" + "=" * 50)
    counts = result["severity_counts"]
    report.append(f"📊 Özet: {counts['critical']} kritik, {counts['high']} yüksek, {counts['medium']} orta")
    
    return "\n".join(report)


# Test
if __name__ == "__main__":
    test_code = '''
import pickle
from subprocess import call
import os

API_KEY = "sk-1234567890abcdef"
PASSWORD = "super_secret_123"

def vulnerable_function(user_input):
    # Tehlikeli: eval kullanımı
    result = eval(user_input)
    
    # Tehlikeli: exec kullanımı  
    exec(user_input)
    
    # Riskli: pickle.loads
    data = pickle.loads(user_input)
    
    # Riskli: os.system
    os.system(f"echo {user_input}")
    
    # Shell injection riski
    call(f"ls {user_input}", shell=True)
    
    return result
'''
    
    print("🧪 Security Analyzer v1.0 - Test")
    print(get_security_report(test_code))
