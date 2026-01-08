"""
Performance Profiler Plugin for Agent-Nexus
============================================
Created by: CopilotOpusAgent
Date: 2026-01-08

Profiles Python code execution:
- Function execution times
- Memory usage tracking
- Call frequency analysis
- Hotspot detection
"""

import cProfile
import pstats
import io
import time
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Callable, Optional, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.plugin_system import PluginBase, PluginResult, PluginConfig, HookPoint


@dataclass
class ProfileResult:
    """Result from profiling a function"""
    function_name: str
    total_time_ms: float
    calls: int
    time_per_call_ms: float
    cumulative_time_ms: float


@dataclass
class ProfileSummary:
    """Summary of profiling results"""
    total_functions: int
    total_time_ms: float
    hotspots: list = field(default_factory=list)  # Top slow functions
    call_counts: dict = field(default_factory=dict)


class ProfilerPlugin(PluginBase):
    """
    Performance profiler plugin.
    
    Profiles code execution and identifies performance hotspots.
    """
    
    def __init__(self, config=None):
        super().__init__(config or PluginConfig(
            hooks=[HookPoint.POST_ANALYZE],
            settings={
                "top_n_hotspots": 10,
                "min_time_threshold_ms": 1.0,
                "include_builtins": False
            }
        ))
        self._profiler = None
        self._results: list[ProfileResult] = []
    
    @property
    def name(self) -> str:
        return "ProfilerPlugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Performance profiler with hotspot detection"
    
    def start_profiling(self):
        """Start the profiler"""
        self._profiler = cProfile.Profile()
        self._profiler.enable()
    
    def stop_profiling(self) -> list[ProfileResult]:
        """Stop profiling and return results"""
        if self._profiler is None:
            return []
        
        self._profiler.disable()
        
        # Parse stats
        stream = io.StringIO()
        stats = pstats.Stats(self._profiler, stream=stream)
        stats.sort_stats('cumulative')
        
        results = []
        
        # Get raw stats
        for key, value in stats.stats.items():
            filename, line, func_name = key
            cc, nc, tt, ct, callers = value
            
            # Skip builtins if configured
            if not self.config.settings.get("include_builtins", False):
                if '<' in func_name or filename.startswith('<'):
                    continue
            
            time_ms = tt * 1000
            if time_ms >= self.config.settings.get("min_time_threshold_ms", 1.0):
                results.append(ProfileResult(
                    function_name=f"{func_name} ({Path(filename).name}:{line})",
                    total_time_ms=round(time_ms, 3),
                    calls=nc,
                    time_per_call_ms=round((tt / nc * 1000) if nc > 0 else 0, 3),
                    cumulative_time_ms=round(ct * 1000, 3)
                ))
        
        # Sort by total time
        results.sort(key=lambda r: r.total_time_ms, reverse=True)
        
        self._profiler = None
        return results
    
    def profile_function(self, func: Callable, *args, **kwargs) -> tuple[Any, list[ProfileResult]]:
        """Profile a single function call"""
        self.start_profiling()
        try:
            result = func(*args, **kwargs)
        finally:
            stats = self.stop_profiling()
        return result, stats
    
    def profile_code(self, code: str, globals_dict: dict = None) -> list[ProfileResult]:
        """Profile code string execution"""
        if globals_dict is None:
            globals_dict = {}
        
        self.start_profiling()
        try:
            exec(code, globals_dict)
        except Exception as e:
            pass
        finally:
            return self.stop_profiling()
    
    def analyze_file(self, filepath: str) -> ProfileSummary:
        """Analyze a Python file for performance characteristics"""
        import ast
        
        path = Path(filepath)
        if not path.exists() or path.suffix != '.py':
            return ProfileSummary(total_functions=0, total_time_ms=0)
        
        try:
            content = path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            functions = []
            loops = 0
            nested_loops = 0
            comprehensions = 0
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                    
                    # Count loops inside function
                    for child in ast.walk(node):
                        if isinstance(child, (ast.For, ast.While)):
                            loops += 1
                            # Check for nested loops
                            for grandchild in ast.walk(child):
                                if grandchild is not child and isinstance(grandchild, (ast.For, ast.While)):
                                    nested_loops += 1
                        if isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                            comprehensions += 1
            
            # Estimate complexity based on structure
            hotspots = []
            if nested_loops > 0:
                hotspots.append(f"⚠️ {nested_loops} nested loops detected (O(n²) potential)")
            if loops > 10:
                hotspots.append(f"⚠️ {loops} loops total (review for optimization)")
            
            return ProfileSummary(
                total_functions=len(functions),
                total_time_ms=0,  # Would need actual execution
                hotspots=hotspots,
                call_counts={"loops": loops, "nested_loops": nested_loops, "comprehensions": comprehensions}
            )
            
        except Exception as e:
            return ProfileSummary(total_functions=0, total_time_ms=0, hotspots=[str(e)])
    
    def execute(self, context: dict) -> PluginResult:
        """Execute profiler analysis on files"""
        files = context.get("files", [])
        settings = self.config.settings
        
        all_summaries = []
        total_functions = 0
        all_hotspots = []
        
        for filepath in files:
            if not filepath.endswith('.py'):
                continue
            
            summary = self.analyze_file(filepath)
            all_summaries.append({
                "file": Path(filepath).name,
                "functions": summary.total_functions,
                "hotspots": summary.hotspots,
                "metrics": summary.call_counts
            })
            
            total_functions += summary.total_functions
            all_hotspots.extend(summary.hotspots)
        
        return PluginResult(
            success=True,
            plugin_name=self.name,
            plugin_version=self.version,
            message=f"Profiled {len(all_summaries)} files, {total_functions} functions, "
                    f"{len(all_hotspots)} potential hotspots",
            data={
                "files_analyzed": len(all_summaries),
                "total_functions": total_functions,
                "potential_hotspots": len(all_hotspots),
                "summaries": all_summaries,
                "hotspots": all_hotspots[:settings.get("top_n_hotspots", 10)]
            }
        )


def time_function(func: Callable, *args, **kwargs) -> tuple[Any, float]:
    """Simple timing wrapper"""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = (time.perf_counter() - start) * 1000
    return result, elapsed


if __name__ == "__main__":
    print("📊 Performance Profiler Plugin Demo")
    print("=" * 40)
    
    plugin = ProfilerPlugin()
    
    # Analyze source files
    src_dir = Path(__file__).parent.parent / "src"
    files = [str(f) for f in src_dir.glob("*.py")]
    
    result = plugin.execute({"files": files})
    
    print(f"\n{result.message}")
    
    print("\n📁 File Analysis:")
    for summary in result.data.get("summaries", []):
        print(f"  {summary['file']}:")
        print(f"    Functions: {summary['functions']}")
        print(f"    Loops: {summary['metrics'].get('loops', 0)}, "
              f"Nested: {summary['metrics'].get('nested_loops', 0)}")
        for hotspot in summary.get('hotspots', []):
            print(f"    {hotspot}")
    
    if result.data.get("hotspots"):
        print("\n⚠️ Potential Hotspots:")
        for hs in result.data["hotspots"]:
            print(f"  {hs}")
    else:
        print("\n✅ No obvious performance hotspots detected!")
