import sys
from typing import Dict, Optional
import mido
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QComboBox, QLabel, QGridLayout, QFrame, QSizePolicy, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

 

from ui.piano_keyboard_window import PianoKeyboardWidget
from ui.workers.midi_worker import MIDIWorkerThread

# Assume your 'midi_chord_recognize_final.py' is saved as 'midi_recognizer_engine.py'
# and we can import MIDIChordRecognizer and ChordTheory from it.
# If not, you'd copy those classes here or adjust imports.
try:
    from core.chord_recognition_engine import MIDIChordRecognizer, ChordTheory, DEFAULT_CHORD_CONFIG_PATH
except ImportError:
    print("ERROR: Could not import 'midi_recognizer_engine'. Make sure it's in the same directory or Python path.")
    print("You might need to copy the MIDIChordRecognizer and ChordTheory classes here.")
    sys.exit(1)


# --- Main Application Window ---
class ChordAppMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-time MIDI Chord Display")
        self.setGeometry(100, 100, 900, 700) # Increased size for keyboard

        self.recognizer_thread: Optional[MIDIWorkerThread] = None
        self.piano_keyboard_widget: Optional[PianoKeyboardWidget] = None

        # --- Styling (Simple Example) ---
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2E2E2E; /* Dark gray background */
            }
            QLabel {
                color: #E0E0E0; /* Light gray text */
                font-size: 11pt;
            }
            QComboBox {
                font-size: 10pt;
                padding: 5px;
            }
            QFrame#chordDisplayFrame {
                border: 1px solid #555555;
                border-radius: 5px;
                background-color: #3A3A3A;
            }
            QLabel#chordNameLabel {
                font-size: 32pt;
                font-weight: bold;
                color: #4CAF50; /* Green for chord name */
                padding: 10px;
                border-bottom: 1px solid #555555;
            }
            QLabel#statusLabel {
                font-size: 9pt;
                color: #AAAAAA;
            }
            QTextEdit#detailsTextEdit {
                background-color: #333333;
                color: #D0D0D0;
                border: 1px solid #444444;
                font-family: Consolas, Courier New, monospace;
                font-size: 10pt;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self._setup_ui()
        self._populate_midi_ports()

        # Timer to periodically check for new MIDI ports (e.g., if a device is plugged in later)
        self.port_scan_timer = QTimer(self)
        self.port_scan_timer.timeout.connect(self._check_and_repopulate_midi_ports)
        self.port_scan_timer.start(5000) # Check every 5 seconds

    def _setup_ui(self):
        # MIDI Port Selection
        self.midi_port_combo = QComboBox()
        self.midi_port_combo.setPlaceholderText("Select MIDI Input Device")
        self.midi_port_combo.activated.connect(self.on_midi_port_selected) # Use activated for user selection
        self.layout.addWidget(self.midi_port_combo)

        # Chord Display Area
        chord_display_frame = QFrame()
        chord_display_frame.setObjectName("chordDisplayFrame") # For styling
        chord_display_frame.setFrameShape(QFrame.Shape.StyledPanel)
        chord_display_layout = QVBoxLayout(chord_display_frame)

        self.chord_name_label = QLabel("N.C.")
        self.chord_name_label.setObjectName("chordNameLabel")
        self.chord_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chord_display_layout.addWidget(self.chord_name_label)

        # Grid for detailed info
        self.details_grid_layout = QGridLayout()
        self.details_labels: Dict[str, QLabel] = {}
        
        details_to_show = [
            ("Root:", "---"), ("Bass:", "---"), ("Type:", "---"),
            ("Inversion:", "---"), ("Score:", "---"),
            ("Voicing:", "---"), ("Octave Span:", "---")
        ]

        row = 0
        for i, (label_text, val_text) in enumerate(details_to_show):
            lbl = QLabel(label_text)
            val_lbl = QLabel(val_text)
            val_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold)) # Make value bold
            self.details_labels[label_text.replace(":", "").lower().replace(" ", "_")] = val_lbl
            self.details_grid_layout.addWidget(lbl, row, 0)
            self.details_grid_layout.addWidget(val_lbl, row, 1)
            row +=1
        
        chord_display_layout.addLayout(self.details_grid_layout)
        
        # TextEdit for played notes and intervals (more flexible for varying amounts of text)
        self.details_text_edit = QTextEdit()
        self.details_text_edit.setObjectName("detailsTextEdit")
        self.details_text_edit.setReadOnly(True)
        self.details_text_edit.setFixedHeight(150) # Adjust as needed
        chord_display_layout.addWidget(self.details_text_edit)

        self.layout.addWidget(chord_display_frame)

        # --- Piano Keyboard Widget ---
        self.piano_keyboard_widget = PianoKeyboardWidget(self)
        self.piano_keyboard_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed) # Fixed height
        # self.piano_keyboard_widget.setFixedHeight(150) # Or let PianoKeyboardWidget set its own height
        self.layout.addWidget(self.piano_keyboard_widget) # Add it to the main layout

        # Status Label
        self.status_label = QLabel("App Initialized. Select a MIDI port.")
        self.status_label.setObjectName("statusLabel")
        self.layout.addWidget(self.status_label)
        
        # Placeholder for future Piano Keyboard / Staff
        # piano_placeholder = QLabel("Piano Keyboard / Staff Area (Future)")
        # piano_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # piano_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # piano_placeholder.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)
        # self.layout.addWidget(piano_placeholder)


    def _populate_midi_ports(self, selected_port_name: Optional[str] = None):
        current_selection = selected_port_name if selected_port_name else self.midi_port_combo.currentText()
        self.midi_port_combo.blockSignals(True) # Avoid triggering signal during repopulation
        self.midi_port_combo.clear()
        self.midi_port_combo.addItem("Select MIDI Input Device")
        try:
            ports = mido.get_input_names()
            if ports:
                self.midi_port_combo.addItems(ports)
                if current_selection and current_selection in ports:
                    self.midi_port_combo.setCurrentText(current_selection)
                elif selected_port_name and selected_port_name in ports: # If a specific port was requested
                     self.midi_port_combo.setCurrentText(selected_port_name)
            else:
                self.status_label.setText("No MIDI input devices found.")
        except Exception as e:
            self.status_label.setText(f"Error listing MIDI ports: {e}")
            print(f"Error listing MIDI ports: {e}")
        self.midi_port_combo.blockSignals(False)

    def _check_and_repopulate_midi_ports(self):
        # Only repopulate if the recognizer is not active or if the port list changed
        if self.recognizer_thread and self.recognizer_thread.isRunning():
            return 

        current_ports_in_combo = [self.midi_port_combo.itemText(i) for i in range(1, self.midi_port_combo.count())]
        try:
            actual_ports = mido.get_input_names()
            if set(current_ports_in_combo) != set(actual_ports):
                self.status_label.setText("MIDI port list changed. Repopulating...")
                self._populate_midi_ports()
        except Exception as e:
            print(f"Error during periodic MIDI port check: {e}")


    def on_midi_port_selected(self, index: int):
        if index == 0: # "Select MIDI Input Device" placeholder
            if self.recognizer_thread and self.recognizer_thread.isRunning():
                self.recognizer_thread.stop_recognizer()
            self.status_label.setText("Please select a MIDI port.")
            self._reset_chord_display()
            return

        port_name = self.midi_port_combo.itemText(index)
        self.status_label.setText(f"Selected MIDI port: {port_name}. Starting recognizer...")

        if self.recognizer_thread and self.recognizer_thread.isRunning():
            self.recognizer_thread.stop_recognizer()
            # Give it a moment to fully stop before starting a new one
            QTimer.singleShot(200, lambda: self._start_recognizer_for_port(port_name))
        else:
            self._start_recognizer_for_port(port_name)

    def _start_recognizer_for_port(self, port_name: str):
        self.recognizer_thread = MIDIWorkerThread(
            config_path=DEFAULT_CHORD_CONFIG_PATH, # Or from an app setting
            min_notes=2, # Or from an app setting
            buffer_time=0.015 # Or from an app setting
        )
        self.recognizer_thread.set_midi_port(port_name)
        self.recognizer_thread.signals.chord_updated.connect(self.update_chord_display)
        self.recognizer_thread.signals.midi_ports_listed.connect(
            lambda ports: self._populate_midi_ports(selected_port_name=port_name if port_name in ports else None)
        ) # If it lists ports, repopulate
        self.recognizer_thread.signals.recognizer_status.connect(
            lambda status_msg: self.status_label.setText(status_msg)
        )
        self.recognizer_thread.finished.connect(lambda: self.status_label.setText("Recognizer thread finished."))
        
        self._reset_chord_display() # Clear display before starting
        self.recognizer_thread.start()


    def _reset_chord_display(self):
        self.chord_name_label.setText("N.C.")
        self.chord_name_label.setStyleSheet("color: #E0E0E0;") # Reset color
        
        default_val = "---"
        self.details_labels["root"].setText(default_val)
        self.details_labels["bass"].setText(default_val)
        self.details_labels["type"].setText(default_val)
        self.details_labels["inversion"].setText(default_val)
        self.details_labels["score"].setText(default_val)
        self.details_labels["voicing"].setText(default_val)
        self.details_labels["octave_span"].setText(default_val)
        self.details_text_edit.setHtml("")

        if self.piano_keyboard_widget:
            self.piano_keyboard_widget.update_active_notes([]) # Clear all pressed keys


    def update_chord_display(self, chord_data: dict):
        #print(f"UI received chord data: {chord_data}") # For debugging
        
        full_name = chord_data.get('full_chord_name', "N.C.")
        self.chord_name_label.setText(full_name)
        
        if full_name != "N.C." and chord_data.get('score', 0) > 0:
            self.chord_name_label.setStyleSheet("color: #4CAF50;") # Green for recognized chord
        else:
            self.chord_name_label.setStyleSheet("color: #E0E0E0;") # Default color for N.C.

        self.details_labels["root"].setText(chord_data.get('root_note_name', "---"))
        self.details_labels["bass"].setText(chord_data.get('bass_note_name', "---"))
        self.details_labels["type"].setText(chord_data.get('chord_type', "---"))
        self.details_labels["inversion"].setText(chord_data.get('inversion_type', "---"))
        
        score = chord_data.get('score', 0.0)
        self.details_labels["score"].setText(f"{score:.2f}" if score > 0 else "---")
        
        self.details_labels["voicing"].setText(chord_data.get('voicing_density_description', "---"))
        self.details_labels["octave_span"].setText(str(chord_data.get('octave_span_played_notes', "---")))

        # --- Populate TextEdit with more details ---
        html_content = ""
        notes_midi = chord_data.get('played_notes_midi', [])
        if notes_midi:
            note_names = [f"{ChordTheory.midi_to_pitch_class_name(n)}{n//12 - 1}({n})" for n in notes_midi] # C4(60)
            html_content += f"<p><b>Played Notes:</b> {', '.join(note_names)}</p>"
        
        if full_name != "N.C.":
            pcs = chord_data.get('played_pitch_classes', [])
            html_content += f"<p><b>Pitch Classes:</b> {pcs}</p>"
            
            all_rel_root = chord_data.get('all_played_intervals_rel_to_root', [])
            all_rel_root_names = [ChordTheory.interval_to_name(i, use_extended_names=True) for i in all_rel_root]
            html_content += f"<p><b>Intervals (from Root {chord_data.get('root_note_name', '')}):</b> {all_rel_root} <i>({', '.join(all_rel_root_names)})</i></p>"

            extra_rel_root = chord_data.get('extra_played_intervals_rel_to_root', [])
            if extra_rel_root:
                extra_names = [ChordTheory.interval_to_name(i, use_extended_names=True) for i in extra_rel_root]
                html_content += f"<p><b>Extra Intervals (from Root):</b> {extra_rel_root} <i>({', '.join(extra_names)})</i></p>"

            intervals_from_bass = chord_data.get('intervals_from_actual_bass_pc', [])
            intervals_from_bass_names = [ChordTheory.interval_to_name(i) for i in intervals_from_bass]
            html_content += f"<p><b>Intervals (from Bass {chord_data.get('bass_note_name', '')}):</b> {intervals_from_bass} <i>({', '.join(intervals_from_bass_names)})</i></p>"

        self.details_text_edit.setHtml(f"<div>{html_content}</div>")

        # Update Piano Keyboard
        if self.piano_keyboard_widget:
            played_notes_midi = chord_data.get('played_notes_midi', [])
            self.piano_keyboard_widget.update_active_notes(played_notes_midi)


    def closeEvent(self, event):
        self.port_scan_timer.stop()
        if self.recognizer_thread and self.recognizer_thread.isRunning():
            self.status_label.setText("Closing... Stopping recognizer thread.")
            self.recognizer_thread.stop_recognizer()
        super().closeEvent(event)
