import sys
from typing import Dict, Optional
import mido
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QComboBox, QLabel, QGridLayout, 
    QFrame, QSizePolicy, QTextEdit, QHBoxLayout, QCheckBox, QPushButton, QGroupBox,
    QDialog, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPainter, QPen, QTransform

 

from ui.piano_keyboard_window import PianoKeyboardWidget
from ui.workers.midi_worker import MIDIWorkerThread

# Custom spinning loading widget
class SpinningLoader(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        self.setFixedSize(40, 40)
        
    def start_spinning(self):
        self.timer.start(50)  # Update every 50ms for smooth animation
        self.show()
        
    def stop_spinning(self):
        self.timer.stop()
        self.hide()
        
    def rotate(self):
        self.angle = (self.angle + 15) % 360  # Rotate 15 degrees each update
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Set up the pen
        pen = QPen(Qt.GlobalColor.white, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Move to center and rotate
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        
        # Draw spinning arcs
        for i in range(8):
            alpha = 255 - (i * 30)  # Fade effect
            if alpha < 0:
                alpha = 0
            pen.setColor(QColor(255, 255, 255, alpha))
            painter.setPen(pen)
            
            painter.drawLine(0, -15, 0, -10)
            painter.rotate(45)  # 360/8 = 45 degrees between lines

# Custom loading dialog with spinner
class LoadingDialog(QDialog):
    def __init__(self, message="Loading...", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing")
        self.setModal(True)
        self.setFixedSize(250, 100)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        
        # Center the dialog
        if parent:
            parent_geo = parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - self.width()) // 2
            y = parent_geo.y() + (parent_geo.height() - self.height()) // 2
            self.setGeometry(x, y, self.width(), self.height())
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Spinner
        self.spinner = SpinningLoader()
        layout.addWidget(self.spinner)
        
        # Message label
        self.message_label = QLabel(message)
        self.message_label.setStyleSheet("color: white; font-size: 12pt;")
        layout.addWidget(self.message_label)
        
        # Style the dialog
        self.setStyleSheet("""
            QDialog {
                background-color: #2E2E2E;
                border: 2px solid #555555;
                border-radius: 10px;
            }
        """)
        
    def show_loading(self, message=None):
        if message:
            self.message_label.setText(message)
        self.spinner.start_spinning()
        self.show()
        QApplication.processEvents()
        
    def close_loading(self):
        self.spinner.stop_spinning()
        self.close()

# Add QColor import
from PyQt6.QtGui import QFont, QPainter, QPen, QTransform, QColor

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
        self.loading_dialog: Optional[LoadingDialog] = None

        # --- Styling ---
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

        # Advanced Analyzer Controls
        self._setup_analyzer_controls()

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

    def _setup_analyzer_controls(self):
        """Setup controls for advanced chord analyzer"""
        analyzer_group = QGroupBox("Chord Analysis Settings")
        analyzer_layout = QVBoxLayout(analyzer_group)
        
        # Analyzer type selection
        analyzer_type_layout = QHBoxLayout()
        analyzer_type_layout.addWidget(QLabel("Analyzer:"))
        
        self.analyzer_combo = QComboBox()
        self.analyzer_combo.addItems(["Advanced (Enhanced)", "Basic (Traditional)"])
        self.analyzer_combo.setCurrentIndex(0)  # Default to advanced
        self.analyzer_combo.currentTextChanged.connect(self._on_analyzer_changed)
        analyzer_type_layout.addWidget(self.analyzer_combo)
        analyzer_layout.addLayout(analyzer_type_layout)
        
        # Advanced settings (only shown when advanced is selected)
        self.advanced_settings_widget = QWidget()
        advanced_settings_layout = QVBoxLayout(self.advanced_settings_widget)
        
        # Voice separation checkbox
        self.voice_separation_cb = QCheckBox("Enable Voice Separation (Bass/Chord/Melody)")
        self.voice_separation_cb.setChecked(True)
        self.voice_separation_cb.setToolTip("Separates bass, chord tones, and melody for better recognition")
        advanced_settings_layout.addWidget(self.voice_separation_cb)
        
        # Context analysis checkbox
        self.context_analysis_cb = QCheckBox("Enable Musical Context Analysis")
        self.context_analysis_cb.setChecked(True)
        self.context_analysis_cb.setToolTip("Considers chord progressions and voice leading for better accuracy")
        advanced_settings_layout.addWidget(self.context_analysis_cb)
        
        # Fuzzy matching checkbox
        self.fuzzy_matching_cb = QCheckBox("Enable Fuzzy Chord Matching")
        self.fuzzy_matching_cb.setChecked(True)
        self.fuzzy_matching_cb.setToolTip("Recognizes incomplete chords and jazz voicings")
        advanced_settings_layout.addWidget(self.fuzzy_matching_cb)
        
        analyzer_layout.addWidget(self.advanced_settings_widget)
        
        # Chord definitions selection
        definitions_layout = QHBoxLayout()
        definitions_layout.addWidget(QLabel("Chord Set:"))
        
        self.chord_definitions_combo = QComboBox()
        self.chord_definitions_combo.addItems(["Enhanced (Jazz/Advanced)", "Basic (Standard)"])
        self.chord_definitions_combo.setCurrentIndex(0)
        definitions_layout.addWidget(self.chord_definitions_combo)
        analyzer_layout.addLayout(definitions_layout)
        
        self.layout.addWidget(analyzer_group)
    
    def _on_analyzer_changed(self, text: str):
        """Handle analyzer type change"""
        is_advanced = "Advanced" in text
        self.advanced_settings_widget.setVisible(is_advanced)
        
        # If we have an active recognizer, restart it with new settings
        if self.recognizer_thread and self.recognizer_thread.isRunning():
            current_port = self.midi_port_combo.currentText()
            self._restart_recognizer_with_new_settings(current_port)
    
    def _restart_recognizer_with_new_settings(self, port_name: str):
        """Restart the recognizer with updated settings"""
        if self.recognizer_thread and self.recognizer_thread.isRunning():
            # Show spinning loader for restart
            self.loading_dialog = LoadingDialog("Restarting MIDI recognizer...", self)
            self.loading_dialog.show_loading()
            
            self.recognizer_thread.stop_recognizer()
            if not self.recognizer_thread.wait(3000):  # Wait up to 3 seconds
                self.loading_dialog.message_label.setText("Force stopping MIDI thread...")
                QApplication.processEvents()
                print("Warning: MIDI thread did not stop gracefully, forcing termination")
                self.recognizer_thread.terminate()
                self.recognizer_thread.wait(1000)  # Wait a bit more after termination
            
            self.loading_dialog.close_loading()
            self.loading_dialog = None
        
        # Start with new settings
        self._start_recognizer_for_port(port_name)


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
                # Show brief spinning loader for stopping
                self.loading_dialog = LoadingDialog("Stopping MIDI recognizer...", self)
                self.loading_dialog.show_loading()
                
                self.recognizer_thread.stop_recognizer()
                if not self.recognizer_thread.wait(2000):
                    self.loading_dialog.message_label.setText("Force stopping...")
                    QApplication.processEvents()
                    self.recognizer_thread.terminate()
                    self.recognizer_thread.wait(500)
                
                self.loading_dialog.close_loading()
                self.loading_dialog = None
                
            self.status_label.setText("Please select a MIDI port.")
            self._reset_chord_display()
            return

        port_name = self.midi_port_combo.itemText(index)
        self.status_label.setText(f"Selected MIDI port: {port_name}. Starting recognizer...")

        if self.recognizer_thread and self.recognizer_thread.isRunning():
            # Show spinning loader for switching ports
            self.loading_dialog = LoadingDialog("Switching MIDI port...", self)
            self.loading_dialog.show_loading()
            
            self.recognizer_thread.stop_recognizer()
            if not self.recognizer_thread.wait(2000):
                self.loading_dialog.message_label.setText("Force stopping current recognizer...")
                QApplication.processEvents()
                self.recognizer_thread.terminate()
                self.recognizer_thread.wait(500)
            
            self.loading_dialog.close_loading()
            self.loading_dialog = None
            
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
        confidence = chord_data.get('confidence', None)
        if confidence is not None:
            score_text = f"{score:.2f} (C:{confidence:.2f})"
        else:
            score_text = f"{score:.2f}" if score > 0 else "---"
        self.details_labels["score"].setText(score_text)
        
        self.details_labels["voicing"].setText(chord_data.get('voicing_density_description', "---"))
        self.details_labels["octave_span"].setText(str(chord_data.get('octave_span_played_notes', "---")))

        # --- Enhanced details with advanced analysis ---
        html_content = ""
        
        # Show analyzer type
        is_advanced = chord_data.get('advanced_analysis', False)
        analyzer_type = "Advanced Enhanced" if is_advanced else "Basic Traditional"
        html_content += f"<p><b>Analyzer:</b> {analyzer_type}</p>"
        
        notes_midi = chord_data.get('played_notes_midi', [])
        if notes_midi:
            note_names = [f"{ChordTheory.midi_to_pitch_class_name(n)}{n//12 - 1}({n})" for n in notes_midi]
            html_content += f"<p><b>Played Notes:</b> {', '.join(note_names)}</p>"
        
        # Advanced analysis specific information
        if is_advanced and full_name != "N.C.":
            # Voice separation info
            voice_sep = chord_data.get('voice_separation', {})
            if voice_sep:
                bass_notes = voice_sep.get('bass_notes', [])
                chord_notes = voice_sep.get('chord_notes', [])
                melody_notes = voice_sep.get('melody_notes', [])
                
                if bass_notes:
                    bass_names = [f"{ChordTheory.midi_to_pitch_class_name(n)}{n//12 - 1}" for n in bass_notes]
                    html_content += f"<p><b>Bass Voice:</b> {', '.join(bass_names)}</p>"
                
                if chord_notes:
                    chord_names = [f"{ChordTheory.midi_to_pitch_class_name(n)}{n//12 - 1}" for n in chord_notes]
                    html_content += f"<p><b>Chord Voice:</b> {', '.join(chord_names)}</p>"
                
                if melody_notes:
                    melody_names = [f"{ChordTheory.midi_to_pitch_class_name(n)}{n//12 - 1}" for n in melody_notes]
                    html_content += f"<p><b>Melody Voice:</b> {', '.join(melody_names)}</p>"
            
            # Analysis quality
            analysis_quality = chord_data.get('analysis_quality', {})
            if analysis_quality:
                missing = analysis_quality.get('missing_expected_intervals', [])
                extra = analysis_quality.get('extra_intervals', [])
                context_bonus = analysis_quality.get('context_bonus', 0)
                
                if missing:
                    html_content += f"<p><b>Missing Expected:</b> {missing}</p>"
                if extra:
                    html_content += f"<p><b>Extra Notes:</b> {extra}</p>"
                if context_bonus > 0:
                    html_content += f"<p><b>Context Bonus:</b> +{context_bonus:.3f}</p>"
            
            # Complexity level
            complexity = chord_data.get('complexity', '')
            if complexity:
                html_content += f"<p><b>Complexity:</b> {complexity}</p>"
        
        # Standard interval analysis
        if full_name != "N.C.":
            pcs = chord_data.get('played_pitch_classes', [])
            html_content += f"<p><b>Pitch Classes:</b> {pcs}</p>"
            
            all_rel_root = chord_data.get('all_played_intervals_rel_to_root', [])
            if all_rel_root:
                all_rel_root_names = [ChordTheory.interval_to_name(i, use_extended_names=True) for i in all_rel_root]
                html_content += f"<p><b>Intervals (from Root {chord_data.get('root_note_name', '')}):</b> {all_rel_root} <i>({', '.join(all_rel_root_names)})</i></p>"

            # Only show extra intervals for basic analysis (advanced shows this differently)
            if not is_advanced:
                extra_rel_root = chord_data.get('extra_played_intervals_rel_to_root', [])
                if extra_rel_root:
                    extra_names = [ChordTheory.interval_to_name(i, use_extended_names=True) for i in extra_rel_root]
                    html_content += f"<p><b>Extra Intervals (from Root):</b> {extra_rel_root} <i>({', '.join(extra_names)})</i></p>"

            intervals_from_bass = chord_data.get('intervals_from_actual_bass_pc', [])
            if intervals_from_bass:
                intervals_from_bass_names = [ChordTheory.interval_to_name(i) for i in intervals_from_bass]
                html_content += f"<p><b>Intervals (from Bass {chord_data.get('bass_note_name', '')}):</b> {intervals_from_bass} <i>({', '.join(intervals_from_bass_names)})</i></p>"

        self.details_text_edit.setHtml(f"<div>{html_content}</div>")

        # Update Piano Keyboard
        if self.piano_keyboard_widget:
            played_notes_midi = chord_data.get('played_notes_midi', [])
            self.piano_keyboard_widget.update_active_notes(played_notes_midi)


    def closeEvent(self, event):
        """Handle application close with spinning loading animation"""
        if self.recognizer_thread and self.recognizer_thread.isRunning():
            # Accept the event first to start closing
            event.accept()
            
            # Show spinning loader for shutdown
            self.loading_dialog = LoadingDialog("Shutting down application...", self)
            self.loading_dialog.show_loading()
            
            # Stop the port scan timer first
            self.port_scan_timer.stop()
            self.loading_dialog.message_label.setText("Stopping MIDI recognizer...")
            QApplication.processEvents()
            
            # Start the shutdown process
            self._initiate_graceful_shutdown()
        else:
            # No recognizer running, close immediately
            self.port_scan_timer.stop()
            super().closeEvent(event)

    def _initiate_graceful_shutdown(self):
        """Start the graceful shutdown process"""
        # Signal the recognizer to stop
        self.recognizer_thread.stop_recognizer()
        
        # Wait for graceful shutdown with timeout
        if not self.recognizer_thread.wait(3000):  # Wait up to 3 seconds
            self.loading_dialog.message_label.setText("Force stopping MIDI thread...")
            QApplication.processEvents()
            self.recognizer_thread.terminate()
            self.recognizer_thread.wait(1000)  # Wait a bit more after termination
        
        # Complete shutdown
        self._complete_shutdown()

    def _complete_shutdown(self):
        """Complete the shutdown process"""
        if self.loading_dialog:
            self.loading_dialog.message_label.setText("Finalizing shutdown...")
            QApplication.processEvents()
            
            # Brief delay to show completion
            QTimer.singleShot(300, self._finish_shutdown)
        else:
            self._finish_shutdown()

    def _finish_shutdown(self):
        """Final cleanup and close"""
        if self.loading_dialog:
            self.loading_dialog.close_loading()
            self.loading_dialog = None
        
        # Call the parent closeEvent to actually close the window
        QApplication.quit()
