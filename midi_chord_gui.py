import sys
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QComboBox, QLabel, QPushButton)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont
import mido
import zmq
from midi_chord_recognizer import MIDIChordRecognizer
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class ChordUpdateSignal(QObject):
    chord_updated = pyqtSignal(str)  # Signal for chord name updates

class ChordDetectorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time MIDI Chord Detector")
        self.setGeometry(100, 100, 400, 200)

        # Initialize variables
        self.recognizer = None
        self.signals = ChordUpdateSignal()
        self.running = False
        self.zmq_context = None
        self.zmq_socket = None
        self.zmq_thread = None
        self.zmq_running = False

        # Setup GUI
        self.init_ui()

        # Connect signal
        self.signals.chord_updated.connect(self.update_chord_label)

        # Timer for MIDI device refresh
        self.device_refresh_timer = QTimer(self)
        self.device_refresh_timer.timeout.connect(self.refresh_midi_devices)
        self.device_refresh_timer.start(5000)

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
        layout.addWidget(self.chord_label)

        layout.addStretch()

    def refresh_midi_devices(self):
        """Refresh MIDI device list."""
        current_port = self.midi_combo.currentText()
        self.midi_combo.clear()
        devices = mido.get_input_names() or ["No MIDI devices found"]
        self.midi_combo.addItems(devices)
        if current_port in devices:
            self.midi_combo.setCurrentText(current_port)

    def toggle_detection(self):
        """Start or stop chord detection."""
        if not self.running:
            midi_port = self.midi_combo.currentText() if self.midi_combo.currentText() != "No MIDI devices found" else None
            self.recognizer = MIDIChordRecognizer(
                midi_port_name=midi_port,
                zmq_pub_port=5557,
                min_notes_for_chord=2,
                chord_buffer_time_on=0.015,
                chord_config_path="chord_definitions.json"
            )
            if self.recognizer.start():
                self.running = True
                self.toggle_button.setText("Stop Detection")
                self.start_zmq_subscriber()
                logger.info("Chord detection started")
            else:
                logger.info("Failed to start chord recognizer")
        else:
            if self.recognizer:
                self.recognizer.stop()
                self.recognizer = None
            self.running = False
            self.toggle_button.setText("Start Detection")
            self.signals.chord_updated.emit("N.C.")
            self.stop_zmq_subscriber()
            logger.info("Chord detection stopped")

    def start_zmq_subscriber(self):
        """Start ZMQ subscriber to receive chord updates."""
        if self.zmq_running:
            return
        try:
            self.zmq_context = zmq.Context()
            self.zmq_socket = self.zmq_context.socket(zmq.SUB)
            self.zmq_socket.setsockopt_string(zmq.SUBSCRIBE, "")
            self.zmq_socket.connect("tcp://localhost:5557")
            self.zmq_running = True
            self.zmq_thread = threading.Thread(target=self._zmq_listen_loop, daemon=True)
            self.zmq_thread.start()
            logger.info("ZMQ subscriber started")
        except Exception as e:
            logger.info(f"ZMQ subscriber failed: {e}")

    def stop_zmq_subscriber(self):
        """Stop ZMQ subscriber."""
        if not self.zmq_running:
            return
        self.zmq_running = False
        if self.zmq_thread and self.zmq_thread.is_alive():
            self.zmq_thread.join(timeout=1.0)
        if self.zmq_socket:
            self.zmq_socket.close()
        if self.zmq_context:
            self.zmq_context.term()
        self.zmq_socket = None
        self.zmq_context = None
        logger.info("ZMQ subscriber stopped")

    def _zmq_listen_loop(self):
        """Listen for ZMQ chord updates."""
        while self.zmq_running:
            try:
                message = self.zmq_socket.recv_json()
                chord_data = message.get('data', {})
                chord_name = chord_data.get('full_chord_name', 'N.C.')
                self.signals.chord_updated.emit(chord_name)
            except:
                pass  # Ignore errors, keep listening

    def update_chord_label(self, chord_name: str):
        """Update chord label."""
        self.chord_label.setText(chord_name)

    def closeEvent(self, event):
        """Clean up on window close."""
        if self.recognizer:
            self.recognizer.stop()
        self.stop_zmq_subscriber()
        self.device_refresh_timer.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChordDetectorGUI()
    window.show()
    sys.exit(app.exec_())