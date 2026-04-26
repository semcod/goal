"""E2E tests for push workflow - tests the refactored push package."""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPushWorkflowImports:
    """Test that all push workflow imports work correctly."""
    
    def test_push_stages_commit_imports(self):
        """Test that commit stage imports work."""
        from goal.push.stages.commit import get_commit_message, enforce_quality_gates
        assert callable(get_commit_message)
        assert callable(enforce_quality_gates)
    
    def test_push_stages_version_imports(self):
        """Test that version stage imports work."""
        from goal.push.stages.version import handle_version_sync, get_version_info
        assert callable(handle_version_sync)
        assert callable(get_version_info)
    
    def test_push_stages_changelog_imports(self):
        """Test that changelog stage imports work."""
        from goal.push.stages.changelog import handle_changelog
        assert callable(handle_changelog)
    
    def test_push_stages_test_imports(self):
        """Test that test stage imports work."""
        from goal.push.stages.test import run_test_stage
        assert callable(run_test_stage)
    
    def test_push_stages_tag_imports(self):
        """Test that tag stage imports work."""
        from goal.push.stages.tag import create_tag
        assert callable(create_tag)
    
    def test_push_stages_push_remote_imports(self):
        """Test that push_remote stage imports work."""
        from goal.push.stages.push_remote import push_to_remote
        assert callable(push_to_remote)
    
    def test_push_stages_publish_imports(self):
        """Test that publish stage imports work."""
        from goal.push.stages.publish import handle_publish
        assert callable(handle_publish)
    
    def test_push_stages_dry_run_imports(self):
        """Test that dry_run stage imports work."""
        from goal.push.stages.dry_run import handle_dry_run
        assert callable(handle_dry_run)
    
    def test_push_core_imports(self):
        """Test that core module imports work."""
        from goal.push.core import execute_push_workflow, PushContext
        assert callable(execute_push_workflow)
        assert hasattr(PushContext, 'get')
    
    def test_push_commands_import(self):
        """Test that commands module imports work."""
        from goal.push.commands import push
        assert hasattr(push, 'callback')
    
    def test_push_package_import(self):
        """Test that the main push package exports all expected symbols."""
        from goal.push import (
            execute_push_workflow,
            get_commit_message,
            handle_version_sync,
            handle_changelog,
            run_test_stage,
            create_tag,
            push_to_remote,
            handle_publish,
        )
        assert all(callable(f) for f in [
            execute_push_workflow, get_commit_message, handle_version_sync,
            handle_changelog, run_test_stage, create_tag, push_to_remote,
            handle_publish
        ])
    
    def test_push_cmd_shim(self):
        """Test that the backward compatibility shim works."""
        from goal.cli.push_cmd import push, execute_push_workflow
        # push is the click command, execute_push_workflow is the function
        assert hasattr(push, 'callback')
        assert callable(execute_push_workflow)


class TestPushWorkflowIntegration:
    """Integration tests for push workflow stages."""
    
    def test_version_info_returns_tuple(self):
        """Test that get_version_info returns correct tuple."""
        from goal.push.stages.version import get_version_info
        
        # Test the function works with explicit version
        current, new = get_version_info('1.0.0', 'patch')
        assert current == '1.0.0'
        assert new == '1.0.1'
    
    def test_format_changes_section(self):
        """Test the format_changes_section helper."""
        from goal.summary.body_formatter import CommitBodyFormatter
        from goal.summary.quality_filter import SummaryQualityFilter
        
        # Create a mock quality filter
        quality_filter = MagicMock(spec=SummaryQualityFilter)
        quality_filter.categorize_files.return_value = {'core': ['test.py']}
        
        formatter = CommitBodyFormatter(quality_filter)
        
        # Test with empty file analyses
        section, tests, has_changes = formatter.format_changes_section(['test.py'], [])
        # Should return empty since no entities
        assert section == ""
        assert tests == []
        assert has_changes is False
    
    def test_build_functional_overview_with_features(self):
        """Test _build_functional_overview with features."""
        from goal.formatter import _build_functional_overview
        
        title, content, entities = _build_functional_overview(
            features=['API', 'CLI'],
            summary='',
            entities=[],
            files=['test.py'],
            stats={'test.py': (10, 5)},
            current_version='1.0.0',
            new_version='1.0.1',
            commit_msg='feat: add features',
            project_types=['python']
        )
        
        assert title == 'Summary'
        assert 'API' in content
        assert 'CLI' in content
        assert entities == []
    
    def test_build_functional_overview_fallback(self):
        """Test _build_functional_overview fallback path."""
        from goal.formatter import _build_functional_overview
        
        title, content, entities = _build_functional_overview(
            features=[],
            summary='',
            entities=[],
            files=['test.py'],
            stats={'test.py': (10, 5)},
            current_version='1.0.0',
            new_version='1.0.1',
            commit_msg='chore: update',
            project_types=['python']
        )
        
        assert title == 'Overview'
        assert 'python' in content


