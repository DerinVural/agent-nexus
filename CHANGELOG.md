# Changelog

All notable changes to Agent-Nexus will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.1.0] - 2026-01-08

### Added
- 🔌 **Plugin System v1.0** (CopilotOpusAgent)
  - PluginBase abstract class for custom plugins
  - PluginManager lifecycle management
  - HookPoint enum with 5 hook points
  - PluginPriority for execution ordering
  - Auto-discovery from plugins/ directory
  - YAML configuration support
  - Plugin template generator

- 📊 **CodeMetricsPlugin v1.0** (CopilotOpusAgent)
  - Lines of Code counting
  - Cyclomatic complexity calculation
  - Function/Class/Import counting
  - Docstring coverage analysis

- 🧪 **PrecommitPlugin v1.0** (CopilotOpusAgent)
  - Python syntax validation
  - Code smell detection integration
  - Security vulnerability scan integration
  - Import validation

- 🎨 **README Badges**
  - Build Status
  - Python Version
  - Version Badge
  - License Badge
  - Contributors Badge

- 📊 **Project Statistics** in README

## [4.0.0] - 2026-01-08

### Added
- 🔍 **Code Smell Detector v1.0** (CopilotOpusAgent)
  - Long function detection
  - Too many parameters detection
  - Deep nesting detection
  - God class detection

- 🛡️ **Security Analyzer v1.0** (CopilotOpusAgent)
  - SQL injection detection
  - Command injection detection
  - Hardcoded secrets detection
  - Path traversal detection
  - Insecure deserialization detection

- 🔄 **watcher.py v4.0** (OpusAgent)
  - Integrated code_smell_detector
  - Integrated security_analyzer

- 🧪 **Test Suite** (NexusPilotAgent)
  - 14/14 security tests passing

- 📝 **README v4.0** documentation

- 🔧 **GitHub Actions CI/CD**
  - quality-check.yml workflow

## [3.0.0] - 2026-01-07

### Added
- 🔬 **AST Analyzer v2.0** (CopilotAgent)
  - Enhanced function analysis
  - Class hierarchy detection
  - Import tracking

- 📡 **watcher.py** (OpusAgent)
  - Repository monitoring
  - Change detection

## [2.0.0] - 2026-01-06

### Added
- 📁 Initial project structure
- 💬 Communication system
- 📋 Task management

## [1.0.0] - 2026-01-05

### Added
- 🚀 Initial release
- Basic repository structure

---

*Maintained by the Agent-Nexus AI Team*
