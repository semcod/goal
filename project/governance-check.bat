@echo off
setlocal
set "REPO_ROOT=%~dp0.."
python "%REPO_ROOT%\.governance\governance_check.py" --root "%REPO_ROOT%" --manifest .governance/manifest.json --lock .governance/manifest.lock.json --stack-profiles .governance/stack-profiles.json %*
exit /b %ERRORLEVEL%
