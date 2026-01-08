#!/usr/bin/env python3
"""
Test runner with coverage reporting for Agent Nexus
Runs all tests and generates coverage reports
"""

import subprocess
import sys
import os

def run_tests_with_coverage():
    """Run all tests with coverage and generate reports"""
    
    print("🧪 Running tests with coverage analysis...\n")
    
    # Run pytest with coverage
    cmd = [
        "pytest",
        "src/test_code_smell_detector.py",
        "src/test_security_analyzer.py",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html",
        "--cov-report=xml",
        "--cov-fail-under=80",
        "-v"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        
        print("\n" + "="*60)
        if result.returncode == 0:
            print("✅ ALL TESTS PASSED WITH SUFFICIENT COVERAGE!")
            print("="*60)
            print("\n📊 Coverage reports generated:")
            print("  - Terminal: See above")
            print("  - HTML: htmlcov/index.html")
            print("  - XML: coverage.xml (for badges)")
            print("\n💡 Open HTML report: python3 -m http.server 8000 --directory htmlcov")
            return 0
        else:
            print("❌ TESTS FAILED OR COVERAGE BELOW 80%")
            print("="*60)
            return 1
            
    except FileNotFoundError:
        print("❌ pytest not found! Install with: pip install pytest pytest-cov")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests_with_coverage())
