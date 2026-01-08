"""
Code Metrics Plugin for Agent-Nexus
====================================
Created by: CopilotOpusAgent
Date: 2026-01-08

Calculates code metrics for Python files:
- Lines of Code (LOC)
- Cyclomatic Complexity (simplified)
- Function/Class count
- Import count
- Docstring coverage
"""

import ast
from pathlib import Path
from dataclasses import dataclass, field
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.plugin_system import PluginBase, PluginResult, PluginConfig, HookPoint


@dataclass
class FileMetrics:
    """Metrics for a single file"""
    filepath: str
    lines_of_code: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    docstring_count: int = 0
    avg_function_length: float = 0.0
    complexity_score: int = 0  # Simplified cyclomatic
    
    @property
    def total_lines(self) -> int:
        return self.lines_of_code + self.blank_lines + self.comment_lines
    
    @property
    def docstring_coverage(self) -> float:
        """Percentage of functions/classes with docstrings"""
        total = self.function_count + self.class_count
        if total == 0:
            return 100.0
        return (self.docstring_count / total) * 100


class MetricsVisitor(ast.NodeVisitor):
    """AST visitor to collect code metrics"""
    
    def __init__(self):
        self.functions: list[tuple[str, int]] = []  # (name, line_count)
        self.classes: list[str] = []
        self.imports: int = 0
        self.docstrings: int = 0
        self.complexity: int = 1  # Base complexity
    
    def visit_FunctionDef(self, node):
        line_count = (node.end_lineno or node.lineno) - node.lineno + 1
        self.functions.append((node.name, line_count))
        
        # Check for docstring
        if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            self.docstrings += 1
        
        # Count complexity (if, for, while, except, with, and, or)
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, 
                                  ast.ExceptHandler, ast.With)):
                self.complexity += 1
            elif isinstance(child, ast.BoolOp):
                self.complexity += len(child.values) - 1
        
        self.generic_visit(node)
    
    visit_AsyncFunctionDef = visit_FunctionDef
    
    def visit_ClassDef(self, node):
        self.classes.append(node.name)
        
        # Check for docstring
        if (node.body and isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, ast.Constant) and
            isinstance(node.body[0].value.value, str)):
            self.docstrings += 1
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        self.imports += len(node.names)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        self.imports += len(node.names)
        self.generic_visit(node)


class CodeMetricsPlugin(PluginBase):
    """Plugin that calculates code metrics for Python files"""
    
    def __init__(self, config=None):
        super().__init__(config or PluginConfig(
            hooks=[HookPoint.POST_ANALYZE, HookPoint.ON_FILE_CHANGE]
        ))
    
    @property
    def name(self) -> str:
        return "CodeMetricsPlugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Calculates code metrics: LOC, complexity, docstring coverage"
    
    def analyze_file(self, filepath: str) -> FileMetrics:
        """Analyze a single file and return metrics"""
        metrics = FileMetrics(filepath=filepath)
        path = Path(filepath)
        
        if not path.exists() or path.suffix != '.py':
            return metrics
        
        try:
            content = path.read_text(encoding='utf-8')
            lines = content.split('\n')
            
            # Count lines
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    metrics.blank_lines += 1
                elif stripped.startswith('#'):
                    metrics.comment_lines += 1
                else:
                    metrics.lines_of_code += 1
            
            # Parse AST
            tree = ast.parse(content)
            visitor = MetricsVisitor()
            visitor.visit(tree)
            
            metrics.function_count = len(visitor.functions)
            metrics.class_count = len(visitor.classes)
            metrics.import_count = visitor.imports
            metrics.docstring_count = visitor.docstrings
            metrics.complexity_score = visitor.complexity
            
            if visitor.functions:
                total_lines = sum(lines for _, lines in visitor.functions)
                metrics.avg_function_length = total_lines / len(visitor.functions)
            
        except Exception as e:
            metrics.lines_of_code = -1  # Indicate error
        
        return metrics
    
    def execute(self, context: dict) -> PluginResult:
        """Execute metrics analysis on files in context"""
        files = context.get("files", [])
        
        all_metrics: list[dict] = []
        totals = {
            "total_files": 0,
            "total_loc": 0,
            "total_functions": 0,
            "total_classes": 0,
            "total_imports": 0,
            "avg_complexity": 0.0,
            "avg_docstring_coverage": 0.0
        }
        
        for filepath in files:
            if not filepath.endswith('.py'):
                continue
            
            metrics = self.analyze_file(filepath)
            
            if metrics.lines_of_code >= 0:  # No error
                totals["total_files"] += 1
                totals["total_loc"] += metrics.lines_of_code
                totals["total_functions"] += metrics.function_count
                totals["total_classes"] += metrics.class_count
                totals["total_imports"] += metrics.import_count
                totals["avg_complexity"] += metrics.complexity_score
                totals["avg_docstring_coverage"] += metrics.docstring_coverage
                
                all_metrics.append({
                    "file": filepath,
                    "loc": metrics.lines_of_code,
                    "functions": metrics.function_count,
                    "classes": metrics.class_count,
                    "complexity": metrics.complexity_score,
                    "docstring_coverage": round(metrics.docstring_coverage, 1)
                })
        
        # Calculate averages
        if totals["total_files"] > 0:
            totals["avg_complexity"] = round(
                totals["avg_complexity"] / totals["total_files"], 2
            )
            totals["avg_docstring_coverage"] = round(
                totals["avg_docstring_coverage"] / totals["total_files"], 1
            )
        
        return PluginResult(
            success=True,
            plugin_name=self.name,
            plugin_version=self.version,
            message=f"Analyzed {totals['total_files']} files, "
                    f"{totals['total_loc']} LOC, "
                    f"avg complexity: {totals['avg_complexity']}",
            data={
                "totals": totals,
                "files": all_metrics
            }
        )


if __name__ == "__main__":
    # Demo
    print("📊 Code Metrics Plugin Demo")
    print("=" * 40)
    
    plugin = CodeMetricsPlugin()
    
    # Analyze src files
    src_dir = Path(__file__).parent.parent / "src"
    files = [str(f) for f in src_dir.glob("*.py")]
    
    result = plugin.execute({"files": files})
    
    print(f"\n✅ {result.message}")
    print(f"\n📈 Totals:")
    for key, value in result.data["totals"].items():
        print(f"  {key}: {value}")
    
    print(f"\n📁 Per-file metrics:")
    for fm in result.data["files"]:
        print(f"  {Path(fm['file']).name}:")
        print(f"    LOC: {fm['loc']}, Functions: {fm['functions']}, "
              f"Complexity: {fm['complexity']}, Docstrings: {fm['docstring_coverage']}%")
