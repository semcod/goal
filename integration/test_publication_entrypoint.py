"""Exercise the actual wheel and observer executable in an isolated environment."""

import ast
from email.parser import BytesParser
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import tomllib
import unittest
import zipfile

from packaging.requirements import Requirement


ROOT = Path(__file__).resolve().parents[1]


class PublicationEntrypointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="goal-wheel-observer-")
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.base = Path(cls.temporary.name)
        cls.environment = dict(os.environ)
        for key in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"):
            cls.environment.pop(key, None)
        cls.home = cls.base / "home"
        cls.home.mkdir()
        cls.environment.update(HOME=str(cls.home), XDG_CONFIG_HOME=str(cls.home / "config"), XDG_STATE_HOME=str(cls.home / "state"))
        cls.work = cls.base / "empty-project"
        cls.work.mkdir()
        cls.run_checked([sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(cls.base / "dist")], cwd=ROOT)
        wheels = list((cls.base / "dist").glob("goal-*.whl"))
        assert len(wheels) == 1, wheels
        cls.wheel = wheels[0]
        cls.run_checked([sys.executable, "-I", "-m", "venv", str(cls.base / "venv")])
        cls.python = cls.base / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        cls.command = cls.python.parent / ("goal-publication-status.exe" if os.name == "nt" else "goal-publication-status")
        cls.run_checked([str(cls.python), "-I", "-m", "pip", "install", "--disable-pip-version-check", "--no-index", "--no-deps", str(cls.wheel)])

    @classmethod
    def run_checked(cls, argv, cwd=None):
        result = subprocess.run(argv, cwd=cwd or cls.work, env=cls.environment, capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise AssertionError(f"Command failed ({result.returncode}): {argv}\n{result.stdout}\n{result.stderr}")
        return result

    def test_installed_command_is_json_without_project_bootstrap(self):
        result = subprocess.run([str(self.command), "--registry", "private", "--package", "example", "--version", "1.0"], cwd=self.work, env=self.environment, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stderr, "")
        observation = json.loads(result.stdout)
        self.assertEqual(observation["schema"], "goal.publication-observation/v1")
        self.assertEqual(observation["state"], "unknown")
        self.assertFalse(observation["verified"])
        self.assertEqual(list(self.work.iterdir()), [])
        self.assertFalse((self.home / ".goal").exists())

    def test_installed_command_rejects_incomplete_arguments(self):
        result = subprocess.run([str(self.command), "--registry", "pypi"], cwd=self.work, env=self.environment, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("--package", result.stderr)
        self.assertIn("--version", result.stderr)

    def test_wheel_contains_the_observer_and_consistent_release_metadata(self):
        project = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]
        self.assertEqual(project["scripts"]["goal-publication-status"], "goal.publish.state:main")
        version = project["version"]
        self.assertEqual((ROOT / "VERSION").read_text().strip(), version)
        assignments = ast.parse((ROOT / "goal/__init__.py").read_text()).body
        runtime_version = next(node.value.value for node in assignments if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets))
        self.assertEqual(runtime_version, version)
        lock = tomllib.loads((ROOT / "uv.lock").read_text())
        self.assertEqual(next(item["version"] for item in lock["package"] if item["name"] == "goal"), version)
        result = self.run_checked([str(self.python), "-I", "-c", "from importlib.metadata import version; print(version('goal'))"])
        self.assertEqual(result.stdout.strip(), version)
        with zipfile.ZipFile(self.wheel) as archive:
            self.assertEqual(archive.read("goal/publish/state.py"), (ROOT / "goal/publish/state.py").read_bytes())

    def test_publication_tools_are_an_optional_reusable_installation_bundle(self):
        with zipfile.ZipFile(self.wheel) as archive:
            metadata_name = next(name for name in archive.namelist() if name.endswith('.dist-info/METADATA'))
            metadata = BytesParser().parsebytes(archive.read(metadata_name))
        self.assertIn('publish', metadata.get_all('Provides-Extra'))
        requirements = [Requirement(value) for value in metadata.get_all('Requires-Dist')]
        for tool in ('build', 'twine'):
            selected = [requirement for requirement in requirements if requirement.name == tool]
            self.assertTrue(any(requirement.marker and requirement.marker.evaluate({'extra': 'publish'}) for requirement in selected))
            self.assertFalse(any(requirement.marker is None or requirement.marker.evaluate({'extra': ''}) for requirement in selected))
        project = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']
        self.assertEqual(set(project['optional-dependencies']['publish']), {'build', 'twine'})
        self.assertFalse({'build', 'twine'} & set(project['dependencies']))

    def test_installed_observer_distinguishes_verification_and_network_failure(self):
        # Replace network inside the isolated child, keeping the test runner's
        # Goal and ambient PYTHONPATH out of the installed package's imports.
        program = textwrap.dedent('''
            import io,json,sys,tempfile,hashlib
            from pathlib import Path
            from goal.publish import state
            mode=sys.argv[1]
            content=b'exact admitted build'
            class Reply(io.BytesIO):
                status=200
                def geturl(self): return 'https://pypi.org/pypi/example/1.0/json'
            def fetch(url,timeout):
                if mode=='offline': raise TimeoutError('offline')
                digest=hashlib.sha256(content).hexdigest() if mode=='match' else 'b'*64
                return Reply(json.dumps({'info':{'name':'example','version':'1.0'},'urls':[{'filename':'example-1.0.whl','digests':{'sha256':digest},'yanked':False}]}).encode())
            state.urlopen=fetch
            with tempfile.TemporaryDirectory() as directory:
                artifact=Path(directory)/'example-1.0.whl'
                artifact.write_bytes(content)
                raise SystemExit(state.main(['--registry','pypi','--package','example','--version','1.0','--artifact',str(artifact)]))
        ''')
        for mode, code, verification in (("match", 0, "matched"), ("mismatch", 1, "mismatch"), ("offline", 2, "unverified")):
            with self.subTest(mode=mode):
                result = subprocess.run([str(self.python), "-I", "-c", program, mode], cwd=self.work, env=self.environment, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, code, result.stderr)
                observed = json.loads(result.stdout)
                self.assertEqual(observed["verification"], verification)
                self.assertEqual(observed["verified"], mode == "match")
        self.assertEqual(list(self.work.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
