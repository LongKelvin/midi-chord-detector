"""
Optimized PyQt5 GUI for real-time MIDI chord detection.
Features MIDI input selection and real-time chord name display with improved performance.
"""

import sys
import threading
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QComboBox, QLabel, QPushButton, QStatusBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor
import mido
from midi_chord_recognizer import MIDIChordRecognizer
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChordUpdateSignal(QObject):
    chord_updated = pyqtSignal(str)  # Signal for chord name updates
    status_updated = pyqtSignal(str)  # Signal for status updates

class ChordDetectorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time MIDI Chord Detector")
        self.setGeometry(100, 100, 400, 300)

        # Initialize chord recognizer and signals
        self.recognizer = None
        self.signals = ChordUpdateSignal()
        self.running = False
        self.last_chord = "N.C."

        # Setup GUI components
        self.init_ui()

        # Connect signals
        self.signals.chord_updated.connect(self.update_chord_label)
        self.signals.status_updated.connect(self.update_status_bar)

        # Timer for MIDI device refresh
        self.device_refresh_timer = QTimer(self)
        self.device_refresh_timer.timeout.connect(self.refresh_midi_devices)
        self.device_refresh_timer.start(5000)  # Refresh every 5 seconds

        # Timer for chord polling
        self.chord_poll_timer = QTimer(self)
        self.chord_poll_timer.timeout.connect(self.check_chord_update)
        self.chord_poll_timer.setInterval(10)  # Poll every 10ms for low latency

    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # MIDI input selection
        self.midi_combo = QComboBox()
        self.refresh_midi_devices()
        layout.addWidget(QLabel("Select MIDI Input Device:"))
        layout.addWidget(self.midi_combo)

        # Start/Stop button
        self.toggle_button = QPushButton("Start Detection")
        self.toggle_button.clicked.connect(self.toggle_detection)
        layout.addWidget(self.toggle_button)

        # Chord display
        self.chord_label = QLabel("N.C.")
        self.chord_label.setAlignment(Qt.AlignCenter)
        self.chord_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.chord_label.setStyleSheet("color: black; background-color: #f0f0f0; padding: 10px;")
        layout.addWidget(self.chord_label)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Stopped")

        layout.addStretch()

    def refresh_midi_devices(self):
        """Refresh MIDI device list dynamically."""
        current_port = self.midi_combo.currentText()
        self.midi_combo.clear()
        devices = mido.get_input_names() or ["No MIDI devices found"]
        self.midi_combo.addItems(devices)
        # Restore previous selection if still available
        if current_port in devices:
            self.midi_combo.setCurrentText(current_port)
        logger.debug(f"Refreshed MIDI devices: {devices}")

    def toggle_detection(self):
        """Start or stop the chord recognizer."""
        if not self.running:
            midi_port = self.midi_combo.currentText() if self.midi_combo.currentText() != "No MIDI devices found" else None
            self.recognizer = MIDIChordRecognizer(
                midi_port_name=midi_port,
                zmq_pub_port=5557,
                min_notes_for_chord=2,
                chord_buffer_time=0.015,  # Reduced to 15ms for lower latency
                chord_config_path="chord_definitions.json"
            )
            if self.recognizer.start():
                self.running = True
                self.toggle_button.setText("Stop Detection")
                self.signals.status_updated.emit("Running")
                self.chord_poll_timer.start()
                logger.info("Chord detection started")
            else:
                self.signals.status_updated.emit("Failed to start recognizer")
                logger.error("Failed to start chord recognizer")
        else:
            if self.recognizer:
                self.recognizer.stop()
                self.recognizer = None
            self.running = False
            self.toggle_button.setText("Start Detection")
            self.signals.status_updated.emit("Stopped")
            self.signals.chord_updated.emit("N.C.")
            self.chord_poll_timer.stop()
            logger.info("Chord detection stopped")

    def check_chord_update(self):
        """Check for new chord updates from the recognizer."""
        if not self.recognizer or not self.running:
            return
        status = self.recognizer.get_current_status()
        chord_data = status.get('current_chord', {})
        chord_name = chord_data.get('full_chord_name', 'N.C.')
        if chord_name != self.last_chord:
            self.last_chord = chord_name
            self.signals.chord_updated.emit(chord_name)
            # Visual feedback: briefly change label color
            self.chord_label.setStyleSheet("color: blue; background-color: #f0f0f0; padding: 10px;")
            QTimer.singleShot(100, lambda: self.chord_label.setStyleSheet("color: black; background-color: #f0f0f0; padding: 10px;"))
            logger.debug(f"Chord updated: {chord_name}")

    def update_chord_label(self, chord_name: str):
        """Update the chord label (thread-safe)."""
        self.chord_label.setText(chord_name)

    def update_status_bar(self, message: str):
        """Update the status bar (thread-safe)."""
        self.status_bar.showMessage(message)

    def closeEvent(self, event):
        """Clean up resources on window close."""
        if self.recognizer:
            self.recognizer.stop()
        self.chord_poll_timer.stop()
        self.device_refresh_timer.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChordDetectorGUI()
    window.show()
    sys.exit(app.exec_())