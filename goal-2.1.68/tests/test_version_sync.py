import os
from pathlib import Path
from goal.cli import sync_all_versions

def test_sync_updates_init_py(tmp_path):
    """Test that sync_all_versions updates __version__ in __init__.py files."""
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        
        # Create a dummy project structure
        pkg_dir = tmp_path / "mypkg"
        pkg_dir.mkdir()
        
        # valid __init__.py
        init_file = pkg_dir / "__init__.py"
        init_file.write_text('__version__ = "0.1.0"\n')
        
        # nested __init__.py
        sub_dir = pkg_dir / "sub"
        sub_dir.mkdir()
        sub_init = sub_dir / "__init__.py"
        sub_init.write_text('__version__ = "0.1.0"\n')
        
        # Create a venv dir (should be ignored)
        venv_dir = tmp_path / ".venv" / "lib" / "site-packages" / "other"
        venv_dir.mkdir(parents=True)
        venv_init = venv_dir / "__init__.py"
        venv_init.write_text('__version__ = "0.1.0"\n')
        
        # Create VERSION file required by sync_all_versions
        (tmp_path / "VERSION").write_text("0.1.0\n")
        
        # Run sync
        # Bypass nfo decorator if present to avoid rich I/O errors during tests
        func = sync_all_versions
        while hasattr(func, '__wrapped__'):
            func = func.__wrapped__
        
        updated = func("0.2.0")
        
        # Check results
        assert 'mypkg/__init__.py' in updated or str(init_file) in updated
        assert 'mypkg/sub/__init__.py' in updated or str(sub_init) in updated
        
        # Verify content
        assert '__version__ = "0.2.0"' in init_file.read_text()
        assert '__version__ = "0.2.0"' in sub_init.read_text()
        
        # Verify venv ignored
        assert '__version__ = "0.1.0"' in venv_init.read_text()
        
    finally:
        os.chdir(old_cwd)
