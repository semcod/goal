"""Tests for goal/user_config.py."""
import json
import tempfile
from pathlib import Path
from unittest import mock
import pytest

from goal.user_config import (
    UserConfig,
    get_git_user_name,
    get_git_user_email,
    initialize_user_config,
    get_user_config,
    show_user_config,
    AVAILABLE_LICENSES,
)


def test_user_config_load_existing():
    """Test loading existing user config."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / '.goal'
        config_data = {
            'author_name': 'Test User',
            'author_email': 'test@example.com',
            'license': 'MIT'
        }
        config_path.write_text(json.dumps(config_data))
        
        with mock.patch.object(Path, 'home', return_value=Path(tmp_dir)):
            config = UserConfig()
            assert config.get('author_name') == 'Test User'
            assert config.get('author_email') == 'test@example.com'
            assert config.get('license') == 'MIT'


def test_user_config_save():
    """Test saving user config."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with mock.patch.object(Path, 'home', return_value=Path(tmp_dir)):
            config = UserConfig()
            config.set('author_name', 'New User')
            config.set('author_email', 'new@example.com')
            
            # Verify saved
            saved_path = Path(tmp_dir) / '.goal'
            assert saved_path.exists()
            saved_data = json.loads(saved_path.read_text())
            assert saved_data['author_name'] == 'New User'


def test_user_config_is_initialized():
    """Test initialization check."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with mock.patch.object(Path, 'home', return_value=Path(tmp_dir)):
            config = UserConfig()
            assert not config.is_initialized()
            
            # Set required fields
            config.set('author_name', 'Test')
            config.set('author_email', 'test@test.com')
            config.set('license', 'MIT')
            assert config.is_initialized()


def test_get_git_user_name():
    """Test getting git user.name."""
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'Test User\n'
        
        result = get_git_user_name()
        assert result == 'Test User'


def test_get_git_user_name_failure():
    """Test getting git user.name when not set."""
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 1
        
        result = get_git_user_name()
        assert result is None


def test_get_git_user_email():
    """Test getting git user.email."""
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'test@example.com\n'
        
        result = get_git_user_email()
        assert result == 'test@example.com'


def test_available_licenses():
    """Test that available licenses are defined."""
    assert '1' in AVAILABLE_LICENSES
    assert AVAILABLE_LICENSES['1']['id'] == 'Apache-2.0'
    assert 'MIT' in [lic['id'] for lic in AVAILABLE_LICENSES.values()]


def test_user_config_get_default():
    """Test get with default value."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        with mock.patch.object(Path, 'home', return_value=Path(tmp_dir)):
            config = UserConfig()
            assert config.get('nonexistent', 'default') == 'default'