class TestPushWorkflowE2E:
    """End-to-end tests for the complete push workflow."""
    
    def test_push_workflow_dry_run(self, tmp_path):
        """Test push workflow in dry-run mode."""
        from click.testing import CliRunner
        from goal.push.commands import push
        
        runner = CliRunner()
        
        # Create a temporary git repo
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Initialize git repo
            subprocess.run(['git', 'init'], capture_output=True)
            subprocess.run(['git', 'config', 'user.email', 'test@test.com'], capture_output=True)
            subprocess.run(['git', 'config', 'user.name', 'Test'], capture_output=True)
            
            # Create a test file
            Path('test.txt').write_text('test content')
            
            # Run push with dry-run (should not fail on imports)
            result = runner.invoke(push, ['--dry-run', '--yes'])
            
            # Should not have import errors
            assert 'ModuleNotFoundError' not in result.output
            assert 'No module named' not in result.output
    
    def test_push_stages_handle_empty_inputs(self):
        """Test that push stages handle empty inputs gracefully."""
        from goal.push.stages.tag import create_tag
        from goal.push.stages.publish import handle_publish
        
        # These should not raise import errors
        assert create_tag is not None
        assert handle_publish is not None

    def test_handle_publish_skips_when_no_publish_flag_is_set(self):
        """Test that the publish stage respects --no-publish."""
        from goal.push.stages.publish import handle_publish

        with patch('goal.push.stages.publish.publish_project') as mock_publish_project:
            result = handle_publish(['python'], '1.2.3', yes=True, no_publish=True)

        assert result is False
        mock_publish_project.assert_not_called()

    def test_push_command_forwards_no_publish_flag(self):
        """Test that the CLI push command forwards --no-publish to the workflow."""
        from click.testing import CliRunner
        from goal.push.commands import push

        runner = CliRunner()

        with patch('goal.push.commands.execute_push_workflow') as mock_execute:
            result = runner.invoke(push, ['--no-publish'], obj={'yes': False})

        assert result.exit_code == 0
        mock_execute.assert_called_once()
        assert mock_execute.call_args.kwargs['no_publish'] is True

    def test_push_workflow_aborts_on_auto_test_failure(self):
        """Test that --all workflow stops when tests fail."""
        from goal.push.core import execute_push_workflow

        ctx_obj = {
            'yes': True,
            'markdown': False,
            'config': {},
            'user_config': {},
        }

        with patch('goal.push.core.check_pyproject_toml', return_value=None), \
             patch('goal.push.core._initialize_context'), \
             patch('goal.push.core._detect_and_bootstrap_projects', return_value=['python']), \
             patch('goal.push.core.run_git'), \
             patch('goal.push.core.get_staged_files', return_value=['test.txt']), \
             patch('goal.push.core._validate_staged_files'), \
             patch('goal.push.core.get_diff_content', return_value='diff'), \
             patch('goal.push.core.get_diff_stats', return_value={'test.txt': (1, 0)}), \
             patch('goal.push.core.get_commit_message', return_value=('feat: test', None, {})), \
             patch('goal.push.core.get_version_info', return_value=('0.1.0', '0.1.1')), \
             patch('goal.push.core.run_test_stage', return_value=('Tests failed', 1)), \
             patch('goal.push.core._handle_commit_phase') as mock_commit_phase, \
             patch('goal.push.core.create_tag') as mock_create_tag, \
             patch('goal.push.core.push_to_remote') as mock_push_remote, \
             patch('goal.push.core.handle_publish') as mock_publish:
            with pytest.raises(SystemExit) as exc:
                execute_push_workflow(
                    ctx_obj=ctx_obj,
                    bump='patch',
                    no_tag=False,
                    no_changelog=False,
                    no_version_sync=False,
                    no_publish=False,
                    message=None,
                    dry_run=False,
                    yes=True,
                    markdown=False,
                    split=False,
                    ticket=None,
                    abstraction=None,
                    todo=False,
                )

        assert exc.value.code == 1
        mock_commit_phase.assert_not_called()
        mock_create_tag.assert_not_called()
        mock_push_remote.assert_not_called()
        mock_publish.assert_not_called()

    def test_commit_phase_refreshes_costs_before_single_commit(self):
        """Test that the costs README refresh is staged before the main commit."""
        from goal.push.core import _handle_commit_phase

        ctx_obj = {
            'yes': True,
            'markdown': False,
            'config': None,
            'user_config': {},
        }

        with patch('goal.push.core.handle_version_sync') as mock_version_sync, \
             patch('goal.push.core.handle_changelog') as mock_changelog, \
             patch('goal.push.core._update_cost_badges', return_value=True) as mock_update_badges, \
             patch('goal.push.core.run_git_local') as mock_run_git_local, \
             patch('goal.push.core.handle_single_commit') as mock_single_commit:
            _handle_commit_phase(
                ctx_obj=ctx_obj,
                split=False,
                message=None,
                commit_title='feat: add thing',
                commit_body=None,
                commit_msg='feat: add thing',
                files=['src/app.py'],
                ticket=None,
                new_version='1.2.4',
                current_version='1.2.3',
                no_version_sync=False,
                no_changelog=False,
            )

        mock_version_sync.assert_called_once_with('1.2.4', False, {}, True)
        mock_changelog.assert_called_once_with('1.2.4', ['src/app.py'], 'feat: add thing', None, False)
        mock_update_badges.assert_called_once_with(ctx_obj, '1.2.4')
        mock_run_git_local.assert_called_once_with('add', 'README.md')
        mock_single_commit.assert_called_once_with('feat: add thing', None, 'feat: add thing', None, True)

    def test_publish_project_skips_nodejs_publish_when_not_configured(self):
        """Test that local Node.js packages without nodejs project config are not published."""
        from goal.cli.publish import publish_project

        config = {
            'project': {
                'type': ['python'],
            },
        }

        with patch('goal.cli.publish.validate_project_toml_files', return_value=(True, [])), \
             patch('goal.cli.publish.run_command_tee') as mock_run_command:
            result = publish_project(['nodejs'], '1.2.3', yes=True, config=config)

        assert result is True
        mock_run_command.assert_not_called()

    def test_publish_project_runs_nodejs_publish_when_configured(self):
        """Test that explicit Node.js publish configuration still runs npm publish."""
        from goal.cli.publish import publish_project

        config = {
            'project': {
                'type': ['nodejs'],
            },
            'strategies': {
                'nodejs': {
                    'publish': 'npm publish --access public',
                }
            }
        }

        with patch('goal.cli.publish.validate_project_toml_files', return_value=(True, [])), \
             patch('goal.cli.publish.run_command_tee') as mock_run_command:
            mock_run_command.return_value = MagicMock(returncode=0, stdout='', stderr='')

            result = publish_project(['nodejs'], '1.2.3', yes=True, config=config)

        assert result is True
        mock_run_command.assert_called_once_with('npm publish --access public')

    def test_publish_command_falls_back_when_make_publish_fails(self):
        """Test that goal publish falls back to direct publish after Makefile failure."""
        from goal.cli.publish_cmd import _publish_impl

        ctx_obj = {'config': None}

        with patch('goal.cli.publish_cmd.detect_project_types', return_value=['python']) as mock_detect, \
             patch('goal.cli.publish_cmd.shutil.which', return_value='/usr/bin/make') as mock_which, \
             patch('goal.cli.publish_cmd.makefile_has_target', return_value=True) as mock_has_target, \
             patch('goal.cli.publish_cmd.run_command_tee') as mock_run_command, \
             patch('goal.cli.publish_cmd.get_current_version', return_value='1.2.3') as mock_version, \
             patch('goal.cli.publish_cmd.publish_project', return_value=True) as mock_publish_project:
            mock_run_command.return_value = MagicMock(returncode=1, stdout='boom', stderr='boom')

            _publish_impl(ctx_obj, True, 'publish', None)

        mock_detect.assert_called_once()
        mock_which.assert_called_once_with('make')
        mock_has_target.assert_called_once_with('publish')
        mock_run_command.assert_called_once_with('make publish')
        mock_version.assert_called_once_with()
        mock_publish_project.assert_called_once_with(['python'], '1.2.3', False, config=None)

    def test_run_tests_ignores_top_level_tests_dir_as_subdir(self):
        """Test that the canonical top-level tests dir is not rerun as a subdir scan."""
        from goal.cli.tests import run_tests

        with patch('goal.cli.tests._find_python_test_dirs', return_value=[]), \
             patch('goal.cli.tests._find_python_bin', return_value='/tmp/project/.venv/bin/python') as mock_find_python_bin, \
             patch('goal.cli.tests.subprocess.run') as mock_subprocess_run:
            mock_subprocess_run.return_value = MagicMock(returncode=0)

            assert run_tests(['python']) is True

        mock_find_python_bin.assert_called_once()
        assert mock_subprocess_run.call_count == 2
        mock_subprocess_run.assert_any_call(
            ['/tmp/project/.venv/bin/python', '-c', 'import pytest'],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
        )
        mock_subprocess_run.assert_any_call(
            ['/tmp/project/.venv/bin/python', '-m', 'pytest'],
            capture_output=False,
            text=True,
        )

    def test_publish_command_imports_all_required_modules(self):
        """Regression test: publish command must have all imports including shutil."""
        # This test catches issues like missing shutil import in publish_cmd.py
        # which caused: NameError: name 'shutil' is not defined
        from goal.cli.publish_cmd import publish, _publish_impl
        import inspect

        # Get the source file path
        source_file = inspect.getfile(_publish_impl)
        source = Path(source_file).read_text()

        # Check that shutil is imported (not just used)
        assert 'import shutil' in source, \
            f"Missing 'import shutil' in {source_file}"

        # Verify the module can be loaded without errors
        assert callable(_publish_impl)
        assert hasattr(publish, 'callback')


import pytest
pytest.main([__file__, '-v'])

