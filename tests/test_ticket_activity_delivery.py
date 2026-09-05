"""Real managed receipts distinguish completed work from pending delivery."""

import json
from pathlib import Path
import shutil
import subprocess
from unittest.mock import Mock

import click
import pytest

from goal.governance import delivery
from goal.push import core


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


@pytest.fixture
def activity_repo(tmp_path):
    root = tmp_path / 'repo'
    root.mkdir()
    git(root, 'init', '-q', '-b', 'main')
    git(root, 'config', 'user.email', 'test@example.test')
    git(root, 'config', 'user.name', 'Test')
    managed = root / '.governance'
    managed.mkdir()
    source = Path(__file__).resolve().parents[1] / '.governance'
    for name in ('ticket_activity.py', 'ticket-activity.json'):
        shutil.copyfile(source / name, managed / name)
    for ticket in ('ticket-001', 'ticket-002'):
        directory = root / 'project' / ticket
        directory.mkdir(parents=True)
        (directory / 'README.md').write_text('- **Status**: IN_PROGRESS\n')
    git(root, 'add', '.')
    git(root, 'commit', '-qm', 'fixture')
    remote = tmp_path / 'remote.git'
    git(root, 'clone', '-q', '--bare', str(root), str(remote))
    git(root, 'remote', 'add', 'origin', str(remote))
    sha = git(root, 'rev-parse', 'HEAD')
    registry = root / '.git/new-project/terminal-receipts.json'
    registry.parent.mkdir()
    value = {
        'schema': 'new-project.terminal-receipt-registry/v1',
        'repositoryRef': str(remote).removesuffix('.git').lower(),
        'receipts': [
            {'receiptRef': f'receipt:test:{number}', 'ticket': f'ticket-{number:03}',
             'outcome': 'merged', 'headSha': sha, 'terminalSha': sha,
             'targetBranch': 'main', 'occurredAt': '2026-09-05T00:00:00Z'}
            for number in (1, 2)
        ],
    }
    registry.write_text(json.dumps(value))
    return root, registry, value


def policy():
    return delivery.resolve_delivery_policy({}, 'pull-request', all_flags=True)


def test_verified_terminal_receipts_allow_clean_base_noop(activity_repo):
    root, _, _ = activity_repo
    assert delivery.resolve_pull_request_ticket(policy(), None, cwd=root) is None
    assert git(root, 'status', '--porcelain') == ''


def test_one_unfinished_ticket_is_inferred(activity_repo):
    root, registry, value = activity_repo
    value['receipts'].pop()
    registry.write_text(json.dumps(value))
    assert delivery.resolve_pull_request_ticket(policy(), None, cwd=root) == 'ticket-002'


def test_invalid_registry_fails_closed(activity_repo):
    root, registry, _ = activity_repo
    registry.write_text('{}')
    with pytest.raises(click.ClickException, match='GOV-TICKET-ACTIVITY-001'):
        delivery.resolve_pull_request_ticket(policy(), None, cwd=root)


@pytest.mark.parametrize('state', ['dirty', 'ahead', 'branch'])
def test_terminal_receipts_do_not_hide_undelivered_work(activity_repo, state):
    root, _, _ = activity_repo
    if state == 'dirty':
        (root / 'new.py').write_text('pending = True\n')
    elif state == 'ahead':
        git(root, 'commit', '--allow-empty', '-qm', 'unpublished')
    else:
        git(root, 'checkout', '-qb', 'pending')
    with pytest.raises(click.ClickException, match='none was found'):
        delivery.resolve_pull_request_ticket(policy(), None, cwd=root)


def test_noop_exits_before_bootstrap_and_publication(activity_repo, monkeypatch, capsys):
    root, _, _ = activity_repo
    monkeypatch.chdir(root)
    monkeypatch.setattr(delivery, 'validate_delivery_ready', Mock())
    monkeypatch.setattr(core, '_validate_toml_or_exit', Mock())
    def unexpected(*args, **kwargs):
        pytest.fail('no-change delivery started workflow mutations')
    for name in ('_detect_project_types', '_bootstrap_projects_for_delivery',
                 '_handle_commit_phase', 'handle_publish', 'create_tag'):
        monkeypatch.setattr(core, name, unexpected)
    core.execute_push_workflow(
        ctx_obj={'config': {}, 'delivery_mode': 'pull-request', 'all_flags': True},
        bump='patch', no_tag=False, no_changelog=False, no_version_sync=False,
        message=None, dry_run=False, yes=True, markdown=False, split=False,
        ticket=None, abstraction=None, todo=False,
    )
    assert 'No changes to deliver' in capsys.readouterr().out
    assert git(root, 'status', '--porcelain') == ''
