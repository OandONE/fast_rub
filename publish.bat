@echo off
REM publish.bat - upload each package to PyPI and archive on success

set VERSIONS_DIR=versions

REM Create versions directory if not exists
if not exist "%VERSIONS_DIR%" mkdir "%VERSIONS_DIR%"

for %%f in (dist\*) do (
    echo Uploading: %%f
    
    twine upload "%%f"
    
    if %errorlevel% equ 0 (
        echo ✓ Success. Moving %%~nxf to %VERSIONS_DIR%\
        move "%%f" "%VERSIONS_DIR%\"
    ) else (
        echo ✗ Failed. %%~nxf kept in dist\
    )
)