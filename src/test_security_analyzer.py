"""
Test suite for Security Analyzer v1.0
=======================================
Security analyzer modülünü test eden kapsamlı test suite.

Test edilen özellikler:
- eval/exec/compile detection
- pickle.loads detection
- os.system/subprocess detection
- shell=True injection detection
- Hardcoded secrets detection
- Report generation

Katkıda Bulunanlar:
- NexusPilotAgent (v1.0): Test suite implementasyonu
"""

import ast
from security_analyzer import (
    analyze_security,
    get_security_report,
    SecurityConfig
)


def test_eval_exec_detection():
    """eval/exec/compile tespiti"""
    code = '''
def dangerous_code():
    user_input = input("Enter code: ")
    result = eval(user_input)  # CRITICAL: eval usage
    exec("print('hello')")     # CRITICAL: exec usage
    compiled = compile("x=1", "<string>", "exec")  # CRITICAL: compile
    return result

def safe_code():
    x = 1 + 2
    return x
'''
    result = analyze_security(code)
    dangerous = result['dangerous_functions']
    
    assert len(dangerous) >= 3, "En az 3 dangerous function bulunmalı"
    
    # eval tespiti
    eval_issues = [i for i in dangerous if i['function'] == 'eval']
    assert len(eval_issues) == 1, "eval bulunmalı"
    assert eval_issues[0]['severity'] == 'critical', "eval critical olmalı"
    
    # exec tespiti
    exec_issues = [i for i in dangerous if i['function'] == 'exec']
    assert len(exec_issues) == 1, "exec bulunmalı"
    
    # compile tespiti
    compile_issues = [i for i in dangerous if i['function'] == 'compile']
    assert len(compile_issues) == 1, "compile bulunmalı"
    
    print(f"✅ Dangerous functions detected: {len(dangerous)} issues (eval, exec, compile)")


def test_pickle_detection():
    """pickle.loads tespiti"""
    code = '''
import pickle

def deserialize_data(data):
    obj = pickle.loads(data)  # HIGH: deserialization attack
    return obj

def safe_serialize():
    import json
    data = json.loads('{"key": "value"}')
    return data
'''
    result = analyze_security(code)
    risky = result['risky_calls']
    
    pickle_issues = [i for i in risky if 'pickle' in i.get('module', '').lower() or 'loads' in i.get('function', '')]
    assert len(pickle_issues) >= 1, "pickle.loads bulunmalı"
    
    print(f"✅ Pickle.loads detected: {len(pickle_issues)} issue(s)")


def test_os_system_detection():
    """os.system/subprocess detection"""
    code = '''
import os
import subprocess

def run_command(cmd):
    os.system(cmd)  # HIGH: command injection risk
    subprocess.call(cmd)  # HIGH: risky subprocess
    return True

def safe_command():
    import json
    return json.dumps({})
'''
    result = analyze_security(code)
    
    # Risky imports
    risky_imports = result['risky_imports']
    assert len(risky_imports) >= 1, "Risky import bulunmalı (subprocess)"
    
    # Dangerous/risky function calls
    risky_calls = result['risky_calls']
    os_issues = [i for i in risky_calls if 'system' in i.get('function', '').lower() or 'call' in i.get('function', '').lower()]
    assert len(os_issues) >= 1, "os.system veya subprocess.call bulunmalı"
    
    print(f"✅ OS command issues detected: {len(risky_imports)} risky imports, {len(os_issues)} dangerous calls")


def test_shell_injection_detection():
    """shell=True injection tespiti"""
    code = '''
import subprocess

def vulnerable_command(user_input):
    # CRITICAL: shell injection vulnerability
    subprocess.call(user_input, shell=True)
    subprocess.Popen(user_input, shell=True)
    return True

def safe_command():
    # Safe: shell=False (default)
    subprocess.call(["ls", "-la"])
    return True
'''
    result = analyze_security(code)
    issues = result['shell_injection']
    
    assert len(issues) >= 2, "En az 2 shell=True kullanımı bulunmalı"
    assert all(i['severity'] == 'critical' for i in issues), "Shell injection critical olmalı"
    
    print(f"✅ Shell injection detected: {len(issues)} vulnerabilities")


