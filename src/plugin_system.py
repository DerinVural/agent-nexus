"""
Agent-Nexus Plugin System v1.0
===============================
Created by: CopilotOpusAgent
Date: 2026-01-08

Extensible plugin architecture for custom analyzers and tools.

Features:
- Plugin auto-discovery from plugins/ directory
- Hook points: pre-analyze, post-analyze, on-error
- Plugin configuration via YAML
- Execution results and error handling
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional
import importlib.util
import logging
import yaml
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HookPoint(Enum):
    """Available hook points for plugins"""
    PRE_ANALYZE = "pre_analyze"
    POST_ANALYZE = "post_analyze"
    ON_ERROR = "on_error"
    ON_FILE_CHANGE = "on_file_change"
    ON_COMMIT = "on_commit"


class PluginPriority(Enum):
    """Plugin execution priority"""
    HIGHEST = 0
    HIGH = 25
    NORMAL = 50
    LOW = 75
    LOWEST = 100


@dataclass
class PluginResult:
    """Result from plugin execution"""
    success: bool
    plugin_name: str
    plugin_version: str
    message: str
    data: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "plugin_name": self.plugin_name,
            "plugin_version": self.plugin_version,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp
        }


@dataclass
class PluginConfig:
    """Plugin configuration"""
    enabled: bool = True
    priority: PluginPriority = PluginPriority.NORMAL
    hooks: list[HookPoint] = field(default_factory=lambda: [HookPoint.POST_ANALYZE])
    settings: dict = field(default_factory=dict)


class PluginBase(ABC):
    """
    Base class for all plugins.
    
    All plugins must inherit from this class and implement
    the required abstract methods.
    
    Example:
        class MyPlugin(PluginBase):
            @property
            def name(self) -> str:
                return "MyPlugin"
            
            @property
            def version(self) -> str:
                return "1.0.0"
            
            @property
            def description(self) -> str:
                return "My awesome plugin"
            
            def execute(self, context: dict) -> PluginResult:
                # Plugin logic here
                return PluginResult(
                    success=True,
                    plugin_name=self.name,
                    plugin_version=self.version,
                    message="Execution complete"
                )
    """
    
    def __init__(self, config: Optional[PluginConfig] = None):
        self._config = config or PluginConfig()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique plugin name"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version (semver)"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Short plugin description"""
        pass
    
    @property
    def config(self) -> PluginConfig:
        """Get plugin configuration"""
        return self._config
    
    @config.setter
    def config(self, value: PluginConfig):
        """Set plugin configuration"""
        self._config = value
    
    @property
    def hooks(self) -> list[HookPoint]:
        """Hook points this plugin responds to"""
        return self._config.hooks
    
    @property
    def priority(self) -> PluginPriority:
        """Plugin execution priority"""
        return self._config.priority
    
    def initialize(self) -> bool:
        """
        Called when plugin is loaded.
        Override for custom initialization.
        Returns True if initialization successful.
        """
        return True
    
    def cleanup(self) -> None:
        """
        Called when plugin is unloaded.
        Override for cleanup logic.
        """
        pass
    
    @abstractmethod
    def execute(self, context: dict) -> PluginResult:
        """
        Execute the plugin.
        
        Args:
            context: Execution context containing:
                - hook: Current hook point
                - files: List of files to analyze
                - changes: Dict of file changes
                - results: Results from previous plugins
                - config: Global configuration
        
        Returns:
            PluginResult with execution status and data
        """
        pass
    
    def on_error(self, error: Exception, context: dict) -> Optional[PluginResult]:
        """
        Called when plugin execution fails.
        Override for custom error handling.
        """
        logger.error(f"Plugin {self.name} error: {error}")
        return None


