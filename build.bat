@echo off
SETLOCAL

echo ========================================
echo  MIDI Chord Detector - Build Script
echo ========================================
echo.

REM Clean old build folders
echo [1/6] Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [2/6] Checking dependencies...
echo ----------------------------------------------

REM Go to the root project directory
CD /D %~dp0

REM Check if pyinstaller is available
where pyinstaller >nul 2>&1
IF ERRORLEVEL 1 (
    echo ERROR: PyInstaller not found. Please install it first:
    echo     pip install pyinstaller
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking required Python packages...
python -c "import PyQt6; print('✓ PyQt6 found')" 2>nul || (
    echo ERROR: PyQt6 not found. Please install:
    echo     pip install PyQt6
    pause
    exit /b 1
)

python -c "import mido; print('✓ mido found')" 2>nul || (
    echo ERROR: mido not found. Please install:
    echo     pip install mido python-rtmidi
    pause
    exit /b 1
)

python -c "import rtmidi; print('✓ python-rtmidi found')" 2>nul || (
    echo ERROR: python-rtmidi not found. Please install:
    echo     pip install python-rtmidi
    pause
    exit /b 1
)

python -c "import zmq; print('✓ pyzmq found')" 2>nul || (
    echo WARNING: pyzmq not found. Install for full functionality:
    echo     pip install pyzmq
)

echo [3/6] Verifying data files...
if not exist "data\chord_definitions.json" (
    echo ERROR: Basic chord definitions not found!
    pause
    exit /b 1
)
if not exist "data\enhanced_chord_definitions.json" (
    echo ERROR: Enhanced chord definitions not found!
    pause
    exit /b 1
)
echo ✓ All data files found

echo [4/6] Verifying core modules...
if not exist "core\chord_recognition_engine.py" (
    echo ERROR: Core recognition engine not found!
    pause
    exit /b 1
)
if not exist "core\advanced_chord_analyzer.py" (
    echo ERROR: Advanced chord analyzer not found!
    pause
    exit /b 1
)
if not exist "core\music_theory.py" (
    echo ERROR: Music theory module not found!
    pause
    exit /b 1
)
if not exist "core\chord_config.py" (
    echo ERROR: Chord configuration module not found!
    pause
    exit /b 1
)
echo ✓ All core modules found

echo [5/6] Building application with PyInstaller...
echo ----------------------------------------------

REM Run PyInstaller with your .spec file
pyinstaller pyinstaller\midi_chord_app.spec --clean --noconfirm

IF ERRORLEVEL 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for error details.
    pause
    exit /b 1
)

echo [6/6] Verifying build output...
echo ----------------------------------------------
if not exist "dist\midi_chord_app\midi_chord_app.exe" (
    echo ERROR: Executable not found in dist folder!
    pause
    exit /b 1
)

if not exist "dist\midi_chord_app\data\chord_definitions.json" (
    echo ERROR: Basic chord definitions not bundled!
    pause
    exit /b 1
)

if not exist "dist\midi_chord_app\data\enhanced_chord_definitions.json" (
    echo ERROR: Enhanced chord definitions not bundled!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  BUILD COMPLETED SUCCESSFULLY! 🎉
echo ========================================
echo.
echo ✓ Executable: dist\midi_chord_app\midi_chord_app.exe
echo ✓ Data files: dist\midi_chord_app\data\
echo ✓ All dependencies bundled
echo.
echo You can now run the application from:
echo   dist\midi_chord_app\midi_chord_app.exe
echo.
echo Or copy the entire 'dist\midi_chord_app\' folder
echo to distribute your application.
echo.
echo 📝 Note: Make sure you have MIDI devices connected
echo    before running the application for full functionality.
echo.

REM Create a quick launch script
echo @echo off > dist\midi_chord_app\launch.bat
echo echo Starting MIDI Chord Detector... >> dist\midi_chord_app\launch.bat
echo midi_chord_app.exe >> dist\midi_chord_app\launch.bat
echo if ERRORLEVEL 1 pause >> dist\midi_chord_app\launch.bat

echo ✓ Quick launch script created: dist\midi_chord_app\launch.bat
echo.

pause
ENDLOCAL
