# --- Custom Signal Emitter for MIDI Recognizer ---
from PyQt6.QtCore import pyqtSignal, QObject

class RecognizerSignals(QObject):
    chord_updated = pyqtSignal(dict) # Emits the chord data dictionary
    midi_ports_listed = pyqtSignal(list)
    recognizer_status = pyqtSignal(str)