class PluginManager:
    """
    Manages plugin lifecycle: discovery, loading, execution.
    
    Example:
        manager = PluginManager()
        manager.load_plugins("plugins/")
        
        results = manager.run_hook(
            HookPoint.POST_ANALYZE,
            {"files": ["src/main.py"]}
        )
    """
    
    def __init__(self):
        self._plugins: dict[str, PluginBase] = {}
        self._hook_registry: dict[HookPoint, list[PluginBase]] = {
            hook: [] for hook in HookPoint
        }
    
    @property
    def plugins(self) -> dict[str, PluginBase]:
        """Get all registered plugins"""
        return self._plugins.copy()
    
    @property
    def plugin_count(self) -> int:
        """Get number of registered plugins"""
        return len(self._plugins)
    
    def register_plugin(self, plugin: PluginBase) -> bool:
        """
        Register a plugin instance.
        
        Args:
            plugin: Plugin instance to register
        
        Returns:
            True if registration successful
        """
        if plugin.name in self._plugins:
            logger.warning(f"Plugin '{plugin.name}' already registered")
            return False
        
        if not plugin.initialize():
            logger.error(f"Plugin '{plugin.name}' initialization failed")
            return False
        
        self._plugins[plugin.name] = plugin
        
        # Register for hooks
        for hook in plugin.hooks:
            self._hook_registry[hook].append(plugin)
            self._hook_registry[hook].sort(key=lambda p: p.priority.value)
        
        logger.info(f"Registered plugin: {plugin.name} v{plugin.version}")
        return True
    
    def unregister_plugin(self, name: str) -> bool:
        """
        Unregister a plugin by name.
        
        Args:
            name: Plugin name to unregister
        
        Returns:
            True if unregistration successful
        """
        if name not in self._plugins:
            logger.warning(f"Plugin '{name}' not found")
            return False
        
        plugin = self._plugins[name]
        plugin.cleanup()
        
        # Remove from hook registry
        for hook in HookPoint:
            self._hook_registry[hook] = [
                p for p in self._hook_registry[hook] if p.name != name
            ]
        
        del self._plugins[name]
        logger.info(f"Unregistered plugin: {name}")
        return True
    
    def load_plugins(self, plugins_path: str) -> int:
        """
        Auto-discover and load plugins from directory.
        
        Args:
            plugins_path: Path to plugins directory
        
        Returns:
            Number of plugins loaded
        """
        plugins_dir = Path(plugins_path)
        
        if not plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {plugins_path}")
            return 0
        
        loaded = 0
        
        for plugin_file in plugins_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            
            try:
                loaded += self._load_plugin_file(plugin_file)
            except Exception as e:
                logger.error(f"Failed to load {plugin_file}: {e}")
        
        logger.info(f"Loaded {loaded} plugins from {plugins_path}")
        return loaded
    
    def _load_plugin_file(self, plugin_file: Path) -> int:
        """Load plugins from a single file"""
        spec = importlib.util.spec_from_file_location(
            plugin_file.stem, plugin_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        loaded = 0
        
        # Find all PluginBase subclasses
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, PluginBase) and 
                attr is not PluginBase):
                
                try:
                    plugin = attr()
                    if self.register_plugin(plugin):
                        loaded += 1
                except Exception as e:
                    logger.error(f"Failed to instantiate {attr_name}: {e}")
        
        return loaded
    
    def load_config(self, config_path: str) -> bool:
        """
        Load plugin configurations from YAML file.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            True if configuration loaded successfully
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}")
            return False
        
        try:
            with open(config_file) as f:
                config = yaml.safe_load(f)
            
            plugins_config = config.get("plugins", {})
            
            for plugin_name, settings in plugins_config.items():
                if plugin_name in self._plugins:
                    plugin = self._plugins[plugin_name]
                    plugin.config = PluginConfig(
                        enabled=settings.get("enabled", True),
                        priority=PluginPriority[settings.get("priority", "NORMAL").upper()],
                        hooks=[HookPoint[h.upper()] for h in settings.get("hooks", ["post_analyze"])],
                        settings=settings.get("settings", {})
                    )
                    logger.info(f"Configured plugin: {plugin_name}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return False
    
    def run_hook(self, hook: HookPoint, context: dict) -> list[PluginResult]:
        """
        Execute all plugins registered for a hook.
        
        Args:
            hook: Hook point to execute
            context: Execution context
        
        Returns:
            List of plugin results
        """
        results = []
        context["hook"] = hook
        context["results"] = results
        
        for plugin in self._hook_registry[hook]:
            if not plugin.config.enabled:
                continue
            
            try:
                import time
                start = time.perf_counter()
                
                result = plugin.execute(context)
                result.execution_time_ms = (time.perf_counter() - start) * 1000
                
                results.append(result)
                
                logger.debug(
                    f"Plugin {plugin.name} executed in "
                    f"{result.execution_time_ms:.2f}ms"
                )
            except Exception as e:
                error_result = plugin.on_error(e, context)
                if error_result:
                    results.append(error_result)
                else:
                    results.append(PluginResult(
                        success=False,
                        plugin_name=plugin.name,
                        plugin_version=plugin.version,
                        message=f"Execution failed: {e}",
                        errors=[str(e)]
                    ))
        
        return results
    
    def run_all(self, context: dict) -> dict[HookPoint, list[PluginResult]]:
        """
        Run plugins for all hooks.
        
        Args:
            context: Execution context
        
        Returns:
            Dict mapping hooks to their results
        """
        return {
            hook: self.run_hook(hook, context)
            for hook in HookPoint
        }
    
    def get_summary(self) -> dict:
        """Get summary of registered plugins"""
        return {
            "total_plugins": self.plugin_count,
            "plugins": [
                {
                    "name": p.name,
                    "version": p.version,
                    "description": p.description,
                    "enabled": p.config.enabled,
                    "priority": p.priority.name,
                    "hooks": [h.value for h in p.hooks]
                }
                for p in self._plugins.values()
            ]
        }


# Example plugin implementation
class ExamplePlugin(PluginBase):
    """Example plugin demonstrating the plugin architecture"""
    
    @property
    def name(self) -> str:
        return "ExamplePlugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "Example plugin for demonstration"
    
    def execute(self, context: dict) -> PluginResult:
        files = context.get("files", [])
        
        return PluginResult(
            success=True,
            plugin_name=self.name,
            plugin_version=self.version,
            message=f"Analyzed {len(files)} files",
            data={"file_count": len(files)}
        )


def create_plugin_template(name: str, output_dir: str = "plugins") -> str:
    """
    Create a new plugin from template.
    
    Args:
        name: Plugin name (PascalCase)
        output_dir: Output directory
    
    Returns:
        Path to created plugin file
    """
    template = f'''"""
{name} Plugin for Agent-Nexus
=============================
Created by: CopilotOpusAgent
"""

from src.plugin_system import PluginBase, PluginResult, HookPoint, PluginConfig


class {name}(PluginBase):
    """TODO: Add plugin description"""
    
    @property
    def name(self) -> str:
        return "{name}"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "TODO: Add description"
    
    def initialize(self) -> bool:
        # TODO: Add initialization logic
        return True
    
    def execute(self, context: dict) -> PluginResult:
        # TODO: Implement plugin logic
        
        return PluginResult(
            success=True,
            plugin_name=self.name,
            plugin_version=self.version,
            message="Execution complete",
            data={{}}
        )
'''
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    file_path = output_path / f"{name.lower()}_plugin.py"
    file_path.write_text(template)
    
    return str(file_path)


if __name__ == "__main__":
    # Demo
    print("🔌 Agent-Nexus Plugin System v1.0")
    print("=" * 40)
    
    manager = PluginManager()
    
    # Register example plugin
    example = ExamplePlugin()
    manager.register_plugin(example)
    
    # Run plugins
    context = {
        "files": ["src/main.py", "src/utils.py", "tests/test_main.py"]
    }
    
    results = manager.run_hook(HookPoint.POST_ANALYZE, context)
    
    print("\n📊 Results:")
    for result in results:
        print(f"  - {result.plugin_name}: {result.message}")
        print(f"    Success: {result.success}, Time: {result.execution_time_ms:.2f}ms")
    
    print("\n📋 Summary:")
    summary = manager.get_summary()
    print(f"  Total plugins: {summary['total_plugins']}")
    for p in summary['plugins']:
        print(f"  - {p['name']} v{p['version']}: {p['description']}")
