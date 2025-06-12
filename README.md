
# Real-Time MIDI Chord Suite

This project provides a Python-based system for real-time MIDI chord detection and visualization. It features a core engine for processing MIDI input, a PyQt6 GUI for displaying detected chords and live piano keyboard activity.

## Features
- **Core Engine**: `ChordRecognitionEngine` processes MIDI input to detect a wide range of chords (dyads, triads, sevenths, extensions, alterations) with high accuracy.
- **Music Theory Module**: `MusicTheory` class encapsulates chord definitions and interval logic, configurable via JSON.
- **PyQt6 GUI Application**:
    - Real-time display of detailed chord information (name, root, bass, type, inversion, score).
    - Interactive 88-key `PianoKeyboard` visualizing live MIDI input.
    - Dropdown to select MIDI input devices.
    - Start/Stop functionality for chord detection (achieved by selecting/deselecting a port).
- **Configurable Chord Definitions**: `chord_definitions.json` allows for easy customization and expansion of recognizable chords.

## Prerequisites
- **Python**: Version 3.8 or higher.
- **Operating System**: Tested on Windows 10/11, but designed to be cross-platform.
- **Dependencies**:
  - `mido`: For MIDI input/output handling.
  - `python-rtmidi`: Recommended backend for `mido` on Windows/Linux.
  - `PyQt6`: For the GUI interface.
  - Install core dependencies via:
    ```bash
    pip install mido python-rtmidi PyQt6
    ```

## Project Structure

The project is organized into modular packages for better maintainability and separation of concerns:

```bash
midi-chord-suite/
├── chord_app.py                # Main application entry point (Initializes PyQt GUI)
│
├── core/                       # Core non-GUI logic
│   ├── __init__.py             # Makes 'core' a Python package
│   ├── chord_recognition_engine.py  # Contains ChordRecognitionEngine class
│   └── music_theory.py              # Contains MusicTheory class (definitions, interval logic)
│
├── ui/                         # User Interface components (PyQt6)
│   ├── __init__.py             # Makes 'ui' a Python package
│   ├── main_window.py          # Contains MainWindow class (main application window)
│   ├── piano_keyboard.py       # Contains PianoKeyboard and PianoKey custom widget classes
│   ├── workers/                # Contains EngineWorkerThread (QThread for MIDI processing)
│   │                             # and EngineSignals (custom Qt signals)
│   └── resources/              # Optional: For UI assets like QSS stylesheets, icons
│       └── style.qss           # Example stylesheet
│
├── data/                       # Default data files
│   └── chord_definitions.json  # JSON file for chord definitions, loaded by MusicTheory
│                
├── .gitignore                  # Specifies intentionally untracked files for Git
├── README.md                   # This file: Project overview and instructions
  ```

## Setup Instructions

### 1. Clone or Download the Project
- Obtain the project files, ensuring the directory structure outlined above is maintained.

### 2. Create and Activate a Virtual Environment (Recommended)
```bash
# Navigate to the project root directory (midi-chord-suite)
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
# source venv/bin/activate
```

### 3. Install Dependencies
- With your virtual environment activated, install the required Python packages from `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```
  (If `requirements.txt` is not yet created, install manually: `pip install mido python-rtmidi PyQt6`)

### 4. Verify MIDI Backend (Optional)
- `mido` typically uses `rtmidi` as its backend. You can check by running:
  ```bash
  python -c "import mido; print(mido.backend)"
  ```
- If a different backend is shown and you encounter issues, you might need to set the `MIDO_BACKEND` environment variable (e.g., `set MIDO_BACKEND=rtmidi` on Windows CMD before running the app).

### 5. Chord Definitions
- The `data/chord_definitions.json` file should be present and contains a comprehensive set of chord definitions.
- This file is loaded by the `MusicTheory` module at startup.

## Running the Application

