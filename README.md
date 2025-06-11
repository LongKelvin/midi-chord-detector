# Real-Time MIDI Chord Detection Project

This project provides a Python-based system for real-time MIDI chord detection, featuring a core library for processing MIDI input, a PyQt5 GUI for displaying detected chords, and a simulator for testing without a physical MIDI device. It is designed for Windows but should work cross-platform with minor adjustments.

## Features
- **Core Library**: Processes MIDI input to detect chords, supporting dyads, triads, seventh chords, and extended chords, with customizable definitions.
- **GUI Application**: Displays chord names in real-time, with a dropdown to select MIDI input devices and a start/stop button.
- **Virtual MIDI Simulator**: Creates a virtual MIDI port and sends simulated chord sequences for testing without hardware.
- **Chord Definitions**: JSON-based configuration for flexible chord types.

## Prerequisites
- **Python**: Version 3.8 or higher.
- **Operating System**: Windows (tested on Windows 10/11).
- **Dependencies**:
  - `mido`: For MIDI input/output handling.
  - `python-rtmidi`: Backend for `mido`.
  - `PyQt5`: For the GUI interface.
  - Install via:
    ```bash
    pip install mido python-rtmidi PyQt5
    ```

## Project Structure
- `midi_chord_recognizer.py`: Core library for MIDI chord detection.
- `midi_chord_gui.py`: PyQt5 GUI application for real-time chord display.
- `chord_definitions.json`: JSON file defining chord types and intervals.
- `midi_simulator.py`: Script to simulate a virtual MIDI device for testing.

## Setup Instructions

### 1. Clone or Download the Project
- Download the project files or clone the repository to a local directory.
- Ensure all four files (`midi_chord_recognizer.py`, `midi_chord_gui.py`, `chord_definitions.json`, `midi_simulator.py`) are in the same directory.

### 2. Install Dependencies
- Open a terminal in the project directory.
- Install required Python packages:
  ```bash
  pip install mido python-rtmidi PyQt5
  ```

### 3. Verify MIDI Backend
- Ensure `mido` uses the `rtmidi` backend:
  ```bash
  python -c "import mido; print(mido.backend)"
  ```
- Expected output: `<module 'mido.backends.rtmidi' ...>`.
- If not, set the environment variable:
  ```bash
  set MIDO_BACKEND=rtmidi
  ```

### 4. Prepare Chord Definitions
- The `chord_definitions.json` file is pre-configured with a comprehensive set of chords (dyads, triads, seventh chords, etc.).
- Customize it by editing the JSON to add or modify chord types (see "Customizing Chord Definitions" below).
- Ensure the file is in the project directory.

## Running the Application

### Option 1: Using a Physical MIDI Device
1. **Connect a MIDI Device**:
   - Plug in a MIDI keyboard or controller.
   - Check available MIDI ports:
     ```bash
     python -c "import mido; print(mido.get_input_names())"
     ```
2. **Run the GUI**:
   ```bash
   python midi_chord_gui.py
   ```
   - In the GUI:
     - Select your MIDI device from the dropdown (e.g., "MIDI Keyboard").
     - Click "Start Detection".
     - Play chords on the keyboard; the chord name (e.g., "Cmaj", "G7") appears in real-time.
     - Click "Stop Detection" to pause or close the window to exit.

### Option 2: Using the Virtual MIDI Simulator
1. **Run the Simulator**:
   ```bash
   python midi_simulator.py
   ```
   - The script creates a virtual MIDI port named "Virtual MIDI" and sends a sequence of chords (Cmaj, G7, Amin, pause).
   - It waits 2 seconds before starting to allow time to launch the GUI.
2. **Run the GUI** (in a separate terminal, within 2 seconds):
   ```bash
   python midi_chord_gui.py
   ```
   - In the GUI:
     - Select "Virtual MIDI" from the dropdown (refreshed every 5 seconds).
     - Click "Start Detection".
     - The chord label updates to show "Cmaj", "G7", "Amin", and "N.C.", each lasting ~1 second with a blue flash.
     - Close the window to stop.
3. **Stop the Simulator**:
   - Press `Ctrl+C` in the simulator terminal or wait for the sequence to complete.

## Example Output
- **GUI**:
  - Chord label shows: "Cmaj" → "G7" → "Amin" → "N.C." (with blue flash on updates).
  - Status bar shows "Running" or "Stopped".
- **Simulator Log**:
  ```
  2025-06-11 19:31:01,123 - __main__ - INFO - Created virtual MIDI output port: Virtual MIDI
  2025-06-11 19:31:03,126 - __main__ - INFO - Playing chord: [60, 64, 67]
  2025-06-11 19:31:04,226 - __main__ - INFO - Playing chord: [55, 59, 62, 65]
  ...
  ```
- **GUI Log** (if debug enabled in `midi_chord_recognizer.py`):
  ```
  2025-06-11 19:31:03,200 - __main__ - INFO - Chord detection started
  2025-06-11 19:31:03,210 - __main__ - DEBUG - Chord updated: Cmaj
  ...
  ```

## Customizing Chord Definitions
- Edit `chord_definitions.json` to add or modify chords.
- Example entry:
  ```json
  "maj9": {
    "name": "Major 9th",
    "intervals": [0, 4, 7, 11, 14]
  }
  ```
- Each chord has a `name` (display name) and `intervals` (semitones from the root).
- Save changes and restart the GUI to apply.

## Performance Notes
- **Latency**: ~17–18ms (15ms buffer + ~2–3ms processing), suitable for real-time use.
- **CPU/Memory**: Lightweight (<10MB memory, <5% CPU on modern hardware).
- **Tuning**:
  - Reduce `chord_buffer_time` in `midi_chord_gui.py` (e.g., to 0.01) for lower latency, but this may affect chord grouping accuracy.
  - Adjust `min_notes_for_chord` or `confidence_threshold` in `midi_chord_recognizer.py` for specific musical styles.

## Troubleshooting
- **No MIDI Devices**:
  - Ensure `python-rtmidi` is installed and `rtmidi` is the backend.
  - For the simulator, run it first to create the "Virtual MIDI" port.
- **No Chord Updates**:
  - Verify the GUI is "Running" and the correct MIDI port is selected.
  - Check simulator logs to ensure messages are sent.
- **Port Not Found**:
  - Run `python -c "import mido; print(mido.get_input_names())"` while the simulator is active.
  - Try a different port name in `midi_simulator.py` (e.g., "My Virtual MIDI").
- **Errors**:
  - Enable debug logging by modifying `midi_chord_recognizer.py`:
    ```python
    logging.basicConfig(level=logging.DEBUG)
    ```

## Extending the Project
- **Add Chord Progression Display**: Modify `midi_chord_gui.py` to show the chord progression from `recognizer.get_current_status()['progression']`.
- **Interactive Simulator**: Extend `midi_simulator.py` to accept user input for real-time chord simulation.
- **MIDI File Input**: Add support in `midi_simulator.py` to read MIDI files for complex sequences.

## License
This project is provided for educational purposes under the MIT License. See `LICENSE` file (if included) for details.

## Contact
- For issues or feature requests, contact the maintainers or open a GitHub issue.

---
*Generated on June 15, 2025*