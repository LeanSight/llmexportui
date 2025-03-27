@echo off
setlocal

REM Check if a path was provided as a parameter
if "%~1"=="" (
    echo No executable path provided.
    echo Usage: %~nx0 [path_to_executable]
    echo.
    echo Examples:
    echo %~nx0 "C:\Applications\LLMExportTool.exe"
    echo %~nx0 .\LLMExportTool.exe
    goto :EOF
)

REM Get the full path of the executable
set "EXE_PATH=%~f1"

REM Verify if the file exists
if not exist "%EXE_PATH%" (
    echo ERROR: File does not exist: %EXE_PATH%
    echo Please provide a valid path to the executable.
    goto :EOF
)

REM Escape backslashes for the registry
set "REG_PATH=%EXE_PATH:\=\\%"

echo Preparing to register: %EXE_PATH%

REM Create temporary .reg file
echo Windows Registry Editor Version 5.00 > "%TEMP%\llmexport_update.reg"
echo. >> "%TEMP%\llmexport_update.reg"
echo [HKEY_CLASSES_ROOT\Directory\shell\LLMExport] >> "%TEMP%\llmexport_update.reg"
echo @="Export for LLM" >> "%TEMP%\llmexport_update.reg"
echo "Icon"="\"%REG_PATH%\"" >> "%TEMP%\llmexport_update.reg"
echo. >> "%TEMP%\llmexport_update.reg"
echo [HKEY_CLASSES_ROOT\Directory\shell\LLMExport\command] >> "%TEMP%\llmexport_update.reg"
echo @="\"%REG_PATH%\" \"%%1\"" >> "%TEMP%\llmexport_update.reg"

REM Import the .reg file
regedit /s "%TEMP%\llmexport_update.reg"

REM Verify if the operation was successful
if %ERRORLEVEL% EQU 0 (
    echo Registry successfully updated.
    echo The LLMExportTool application is now registered at location:
    echo %EXE_PATH%
) else (
    echo Error updating registry.
)

REM Delete the temporary file
del "%TEMP%\llmexport_update.reg"

REM Pause so the user can see the result
pause