1.  **Navigate to the Project Root**: Open your terminal or command prompt and change the directory to where `chord_app.py` is located (the root of `midi-chord-suite`).
2.  **Ensure Virtual Environment is Active** (if you created one).
3.  **Launch the Application**:
    ```bash
    python chord_app.py
    ```
    You can also pass command-line arguments (e.g., for log level, default MIDI port if implemented):
    ```bash
    python chord_app.py --log-level DEBUG --midi-port "Your MIDI Device Name"
    ```
    Use `python chord_app.py --list-midi-ports` to see available MIDI inputs.

4.  **Using the GUI**:
    -   Upon launch, the main window will appear.
    -   Use the "Select MIDI Input Device" dropdown to choose your connected MIDI keyboard or controller.
    -   Once a device is selected, the application automatically starts listening.
    -   Play notes or chords on your MIDI device.
    -   The "Chord Display" area will update in real-time with detailed information about the recognized chord.
    -   The virtual "Piano Keyboard" at the bottom of the window will visually highlight the keys being played.
    -   To stop detection for a specific port, select the placeholder "Select MIDI Input Device" from the dropdown.
    -   Close the application window to exit completely. The status bar provides operational feedback.

## GUI Features
- **MIDI Device Selection**: Dynamically populated dropdown lists all available MIDI input ports.
- **Real-Time Chord Display**:
    - Prominent display of the full recognized chord name (e.g., "Cmaj9/E").
    - Detailed breakdown: Root note, Bass note, Chord Type, Inversion (e.g., "1st Inversion", "Root Position"), and Recognition Score.
    - Voicing characteristics: Density (e.g., "Close Voicing") and octave span of played notes.
    - Lists of played MIDI notes (with numbers and names) and unique pitch classes.
    - Intervals of played notes relative to the recognized root and also relative to the actual bass note.
- **Live Piano Keyboard**: An 88-key visual piano representation that highlights keys in real-time as they are pressed on the MIDI input device.
- **Status Bar**: Displays messages about the application's current state, selected MIDI port, and any errors.
- **Styling**: Basic dark theme implemented with potential for further customization via QSS (`ui/resources/style.qss`).

## Customizing Chord Definitions
- Modify the `data/chord_definitions.json` file to add, remove, or alter chord types.
- The JSON structure for each chord is:
  ```json
  "chord_symbol": {
    "name": "Descriptive Chord Name",
    "intervals": [/* list of semitone intervals from the root, e.g., 0, 4, 7 for major */]
  }
  ```
- Example:
  ```json
  "min7b5": {
    "name": "Half-Diminished 7th",
    "intervals": [0, 3, 6, 10]
  }
  ```
- The application loads these definitions when it starts. Restart the application to apply any changes made to this file.

## Performance Considerations
- **Latency**: The system aims for low latency. The `chord_buffer_time_on` (default ~15ms) in the `ChordRecognitionEngine` provides a brief window for notes of a chord to arrive together before analysis. Piano key visualization is intended to be as immediate as possible.
- **Resource Usage**: Designed to be relatively lightweight. CPU and memory usage will vary with system specifications and the complexity of MIDI input.

## Troubleshooting
- **No MIDI Devices in Dropdown**:
    - Ensure your MIDI device is connected *before* starting the application, or wait for the periodic port scan (every 5 seconds) to update the list.
    - Verify `python-rtmidi` is installed and functioning as a `mido` backend.
    - Check your operating system's sound/MIDI settings to confirm the device is recognized.
- **Application Not Responding or No Updates**:
    - Ensure the correct MIDI port is selected.
    - Check the status bar for any error messages.
    - Run the application from a terminal to see console output, especially if you set a more verbose log level (e.g., `python chord_app.py --log-level DEBUG`).
- **Errors During Startup or Operation**:
    - Confirm all dependencies listed in `requirements.txt` are installed in your active Python environment.
    - Ensure `data/chord_definitions.json` is present in the correct location and contains valid JSON.
    - Look for error messages in the console output.


## License
This project is typically provided under a permissive open-source license like MIT (check for a `LICENSE` file in the repository). For this example, assume it's for educational and personal use.

## Contact / Contributions
For feedback, bug reports, or if you wish to contribute, please refer to the project's source repository (if applicable) for issue tracking and contribution guidelines.

## Author: Long Kelvin ##
