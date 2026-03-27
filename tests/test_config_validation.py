"""Tests for configuration validation."""

import pytest
from goal.config.validation import ConfigValidator, ConfigValidationError, _auto_fix_config
from goal.config.constants import DEFAULT_CONFIG


class TestConfigValidator:
    """Test configuration validator."""
    
    def test_valid_default_config(self):
        """Test that default config is valid."""
        validator = ConfigValidator(DEFAULT_CONFIG)
        is_valid, errors, warnings = validator.validate()
        
        # Default config should be valid (might have warnings about auto-detection)
        assert is_valid or len(errors) == 0
        
    def test_missing_required_section(self):
        """Test validation catches missing required sections."""
        config = {'project': {'name': 'test'}, 'versioning': {}}  # missing 'git'
        validator = ConfigValidator(config)
        is_valid, errors, warnings = validator.validate()
        
        assert not is_valid
        assert any("Missing required section: 'git'" in e for e in errors)
    
    def test_invalid_project_type(self):
        """Test validation catches invalid project type."""
        config = DEFAULT_CONFIG.copy()
        config['project'] = {'name': 'test', 'type': 'invalid_type'}
        
        validator = ConfigValidator(config)
        is_valid, errors, warnings = validator.validate()
        
        assert not is_valid
        assert any("Invalid project type: 'invalid_type'" in e for e in errors)
    
    def test_invalid_commit_type(self):
        """Test validation catches invalid commit type."""
        config = DEFAULT_CONFIG.copy()
        config['git'] = config.get('git', {}).copy()
        config['git']['commit'] = {'type': 'invalid'}
        
        validator = ConfigValidator(config)
        is_valid, errors, warnings = validator.validate()
        
        assert not is_valid
        assert any("Invalid commit type: 'invalid'" in e for e in errors)
    
    def test_invalid_version_strategy(self):
        """Test validation catches invalid version strategy."""
        config = DEFAULT_CONFIG.copy()
        config['versioning'] = config.get('versioning', {}).copy()
        config['versioning']['strategy'] = 'invalid'
        
        validator = ConfigValidator(config)
        is_valid, errors, warnings = validator.validate()
        
        assert not is_valid
        assert any("Invalid version strategy: 'invalid'" in e for e in errors)
    
    def test_wrong_type_bool(self):
        """Test validation catches wrong types for boolean fields."""
        config = DEFAULT_CONFIG.copy()
        config['git'] = config.get('git', {}).copy()
        config['git']['commit'] = {'require_ticket': 'yes'}  # should be bool
        
        validator = ConfigValidator(config)
        is_valid, errors, warnings = validator.validate()
        
        assert not is_valid
        assert any("require_ticket must be a boolean" in e for e in errors)
    
    def test_coverage_threshold_range(self):
        """Test validation catches coverage threshold out of range."""
        config = DEFAULT_CONFIG.copy()
        config['advanced'] = {'tests': {'coverage_threshold': 150}}
        
        validator = ConfigValidator(config)
        is_valid, errors, warnings = validator.validate()
        
        assert not is_valid
        assert any("coverage_threshold must be between 0 and 100" in e for e in errors)
    
    def test_strict_mode_treats_warnings_as_errors(self):
        """Test that strict mode converts warnings to errors."""
        # Config with missing project name (generates warning)
        config = DEFAULT_CONFIG.copy()
        config['project'] = {'type': 'python'}  # no name
        
        validator = ConfigValidator(config)
        
        # Non-strict: should be valid with warnings
        is_valid, errors, warnings = validator.validate(strict=False)
        assert is_valid
        assert len(warnings) > 0
        
        # Strict: should be invalid
        is_valid, errors, warnings = validator.validate(strict=True)
        assert not is_valid
        assert len(errors) > 0
    
    def test_unknown_keys_warning(self):
        """Test that unknown keys generate warnings."""
        config = DEFAULT_CONFIG.copy()
        config['unknown_section'] = {'key': 'value'}
        
        validator = ConfigValidator(config)
        is_valid, errors, warnings = validator.validate()
        
        assert is_valid  # Unknown keys are warnings, not errors
        assert any("Unknown configuration key: 'unknown_section'" in w for w in warnings)


class TestAutoFixConfig:
    """Test configuration auto-fix functionality."""
    
    def test_fix_branch_prefix(self):
        """Test auto-fix for branch prefix."""
        config = {'git': {'remote': {'branch_prefix': 'wrong'}}}
        warnings = ["Branch prefix 'wrong' doesn't follow conventional naming (e.g., 'feature/')"]
        
        fixed = _auto_fix_config(config, warnings)
        
        assert fixed['git']['remote']['branch_prefix'] == 'feature/'
    
    def test_fix_tag_format(self):
        """Test auto-fix for tag format."""
        config = {'versioning': {'tag_format': 'version-{v}'}}
        warnings = ["tag_format 'version-{v}' doesn't contain '{version}'"]
        
        fixed = _auto_fix_config(config, warnings)
        
        assert fixed['versioning']['tag_format'] == 'v{version}'


class TestConfigValidationError:
    """Test ConfigValidationError exception."""
    
    def test_error_message_formatting(self):
        """Test that error message is formatted correctly."""
        errors = ["Error 1", "Error 2"]
        warnings = ["Warning 1"]
        
        exc = ConfigValidationError(errors, warnings)
        message = str(exc)
        
        assert "Configuration validation failed:" in message
        assert "Error 1" in message
        assert "Error 2" in message
        assert "Warning 1" in message
