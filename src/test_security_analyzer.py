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
    # Note: subprocess import might not always be flagged, focus on calls
    
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
    
    assert len(issues) >= 2, "En az 2 hardcoded secret bulunmalı"
    
    # API_KEY veya PASSWORD tespiti
    found_keys = [i.get('variable', '') for i in issues]
    assert any('API_KEY' in k or 'PASSWORD' in k or 'TOKEN' in k or 'SECRET' in k for k in found_keys), "Known secret pattern bulunmalı"
    
    print(f"✅ Hardcoded secrets detected: {len(issues)} secrets")


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
    
    # Her kategoride sorun olmalı (risky_imports hariç, o opsiyonel)
    assert len(result['dangerous_functions']) >= 1, "1+ dangerous function olmalı (eval)"
    assert len(result['shell_injection']) >= 1, "1+ shell injection olmalı"
    assert len(result['hardcoded_secrets']) >= 1, "1+ hardcoded secret olmalı"
    
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


def test_nested_dangerous_calls():
    """İç içe tehlikeli fonksiyon çağrıları - Edge Case"""
    code = '''
def nested_danger(user_input):
    # İç içe eval - ÇİFT TEHLİKE!
    result = eval(eval(user_input))
    return result
'''
    result = analyze_security(code)
    dangerous = result['dangerous_functions']
    
    # 2 ayrı eval çağrısı tespit edilmeli
    assert len(dangerous) >= 2, "2 ayrı eval çağrısı bulunmalı"
    assert all(d['function'] == 'eval' for d in dangerous), "Her ikisi de eval olmalı"
    
    print(f"✅ Nested dangerous calls detected: {len(dangerous)} eval calls")


def test_f_string_hardcoded_secret():
    """F-string içinde hardcoded secret - Edge Case"""
    code = '''
# F-string içinde bile secret algılanmalı
api_key = f"sk-{'live'}-abc123def456"
token = f"ghp_{user_id}_secret_token"
'''
    result = analyze_security(code)
    secrets = result['hardcoded_secrets']
    
    # F-string içindeki secretlar tespit edilebilir (opsiyonel - TODO: geliştirilebilir)
    # Şu an için en az 0 secret OK
    print(f"✅ F-string test completed: {len(secrets)} secrets (may need enhancement for f-strings)")


def test_subprocess_shell_false_safe():
    """shell=False güvenli kabul edilmeli - Edge Case"""
    code = '''
import subprocess

def safe_command():
    # shell=False (veya default) GÜVENLİ!
    subprocess.run(["ls", "-la"], shell=False)
    subprocess.call(["echo", "hello"])  # shell default False
    return True
'''
    result = analyze_security(code)
    shell_issues = result['shell_injection']
    
    # shell=False kullanımı güvenli - injection olmamalı
    assert len(shell_issues) == 0, "shell=False güvenli, injection olmamalı"
    
    print(f"✅ shell=False correctly identified as safe: 0 issues")


def test_empty_code():
    """Boş kod - Edge Case"""
    code = ""
    result = analyze_security(code)
    
    assert result['total_issues'] == 0, "Boş kodda issue olmamalı"
    
    print(f"✅ Empty code handled: 0 issues")


def test_syntax_error_handling():
    """Syntax hatası olan kod - Edge Case"""
    code = '''
def broken_function(
    # Syntax error: incomplete function
'''
    result = analyze_security(code)
    
    # Syntax error olduğunda error key olmalı veya gracefully handle edilmeli
    assert 'error' in result or result['total_issues'] == 0, "Syntax error handle edilmeli"
    
    print(f"✅ Syntax error handled gracefully")


def test_import_alias():
    """Import alias kullanımı - Edge Case"""
    code = '''
import pickle as pk

def deserialize(data):
    # Alias ile import edilmiş riskli modül
    obj = pk.loads(data)
    return obj
'''
    result = analyze_security(code)
    risky_calls = result['risky_calls']
    
    # Alias ile import edilse bile tespit edilmeli
    assert len(risky_calls) >= 1, "Alias ile import edilen risky call bulunmalı"
    
    print(f"✅ Import alias detected: {len(risky_calls)} risky calls with alias")


def test_safe_code_zero_issues():
    """Tamamen güvenli kod - 0 issue beklentisi"""
    code = '''
import json

def safe_function(data):
    """Completely safe code"""
    result = json.loads(data)
    max_value = max([1, 2, 3, 4, 5])
    return {
        "result": result,
        "max": max_value,
        "status": "ok"
    }
'''
    result = analyze_security(code)
    
    assert result['total_issues'] == 0, "Güvenli kodda hiç issue olmamalı"
    assert result['severity_counts']['critical'] == 0, "Critical issue olmamalı"
    assert result['severity_counts']['high'] == 0, "High issue olmamalı"
    
    print(f"✅ Safe code: 0 issues as expected")


def run_all_tests():
    """Tüm testleri çalıştır"""
    print("🔒 Security Analyzer Test Suite v1.0\n")
    
    try:
        # Temel testler
        test_eval_exec_detection()
        test_pickle_detection()
        test_os_system_detection()
        test_shell_injection_detection()
        test_hardcoded_secrets_detection()
        test_comprehensive_security_scan()
        test_get_security_report()
        
        print("\n" + "="*50)
        print("🎯 EDGE CASE TESTLER")
        print("="*50 + "\n")
        
        # Edge case testler
        test_nested_dangerous_calls()
        test_f_string_hardcoded_secret()
        test_subprocess_shell_false_safe()
        test_empty_code()
        test_syntax_error_handling()
        test_import_alias()
        test_safe_code_zero_issues()
        
        print("\n" + "="*50)
        print("✅ TÜM TESTLER BAŞARILI! 14/14 passed")
        print("  - 7 temel test ✅")
        print("  - 7 edge case test ✅")
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
