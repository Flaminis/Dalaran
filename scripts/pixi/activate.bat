:<<'BATCH_SCRIPT'
@echo off
REM Polyglot script: works in cmd.exe and bash/Git Bash
REM Pixi activation script for Windows.
REM Runs ensure-dalaran-env to set up the environment.

REM ensure-dalaran-env may not exist yet on first activation (before package install).
REM In that case, silently skip - it will run on next activation after install.
where ensure-dalaran-env >nul 2>nul
if %errorlevel%==0 (
    ensure-dalaran-env
)
goto :eof
BATCH_SCRIPT

# Bash section - runs when executed by bash/Git Bash on Windows
if command -v ensure-dalaran-env &> /dev/null; then
    ensure-dalaran-env
fi
