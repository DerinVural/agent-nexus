#!/usr/bin/env python3
"""
Tests for plugin_system.py
CopilotOpusAgent - Test Suite v1.0
Aligned with actual PluginManager API
"""

import pytest
import sys
from datetime import datetime

# Import from plugin_system
from plugin_system import (
    PluginBase,
    PluginManager,
    PluginPriority,
    PluginResult,
    PluginConfig,
    HookPoint
)


class TestPluginResult:
    """Test PluginResult dataclass"""
    
    def test_success_result(self):
        """Test successful plugin result"""
        result = PluginResult(
            success=True,
            plugin_name="TestPlugin",
            plugin_version="1.0.0",
            message="Test passed"
        )
        assert result.success is True
        assert result.plugin_name == "TestPlugin"
        assert result.plugin_version == "1.0.0"
        assert result.message == "Test passed"
        assert result.data == {}
        assert result.errors == []
    
    def test_failure_result(self):
        """Test failed plugin result"""
        result = PluginResult(
            success=False,
            plugin_name="FailPlugin",
            plugin_version="1.0.0",
            message="Test failed",
            data={"error": "something"},
            errors=["Error 1"]
        )
        assert result.success is False
        assert result.data == {"error": "something"}
        assert "Error 1" in result.errors
    
    def test_to_dict(self):
        """Test PluginResult to_dict method"""
        result = PluginResult(
            success=True,
            plugin_name="DictPlugin",
            plugin_version="1.0.0",
            message="Dict test"
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["plugin_name"] == "DictPlugin"
        assert "timestamp" in d
    
    def test_execution_time(self):
        """Test execution time tracking"""
        result = PluginResult(
            success=True,
            plugin_name="TimePlugin",
            plugin_version="1.0.0",
            message="Time test",
            execution_time_ms=123.45
        )
        assert result.execution_time_ms == 123.45


class TestPluginConfig:
    """Test PluginConfig dataclass"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = PluginConfig()
        assert config.enabled is True
        assert config.priority == PluginPriority.NORMAL
        assert HookPoint.POST_ANALYZE in config.hooks
        assert config.settings == {}
    
    def test_custom_config(self):
        """Test custom configuration"""
        config = PluginConfig(
            enabled=False,
            priority=PluginPriority.HIGH,
            hooks=[HookPoint.ON_COMMIT],
            settings={"threshold": 80}
        )
        assert config.enabled is False
        assert config.priority == PluginPriority.HIGH
        assert config.hooks == [HookPoint.ON_COMMIT]
        assert config.settings["threshold"] == 80


class TestPluginPriority:
    """Test PluginPriority enum"""
    
    def test_priority_values(self):
        """Test priority ordering (lower value = higher priority)"""
        assert PluginPriority.HIGHEST.value < PluginPriority.HIGH.value
        assert PluginPriority.HIGH.value < PluginPriority.NORMAL.value
        assert PluginPriority.NORMAL.value < PluginPriority.LOW.value
        assert PluginPriority.LOW.value < PluginPriority.LOWEST.value
    
    def test_all_priorities_exist(self):
        """Test all priority levels exist"""
        priorities = [PluginPriority.LOWEST, PluginPriority.LOW, 
                      PluginPriority.NORMAL, PluginPriority.HIGH,
                      PluginPriority.HIGHEST]
        assert len(priorities) == 5


class TestHookPoint:
    """Test HookPoint enum"""
    
    def test_hook_points_exist(self):
        """Test all hook points exist"""
        assert HookPoint.PRE_ANALYZE
        assert HookPoint.POST_ANALYZE
        assert HookPoint.ON_ERROR
        assert HookPoint.ON_FILE_CHANGE
        assert HookPoint.ON_COMMIT
    
    def test_hook_values(self):
        """Test hook point string values"""
        assert HookPoint.PRE_ANALYZE.value == "pre_analyze"
        assert HookPoint.POST_ANALYZE.value == "post_analyze"
        assert HookPoint.ON_COMMIT.value == "on_commit"


class DummyPlugin(PluginBase):
    """A dummy plugin for testing"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.executed = False
        self.cleaned_up = False
        self._initialized = False
    
    @property
    def name(self) -> str:
        return "DummyPlugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "A dummy plugin for testing"
    
    def initialize(self) -> bool:
        self._initialized = True
        return True
    
    def execute(self, context: dict = None) -> PluginResult:
        self.executed = True
        return PluginResult(
            success=True,
            plugin_name=self.name,
            plugin_version=self.version,
            message="Dummy plugin executed",
            data={"context": context or {}}
        )
    
    def cleanup(self) -> None:
        self.cleaned_up = True


class FailingPlugin(PluginBase):
    """A plugin that always fails for testing error handling"""
    
    @property
    def name(self) -> str:
        return "FailingPlugin"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    @property
    def description(self) -> str:
        return "A plugin that always fails"
    
    def initialize(self) -> bool:
        return True
    
    def execute(self, context: dict = None) -> PluginResult:
        return PluginResult(
            success=False,
            plugin_name=self.name,
            plugin_version=self.version,
            message="Intentional failure",
            errors=["Failed on purpose"]
        )


class TestPluginBase:
    """Test PluginBase abstract class implementation"""
    
    def test_dummy_plugin_properties(self):
        """Test plugin property access"""
        plugin = DummyPlugin()
        assert plugin.name == "DummyPlugin"
        assert plugin.version == "1.0.0"
        assert plugin.description == "A dummy plugin for testing"
    
    def test_plugin_config_access(self):
        """Test plugin config access"""
        config = PluginConfig(priority=PluginPriority.HIGH)
        plugin = DummyPlugin(config)
        assert plugin.config.priority == PluginPriority.HIGH
    
    def test_dummy_plugin_execute(self):
        """Test plugin execution"""
        plugin = DummyPlugin()
        result = plugin.execute({"file": "test.py"})
        assert result.success is True
        assert plugin.executed is True
        assert result.data["context"]["file"] == "test.py"
    
    def test_dummy_plugin_cleanup(self):
        """Test plugin cleanup"""
        plugin = DummyPlugin()
        plugin.cleanup()
        assert plugin.cleaned_up is True
    
    def test_failing_plugin(self):
        """Test a plugin that fails"""
        plugin = FailingPlugin()
        result = plugin.execute()
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_plugin_hooks(self):
        """Test plugin hooks property"""
        config = PluginConfig(hooks=[HookPoint.ON_COMMIT, HookPoint.POST_ANALYZE])
        plugin = DummyPlugin(config)
        assert HookPoint.ON_COMMIT in plugin.hooks
        assert HookPoint.POST_ANALYZE in plugin.hooks
    
    def test_plugin_initialize(self):
        """Test plugin initialization"""
        plugin = DummyPlugin()
        result = plugin.initialize()
        assert result is True
        assert plugin._initialized is True


class TestPluginManager:
    """Test PluginManager class"""
    
    def test_manager_creation(self):
        """Test plugin manager instantiation"""
        manager = PluginManager()
        assert manager is not None
        assert manager.plugin_count == 0
    
    def test_register_plugin(self):
        """Test registering a plugin"""
        manager = PluginManager()
        plugin = DummyPlugin()
        
        result = manager.register_plugin(plugin)
        assert result is True
        assert manager.plugin_count == 1
        assert "DummyPlugin" in manager.plugins
    
    def test_plugins_property(self):
        """Test plugins property returns copy"""
        manager = PluginManager()
        plugin = DummyPlugin()
        manager.register_plugin(plugin)
        
        plugins = manager.plugins
        assert isinstance(plugins, dict)
        assert "DummyPlugin" in plugins
    
    def test_unregister_plugin(self):
        """Test unregistering a plugin"""
        manager = PluginManager()
        plugin = DummyPlugin()
        
        manager.register_plugin(plugin)
        assert manager.plugin_count == 1
        
        result = manager.unregister_plugin("DummyPlugin")
        assert result is True
        assert manager.plugin_count == 0
    
    def test_unregister_nonexistent_plugin(self):
        """Test unregistering a plugin that doesn't exist"""
        manager = PluginManager()
        result = manager.unregister_plugin("NonExistent")
        assert result is False
    
    def test_run_hook(self):
        """Test running plugins for a specific hook"""
        manager = PluginManager()
        config = PluginConfig(hooks=[HookPoint.POST_ANALYZE])
        plugin = DummyPlugin(config)
        
        manager.register_plugin(plugin)
        results = manager.run_hook(HookPoint.POST_ANALYZE, {"test": True})
        
        assert len(results) == 1
        assert results[0].success is True
        assert plugin.executed is True
    
    def test_run_hook_disabled_plugin(self):
        """Test that disabled plugins are skipped"""
        manager = PluginManager()
        config = PluginConfig(enabled=False, hooks=[HookPoint.POST_ANALYZE])
        plugin = DummyPlugin(config)
        
        manager.register_plugin(plugin)
        results = manager.run_hook(HookPoint.POST_ANALYZE, {})
        
        # Disabled plugins should be skipped
        assert len(results) == 0
        assert plugin.executed is False
    
    def test_run_all(self):
        """Test running plugins for all hooks"""
        manager = PluginManager()
        config = PluginConfig(hooks=[HookPoint.POST_ANALYZE])
        plugin = DummyPlugin(config)
        
        manager.register_plugin(plugin)
        results = manager.run_all({"batch": True})
        
        assert isinstance(results, dict)
        assert HookPoint.POST_ANALYZE in results


class TestPluginManagerAdvanced:
    """Advanced PluginManager tests"""
    
    def test_multiple_plugins(self):
        """Test with multiple plugins"""
        manager = PluginManager()
        plugin1 = DummyPlugin()
        plugin2 = FailingPlugin()
        
        manager.register_plugin(plugin1)
        manager.register_plugin(plugin2)
        
        assert manager.plugin_count == 2
        assert "DummyPlugin" in manager.plugins
        assert "FailingPlugin" in manager.plugins
    
    def test_priority_ordering(self):
        """Test plugins are sorted by priority"""
        manager = PluginManager()
        
        # Check that higher priority plugins execute first
        high_config = PluginConfig(priority=PluginPriority.HIGH)
        low_config = PluginConfig(priority=PluginPriority.LOW)
        
        assert high_config.priority.value < low_config.priority.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
