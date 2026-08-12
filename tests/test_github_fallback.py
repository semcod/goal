"""Tests for GitHub Releases fallback when PyPI upload is blocked."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


from goal.publish.github_fallback import (
    GitHubReleaseConfig,
    detect_github_owner_repo,
    get_github_release_config,
    is_pypi_blocked,
    publish_github_release,
    resolve_github_repo,
    try_github_fallback,
    try_github_release_on_tag,
)


class TestBlockedDetection:
    def test_429_is_blocked(self):
        result = MagicMock(stderr="HTTPError: 429 Too Many Requests\nToo Many Requests")
        assert is_pypi_blocked(result) is True

    def test_403_is_blocked(self):
        result = MagicMock(stderr="HTTPError: 403 Forbidden")
        assert is_pypi_blocked(result) is True

    def test_auth_error_is_blocked(self):
        result = MagicMock(stderr="does not have permission to upload")
        assert is_pypi_blocked(result) is True


class TestGitHubConfig:
    def test_disabled_when_explicit_off(self):
        config = {"publishing": {"fallback": {"github_release": {"enabled": False}}}}
        assert get_github_release_config(config) is None

    def test_repo_map_resolution(self):
        gh = GitHubReleaseConfig(
            enabled=True,
            owner="tellmesh",
            repo="",
            token_env="GITHUB_TOKEN",
            skip_pypi_retries_on_block=True,
            asset_glob="dist/*",
            repo_map={"uricontrol": "uricore"},
        )
        assert resolve_github_repo("uricontrol", gh) == ("tellmesh", "uricore")
        assert resolve_github_repo("urimail", gh) == ("tellmesh", "urimail")

    def test_detect_github_remote(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="git@github.com:tellmesh/goal.git\n",
            )
            assert detect_github_owner_repo() == ("tellmesh", "goal")


class TestPublishFallbackOnBlock:
    def test_429_skips_pypi_retries_when_github_actionable(self, tmp_path, monkeypatch):
        from goal.cli.publish import _run_publish_command

        dist = tmp_path / "dist"
        dist.mkdir()
        (dist / "demo-1.0.0-py3-none-any.whl").write_bytes(b"wheel")
        monkeypatch.chdir(tmp_path)

        gh_config = GitHubReleaseConfig(
            enabled=True,
            owner="tellmesh",
            repo="demo",
            token_env="GITHUB_TOKEN",
            skip_pypi_retries_on_block=True,
            asset_glob="dist/*",
            repo_map={},
        )

        def fake_run(cmd):
            m = MagicMock()
            m.returncode = 1
            m.stderr = "HTTPError: 429 Too Many Requests\nToo Many Requests"
            m.stdout = ""
            return m

        with (
            patch("goal.cli.publish.run_command_tee", side_effect=fake_run),
            patch("goal.cli.publish.time.sleep") as mock_sleep,
            patch("goal.cli.publish.get_github_release_config", return_value=gh_config),
            patch("goal.cli.publish.github_fallback_actionable", return_value=True),
            patch(
                "goal.cli.publish.try_github_fallback",
                return_value=True,
            ) as mock_fallback,
            patch(
                "goal.cli.publish._read_python_package_name",
                return_value="demo",
            ),
        ):
            result = _run_publish_command(
                "python",
                "twine upload dist/*",
                version="1.0.0",
                config={"publishing": {}},
            )

        assert result is True
        mock_sleep.assert_not_called()
        mock_fallback.assert_called_once()

    def test_429_retries_when_github_not_actionable(self):
        from goal.cli.publish import _run_publish_command

        call_count = 0

        def fake_run(cmd):
            nonlocal call_count
            call_count += 1
            m = MagicMock()
            if call_count < 2:
                m.returncode = 1
                m.stderr = "HTTPError: 429 Too Many Requests\nToo Many Requests"
            else:
                m.returncode = 0
            m.stdout = ""
            return m

        gh_config = GitHubReleaseConfig(
            enabled=True,
            owner="tellmesh",
            repo="demo",
            token_env="GITHUB_TOKEN",
            skip_pypi_retries_on_block=True,
            asset_glob="dist/*",
            repo_map={},
        )

        with (
            patch("goal.cli.publish.run_command_tee", side_effect=fake_run),
            patch("goal.cli.publish.time.sleep") as mock_sleep,
            patch("goal.cli.publish.get_github_release_config", return_value=gh_config),
            patch("goal.cli.publish.github_fallback_actionable", return_value=False),
        ):
            result = _run_publish_command("python", "twine upload dist/*")

        assert result is True
        assert call_count == 2
        assert mock_sleep.call_count == 1

    def test_publish_github_release_uploads_assets(self, tmp_path, monkeypatch):
        dist = tmp_path / "dist"
        dist.mkdir()
        wheel = dist / "pkg-2.0.0-py3-none-any.whl"
        wheel.write_bytes(b"wheel")
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")

        gh_config = GitHubReleaseConfig(
            enabled=True,
            owner="tellmesh",
            repo="pkg",
            token_env="GITHUB_TOKEN",
            skip_pypi_retries_on_block=True,
            asset_glob="dist/*",
            repo_map={},
        )

        calls = []

        def fake_tee(cmd):
            calls.append(cmd)
            m = MagicMock()
            m.returncode = 0
            m.stdout = ""
            m.stderr = ""
            return m

        with (
            patch("goal.publish.github_fallback._gh_available", return_value=True),
            patch("goal.publish.github_fallback.run_command_tee", side_effect=fake_tee),
            patch(
                "subprocess.run",
                return_value=MagicMock(returncode=1),
            ),
        ):
            ok = publish_github_release(
                "2.0.0",
                package_name="pkg",
                gh_config=gh_config,
                artifacts=[wheel],
            )

        assert ok is True
        assert any("gh release create v2.0.0" in c for c in calls)
        assert any("gh release upload v2.0.0" in c and str(wheel) in c for c in calls)

    def test_package_fallback_still_rejects_missing_assets(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        gh_config = GitHubReleaseConfig(
            enabled=True,
            owner="tellmesh",
            repo="pkg",
            token_env="GITHUB_TOKEN",
            skip_pypi_retries_on_block=True,
            asset_glob="dist/*",
            repo_map={},
        )

        with (
            patch("goal.publish.github_fallback._gh_available", return_value=True),
            patch("goal.publish.github_fallback.run_command_tee") as run_tee,
        ):
            ok = publish_github_release(
                "2.0.0",
                package_name="pkg",
                gh_config=gh_config,
            )

        assert ok is False
        run_tee.assert_not_called()

    def test_create_on_tag_allows_generic_release_without_assets(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        config = {
            "publishing": {
                "fallback": {
                    "github_release": {
                        "enabled": True,
                        "owner": "wellmanifest",
                        "repo": "new-project",
                        "create_on_tag": True,
                    }
                }
            }
        }
        calls = []

        def fake_tee(command):
            calls.append(command)
            return MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("goal.publish.github_fallback._gh_available", return_value=True),
            patch(
                "goal.publish.github_fallback.subprocess.run",
                return_value=MagicMock(returncode=1),
            ),
            patch(
                "goal.publish.github_fallback.run_command_tee",
                side_effect=fake_tee,
            ),
        ):
            ok = try_github_release_on_tag(
                version="0.16.0",
                package_name="new-project",
                config=config,
                allow_empty_assets=True,
            )

        assert ok is True
        assert len(calls) == 1
        assert "gh release create v0.16.0" in calls[0]
        assert "PyPI blocked" not in calls[0]
        assert not any("gh release upload" in call for call in calls)

    def test_assetless_release_is_idempotent_when_release_exists(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        gh_config = GitHubReleaseConfig(
            enabled=True,
            owner="wellmanifest",
            repo="new-project",
            token_env="GITHUB_TOKEN",
            skip_pypi_retries_on_block=True,
            asset_glob="dist/*",
            repo_map={},
            create_on_tag=True,
        )

        with (
            patch("goal.publish.github_fallback._gh_available", return_value=True),
            patch(
                "goal.publish.github_fallback.subprocess.run",
                return_value=MagicMock(returncode=0),
            ),
            patch("goal.publish.github_fallback.run_command_tee") as run_tee,
        ):
            ok = publish_github_release(
                "0.16.0",
                package_name="new-project",
                gh_config=gh_config,
                allow_empty_assets=True,
            )

        assert ok is True
        run_tee.assert_not_called()

    def test_try_github_fallback_noop_when_not_blocked(self):
        result = MagicMock(stderr="network timeout")
        assert (
            try_github_fallback(
                result,
                version="1.0.0",
                config={
                    "publishing": {"fallback": {"github_release": {"enabled": True}}}
                },
            )
            is False
        )