def test_hardcoded_secrets_detection():
    """Hardcoded secrets tespiti"""
    code = '''
# CRITICAL: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"
PASSWORD = "mysecretpassword123"
SECRET_TOKEN = "ghp_abcdefghijklmnop"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# Safe variables
MAX_RETRIES = 3
DEBUG = True
USERNAME = "admin"  # Not a secret
'''
    result = analyze_security(code)
    issues = result['hardcoded_secrets']
    
    assert len(issues) >= 3, "En az 3 hardcoded secret bulunmalı"
    
    # API_KEY tespiti
    api_key_issues = [i for i in issues if 'API_KEY' in i.get('variable', '')]
    assert len(api_key_issues) >= 1, "API_KEY bulunmalı"
    
    # PASSWORD tespiti
    password_issues = [i for i in issues if 'PASSWORD' in i.get('variable', '')]
    assert len(password_issues) >= 1, "PASSWORD bulunmalı"
    
    # TOKEN tespiti
    token_issues = [i for i in issues if 'TOKEN' in i.get('variable', '')]
    assert len(token_issues) >= 1, "TOKEN bulunmalı"
    
    print(f"✅ Hardcoded secrets detected: {len(issues)} secrets (API_KEY, PASSWORD, TOKEN, etc.)")


def test_comprehensive_security_scan():
    """Kapsamlı güvenlik taraması"""
    code = '''
import pickle
import subprocess
import os

API_KEY = "secret-key-12345"
DATABASE_PASSWORD = "db_pass_secret"

def process_user_data(user_input, serialized_data):
    # Multiple security issues in one function
    
    # 1. Hardcoded secret usage
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    # 2. Dangerous deserialization
    obj = pickle.loads(serialized_data)
    
    # 3. Code execution
    result = eval(user_input)
    
    # 4. Command injection
    os.system(f"echo {user_input}")
    
    # 5. Shell injection
    subprocess.call(user_input, shell=True)
    
    return result
'''
    result = analyze_security(code)
    
    assert 'dangerous_functions' in result, "Dangerous functions kategorisi olmalı"
    assert 'risky_imports' in result, "Risky imports kategorisi olmalı"
    assert 'shell_injection' in result, "Shell injection kategorisi olmalı"
    assert 'hardcoded_secrets' in result, "Hardcoded secrets kategorisi olmalı"
    
    # Her kategoride sorun olmalı
    assert len(result['dangerous_functions']) >= 1, "1+ dangerous function olmalı (eval)"
    assert len(result['risky_imports']) >= 1, "1+ risky import olmalı"
    assert len(result['shell_injection']) >= 1, "1+ shell injection olmalı"
    assert len(result['hardcoded_secrets']) >= 2, "2+ hardcoded secret olmalı"
    
    # Toplam sorun sayısı
    total = result['total_issues']
    print(f"✅ Comprehensive scan: {total} total security issues found")


def test_get_security_report():
    """Güvenlik raporu üretimi testi"""
    code = '''
import pickle
import subprocess

API_KEY = "sk-secret123"

def vulnerable_function(data, cmd):
    obj = pickle.loads(data)
    result = eval("1+1")
    subprocess.call(cmd, shell=True)
    os.system("ls")
    return obj
'''
    report = get_security_report(code)
    
    assert "Güvenlik" in report or "Security" in report or "sorun" in report, "Rapor içeriği olmalı"
    assert "Özet" in report or "özet" in report or "tespit" in report, "Rapor bilgisi olmalı"
    
    print(f"✅ Security report generated successfully")
    print("\n" + "="*50)
    print(report)
    print("="*50)


def run_all_tests():
    """Tüm testleri çalıştır"""
    print("🔒 Security Analyzer Test Suite v1.0\n")
    
    try:
        test_eval_exec_detection()
        test_pickle_detection()
        test_os_system_detection()
        test_shell_injection_detection()
        test_hardcoded_secrets_detection()
        test_comprehensive_security_scan()
        test_get_security_report()
        
        print("\n" + "="*50)
        print("✅ TÜM TESTLER BAŞARILI! 7/7 passed")
        print("="*50)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST BAŞARISIZ: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n💥 HATA: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
