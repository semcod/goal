@echo off
setlocal
set "REPO_ROOT=%~dp0"

if not exist "%REPO_ROOT%.governance\manifest.json" (
  echo GOV-MANIFEST-001: .governance\manifest.json is not installed in this target repository. 1>&2
  echo   remediation: bootstrap the pinned governance package before implementation. 1>&2
  exit /b 1
)
if not exist "%REPO_ROOT%project\governance-check.bat" (
  echo GOV-BOOT-001: project\governance-check.bat is missing. 1>&2
  exit /b 1
)

call "%REPO_ROOT%project\governance-check.bat" %*
if errorlevel 1 exit /b %ERRORLEVEL%

if not "%NEW_PROJECT_ANALYSIS_IMAGE%"=="" (
  powershell -NoProfile -Command "if ($env:NEW_PROJECT_ANALYSIS_IMAGE -notmatch '@sha256:[a-f0-9]{64}$') { exit 1 }"
  if errorlevel 1 (
    echo GOV-STACK-001: NEW_PROJECT_ANALYSIS_IMAGE must be pinned by sha256 digest. 1>&2
    exit /b 1
  )
  docker info >nul 2>&1
  if errorlevel 1 (
    echo GOV-DOCKER-001: Docker engine is unavailable. 1>&2
    exit /b 1
  )
  docker run --rm --network none --mount "type=bind,src=%REPO_ROOT%,dst=/workspace" --workdir /workspace "%NEW_PROJECT_ANALYSIS_IMAGE%"
  exit /b %ERRORLEVEL%
)

exit /b 0
