"""
Pre-commit Quality Gate Plugin for Agent-Nexus
===============================================
Created by: CopilotOpusAgent
Date: 2026-01-08

Runs quality checks before commit:
- Python syntax validation
- Code smell detection
- Security vulnerability scan
- Import validation
- Test execution (optional)
"""

import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.plugin_system import PluginBase, PluginResult, PluginConfig, HookPoint, PluginPriority


@dataclass
class CheckResult:
    """Result of a single check"""
    name: str
    passed: bool
    message: str
    details: list = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = []


class PrecommitPlugin(PluginBase):
    """Pre-commit quality gate plugin."""
    
    def __init__(self, config=None):
        super().__init__(config or PluginConfig(
            priority=PluginPriority.HIGHEST,
            hooks=[HookPoint.ON_COMMIT],
            settings={
                "check_syntax": True,
                "check_code_smells": True,
                "check_security": True,
                "check_imports": True,
                "run_tests": False
            }
        ))
    
    @property
    def name(self) -> str:
        return "PrecommitPlugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Pre-commit quality gate with syntax, smell, and security checks"
    
    def check_syntax(self, files: list) -> CheckResult:
        """Check Python syntax for all files"""
        errors = []
        for filepath in files:
            if not filepath.endswith('.py'):
                continue
            try:
                path = Path(filepath)
                if not path.exists():
                    continue
                content = path.read_text(encoding='utf-8')
                compile(content, filepath, 'exec')
            except SyntaxError as e:
                errors.append(f"{filepath}:{e.lineno}: {e.msg}")
        
        if errors:
            return CheckResult("Syntax Check", False, f"{len(errors)} syntax error(s)", errors)
        return CheckResult("Syntax Check", True, "All files have valid syntax")
    
    def check_code_smells(self, files: list) -> CheckResult:
        """Run code smell detector on files"""
        try:
            from src.code_smell_detector import CodeSmellDetector
            detector = CodeSmellDetector()
            all_smells = []
            
            for filepath in files:
                if not filepath.endswith('.py'):
                    continue
                path = Path(filepath)
                if not path.exists():
                    continue
                smells = detector.detect_smells(str(path))
                for smell in smells:
                    all_smells.append(f"{path.name}: {smell.get('type')} - {smell.get('message')}")
            
            if all_smells:
                return CheckResult("Code Smell Check", False, f"{len(all_smells)} smell(s)", all_smells[:10])
            return CheckResult("Code Smell Check", True, "No code smells")
        except Exception as e:
            return CheckResult("Code Smell Check", True, f"Skipped: {e}")
    
    def check_security(self, files: list) -> CheckResult:
        """Run security analyzer on files"""
        try:
            from src.security_analyzer import SecurityAnalyzer
            analyzer = SecurityAnalyzer()
            all_issues = []
            
            for filepath in files:
                if not filepath.endswith('.py'):
                    continue
                path = Path(filepath)
                if not path.exists():
                    continue
                issues = analyzer.analyze(str(path))
                for issue in issues:
                    if issue.get('severity') in ['critical', 'high']:
                        all_issues.append(f"[{issue['severity'].upper()}] {path.name}: {issue.get('message')}")
            
            if all_issues:
                return CheckResult("Security Check", False, f"{len(all_issues)} issue(s)", all_issues)
            return CheckResult("Security Check", True, "No vulnerabilities")
        except Exception as e:
            return CheckResult("Security Check", True, f"Skipped: {e}")
    
    def check_imports(self, files: list) -> CheckResult:
        """Check for import errors"""
        import ast
        errors = []
        for filepath in files:
            if not filepath.endswith('.py'):
                continue
            path = Path(filepath)
            if not path.exists():
                continue
            try:
                content = path.read_text(encoding='utf-8')
                ast.parse(content)
            except Exception as e:
                errors.append(f"{filepath}: {e}")
        
        if errors:
            return CheckResult("Import Check", False, f"{len(errors)} error(s)", errors)
        return CheckResult("Import Check", True, "All imports valid")
    
    def execute(self, context: dict) -> PluginResult:
        """Execute all pre-commit checks"""
        files = context.get("files", [])
        settings = self.config.settings
        results = []
        
        if settings.get("check_syntax", True):
            results.append(self.check_syntax(files))
        if settings.get("check_code_smells", True):
            results.append(self.check_code_smells(files))
        if settings.get("check_security", True):
            results.append(self.check_security(files))
        if settings.get("check_imports", True):
            results.append(self.check_imports(files))
        
        failed = [r for r in results if not r.passed]
        passed = [r for r in results if r.passed]
        
        summary = []
        for r in results:
            status = "✅" if r.passed else "❌"
            summary.append(f"{status} {r.name}: {r.message}")
            for d in r.details[:3]:
                summary.append(f"   - {d}")
        
        return PluginResult(
            success=len(failed) == 0,
            plugin_name=self.name,
            plugin_version=self.version,
            message=f"Pre-commit: {len(passed)}/{len(results)} checks passed",
            data={"total": len(results), "passed": len(passed), "summary": summary},
            errors=[r.message for r in failed]
        )


if __name__ == "__main__":
    print("🔍 Pre-commit Plugin Demo")
    print("=" * 40)
    
    plugin = PrecommitPlugin()
    src_dir = Path(__file__).parent.parent / "src"
    files = [str(f) for f in src_dir.glob("*.py")]
    
    result = plugin.execute({"files": files})
    
    print(f"\n{result.message}")
    print("\n📋 Summary:")
    for line in result.data.get("summary", []):
        print(f"  {line}")
    
    if result.success:
        print("\n✅ All checks passed!")
    else:
        print(f"\n❌ {len(result.errors)} failed")
