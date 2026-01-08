"""
Test suite for Code Smell Detector v1.0
==========================================
Code smell detector modülünü test eden kapsamlı test suite.

Test edilen özellikler:
- Long Function detection (>50 satır)
- Too Many Parameters (>5 parametre)
- Deep Nesting (>4 seviye)
- God Class (>20 method)
- Custom configuration
- Report generation

Katkıda Bulunanlar:
- NexusPilotAgent (v1.0): Test suite implementasyonu
"""

import ast
from code_smell_detector import (
    detect_long_functions,
    detect_too_many_params,
    detect_deep_nesting,
    detect_god_class,
    detect_all_smells,
    get_smell_report,
    SmellConfig
)


def test_long_function_detection():
    """Long function tespiti - 50+ satır"""
    code = '''
def long_function():
    """ This is a very long function """
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    f = 9
    g = 10
    h = 11
    i = 12
    j = 13
    k = 14
    l = 15
    m = 16
    n = 17
    o = 18
    p = 19
    q = 20
    r = 21
    s = 22
    t = 23
    u = 24
    v = 25
    w = 26
    x = 27
    y = 28
    z = 29
    aa = 30
    bb = 31
    cc = 32
    dd = 33
    ee = 34
    ff = 35
    gg = 36
    hh = 37
    ii = 38
    jj = 39
    kk = 40
    ll = 41
    mm = 42
    nn = 43
    oo = 44
    pp = 45
    qq = 46
    rr = 47
    ss = 48
    tt = 49
    return "done"
'''
    tree = ast.parse(code)
    smells = detect_long_functions(tree)
    
    assert len(smells) == 1, "Bir long function bulunmalı"
    assert smells[0]['name'] == 'long_function', "Fonksiyon adı doğru olmalı"
    assert smells[0]['lines'] > 50, "50+ satır olmalı"
    print(f"✅ Long function detected: {smells[0]['name']} - {smells[0]['lines']} lines")


def test_too_many_parameters():
    """Too many parameters tespiti - 5+ parametre"""
    code = '''
def complex_function(a, b, c, d, e, f, g, h):
    """Function with 8 parameters"""
    return a + b + c + d + e + f + g + h

def simple_function(x, y):
    """Function with 2 parameters"""
    return x + y
'''
    tree = ast.parse(code)
    smells = detect_too_many_params(tree, threshold=5)
    
    assert len(smells) == 1, "Bir complex function bulunmalı"
    assert smells[0]['name'] == 'complex_function', "Fonksiyon adı doğru olmalı"
    assert smells[0]['count'] == 8, "8 parametre olmalı"
    assert 'a' in smells[0]['params'], "Parametre listesi doğru olmalı"
    print(f"✅ Too many params detected: {smells[0]['name']} - {smells[0]['count']} params")


def test_deep_nesting_detection():
    """Deep nesting tespiti - 4+ seviye"""
    code = '''
def deeply_nested():
    if True:  # level 1
        for i in range(10):  # level 2
            while True:  # level 3
                try:  # level 4
                    with open("file") as f:  # level 5
                        if True:  # level 6
                            print("deep!")
                except:
                    pass
'''
    tree = ast.parse(code)
    smells = detect_deep_nesting(tree, threshold=4)
    
    assert len(smells) == 1, "Bir deeply nested function bulunmalı"
    assert smells[0]['name'] == 'deeply_nested', "Fonksiyon adı doğru olmalı"
    assert smells[0]['depth'] >= 5, "5+ seviye nesting olmalı"
    print(f"✅ Deep nesting detected: {smells[0]['name']} - {smells[0]['depth']} levels")


def test_god_class_detection():
    """God class tespiti - 20+ method"""
    code = '''
class MegaController:
    """A god class with many methods"""
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
    def method21(self): pass
    def method22(self): pass

class SmallClass:
    """A small class"""
    def method1(self): pass
    def method2(self): pass
'''
    tree = ast.parse(code)
    smells = detect_god_class(tree, threshold=20)
    
    assert len(smells) == 1, "Bir god class bulunmalı"
    assert smells[0]['name'] == 'MegaController', "Class adı doğru olmalı"
    assert smells[0]['method_count'] == 22, "22 method olmalı"
    print(f"✅ God class detected: {smells[0]['name']} - {smells[0]['method_count']} methods")


def test_smell_config_customization():
    """Custom configuration testi"""
    code = '''
def medium_function(a, b, c):
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    c = 6
    d = 7
    e = 8
    return x + y
'''
    tree = ast.parse(code)
    
    # Varsayılan config - 50+ satır
    smells_default = detect_long_functions(tree, threshold=50)
    assert len(smells_default) == 0, "Varsayılan config'de smell yok"
    
    # Custom config - 5+ satır
    smells_custom = detect_long_functions(tree, threshold=5)
    assert len(smells_custom) == 1, "Custom config'de smell bulunmalı"
    
    print(f"✅ Config customization works: default={len(smells_default)}, custom={len(smells_custom)}")


def test_get_smell_report():
    """Rapor üretimi testi"""
    code = '''
def complex_function(a, b, c, d, e, f, g, h):
    if True:
        for i in range(10):
            while True:
                try:
                    with open("file") as f:
                        if True:
                            print("deep!")
                except:
                    pass
    return a + b

class GodClass:
    def m1(self): pass
    def m2(self): pass
    def m3(self): pass
    def m4(self): pass
    def m5(self): pass
    def m6(self): pass
    def m7(self): pass
    def m8(self): pass
    def m9(self): pass
    def m10(self): pass
    def m11(self): pass
    def m12(self): pass
    def m13(self): pass
    def m14(self): pass
    def m15(self): pass
    def m16(self): pass
    def m17(self): pass
    def m18(self): pass
    def m19(self): pass
    def m20(self): pass
    def m21(self): pass
'''
    all_smells = detect_all_smells(code)
    report = get_smell_report(code)  # Pass code string, not all_smells dict
    
    assert "Code Smell Raporu" in report or "Raporu" in report or "sorun" in report, "Rapor içeriği olmalı"
    assert "parametre" in report.lower() or "complex_function" in report, "Parametre uyarısı olmalı"
    assert "god class" in report.lower() or "godclass" in report or "21 method" in report, "God class uyarısı olmalı"
    assert "iç içe" in report.lower() or "nesting" in report.lower(), "Nesting uyarısı olmalı"
    
    print(f"✅ Report generated successfully")
    print("\n" + "="*50)
    print(report)
    print("="*50)


def run_all_tests():
    """Tüm testleri çalıştır"""
    print("🧪 Code Smell Detector Test Suite v1.0\n")
    
    try:
        test_long_function_detection()
        test_too_many_parameters()
        test_deep_nesting_detection()
        test_god_class_detection()
        test_smell_config_customization()
        test_get_smell_report()
        
        print("\n" + "="*50)
        print("✅ TÜM TESTLER BAŞARILI! 6/6 passed")
        print("="*50)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST BAŞARISIZ: {e}")
        return False
    except Exception as e:
        print(f"\n💥 HATA: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
