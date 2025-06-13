@echo off
SETLOCAL


REM Clean old build folders
echo Cleaning previous build...
rmdir /s /q build
rmdir /s /q dist

echo.
echo Building MIDI Chord App using PyInstaller...
echo ----------------------------------------------

REM Go to the root project directory
CD /D %~dp0

REM Make sure pyinstaller is available
where pyinstaller >nul 2>&1
IF ERRORLEVEL 1 (
    echo  PyInstaller not found. Please install it first:
    echo     pip install pyinstaller
    pause
    exit /b 1
)

REM Run PyInstaller with your .spec file
pyinstaller pyinstaller\midi_chord_app.spec --clean

IF ERRORLEVEL 1 (
    echo  Build failed.
    pause
    exit /b 1
)

echo.
echo  Build completed successfully!
echo  Check the dist\midi_chord_app\ folder.
echo.

pause
ENDLOCAL
