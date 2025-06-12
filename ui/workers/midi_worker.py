# --- QThread for running the MIDI Recognizer ---
from typing import Optional

from PyQt6.QtCore import QThread

import mido
from core.chord_recognition_engine import MIDIChordRecognizer
from ui.workers.recognizer_signal import RecognizerSignals


class MIDIWorkerThread(QThread):
    def __init__(self, config_path, min_notes, buffer_time, parent=None):
        super().__init__(parent)
        self.signals = RecognizerSignals()
        self.recognizer: Optional[MIDIChordRecognizer] = None
        self.selected_midi_port: Optional[str] = None
        
        self._config_path = config_path
        self._min_notes = min_notes
        self._buffer_time = buffer_time
        self._running = False

    def set_midi_port(self, port_name: Optional[str]):
        self.selected_midi_port = port_name

    def run(self):
        self._running = True
        self.signals.recognizer_status.emit(f"Worker thread started.")

        if not self.selected_midi_port:
            available_ports = mido.get_input_names()
            self.signals.midi_ports_listed.emit(available_ports)
            if not available_ports:
                self.signals.recognizer_status.emit("No MIDI input ports found.")
                self._running = False
                return
            # Default to first port if none explicitly selected before start
            # self.selected_midi_port = available_ports[0] 
            # Better to wait for user selection
            self.signals.recognizer_status.emit("Please select a MIDI port.")
            self._running = False # Stop if no port selected yet
            return

        self.recognizer = MIDIChordRecognizer(
            midi_port_name=self.selected_midi_port,
            
            min_notes_for_chord=self._min_notes,
            chord_buffer_time_on=self._buffer_time,
            chord_config_path=self._config_path,
            use_zmq=False,  # << Explicitly disable ZMQ for UI instance
            update_callback=self.signals.chord_updated.emit # << Pass the signal emitter
            
            
        )
        
        # Override the recognizer's publish method to emit a signal instead
        # This is a bit of a monkey-patch; a cleaner way would be to pass a callback
        # or make the recognizer itself emit signals (if it were Qt-aware).
        original_publish_method = self.recognizer._publish
        def qt_publish_override(data_to_publish: dict):
            self.signals.chord_updated.emit(data_to_publish)
            # If you still want ZMQ publishing for other apps:
            # original_publish_method(data_to_publish) 
            # (but ensure ZMQ setup isn't conflicting or disable it in recognizer for this UI)
            
            # For this UI, we'll assume the recognizer's _publish does nothing or we replace it
            # To prevent ZMQ from being used by this UI directly:
            self.recognizer.zmq_socket = None # Disable ZMQ for this instance
            
        self.recognizer._publish = qt_publish_override
        
        # Also, need to disable ZMQ setup in the recognizer for this specific UI use case,
        # or make it optional. For simplicity, we'll assume `_setup_zmq` can handle `self.zmq_socket` being None.
        # A more robust way: add a `use_zmq=False` flag to MIDIChordRecognizer.__init__
        
        original_setup_zmq = self.recognizer._setup_zmq
        def no_zmq_setup():
            self.recognizer.zmq_context = None # Ensure no ZMQ setup
            self.recognizer.zmq_socket = None
            return True # Pretend ZMQ setup was successful
        self.recognizer._setup_zmq = no_zmq_setup


        if self.recognizer.start(): # This start will use the overridden _publish and _setup_zmq
            self.signals.recognizer_status.emit(f"Recognizer started on {self.recognizer.midi_port_name if self.recognizer.midi_port else 'N/A'}.")
            while self._running and self.recognizer.running:
                # The recognizer's internal loop handles MIDI messages.
                # This QThread loop just keeps the thread alive until stopped.
                self.msleep(100) # Sleep to be responsive to _running flag
            
            if self.recognizer.running: # If loop exited due to self._running = False
                 self.recognizer.stop()
            self.signals.recognizer_status.emit("Recognizer stopped.")
        else:
            self.signals.recognizer_status.emit("Failed to start MIDI recognizer.")
        
        self.recognizer = None # Clear recognizer instance

    def stop_recognizer(self):
        self._running = False
        if self.recognizer:
            self.recognizer.stop() # Tell the engine to stop
        self.quit() # Ask QThread to quit
        self.wait() # Wait for run() to finish
        self.signals.recognizer_status.emit("Worker thread stopped.")
