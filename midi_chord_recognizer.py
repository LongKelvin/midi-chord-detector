import mido
import zmq
import json
import time
import threading
import logging
from typing import Set, Dict, Optional, FrozenSet, Tuple
from collections import OrderedDict
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DEFAULT_ZMQ_PUB_PORT = 5557
DEFAULT_MIN_NOTES_FOR_CHORD = 2
DEFAULT_CHORD_BUFFER_TIME_ON = 0.015
DEFAULT_CHORD_CONFIG_PATH = "chord_definitions.json"

class ChordTheory:
    NOTE_PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    CHORD_DEFINITIONS: Dict[str, Tuple[str, FrozenSet[int]]] = OrderedDict([
        ('maj', ("Major Triad", frozenset([0, 4, 7]))),
        ('min', ("Minor Triad", frozenset([0, 3, 7]))),
        ('dim', ("Diminished Triad", frozenset([0, 3, 6]))),
        ('aug', ("Augmented Triad", frozenset([0, 4, 8]))),
        ('sus2', ("Suspended 2nd", frozenset([0, 2, 7]))),
        ('sus4', ("Suspended 4th", frozenset([0, 5, 7]))),
        ('maj7', ("Major 7th", frozenset([0, 4, 7, 11]))),
        ('min7', ("Minor 7th", frozenset([0, 3, 7, 10]))),
        ('7', ("Dominant 7th", frozenset([0, 4, 7, 10]))),
    ])

    @classmethod
    def load_chord_definitions(cls, config_path: str = DEFAULT_CHORD_CONFIG_PATH) -> None:
        try:
            if not Path(config_path).exists():
                logger.info(f"No chord config at {config_path}, using defaults")
                return
            with open(config_path, 'r') as f:
                custom_chords = json.load(f)
            cls.CHORD_DEFINITIONS.clear()
            for chord_type, data in custom_chords.items():
                intervals = frozenset(data.get('intervals', []))
                if intervals and isinstance(data.get('name'), str):
                    cls.CHORD_DEFINITIONS[chord_type] = (data['name'], intervals)
                    logger.info(f"Loaded chord: {chord_type}")
        except Exception as e:
            logger.info(f"Failed to load chord definitions: {e}")

    @staticmethod
    def midi_to_pitch_class_name(midi_note: int) -> str:
        if not (0 <= midi_note <= 127):
            return "Invalid"
        return ChordTheory.NOTE_PITCH_CLASSES[midi_note % 12]

    @classmethod
    def recognize_chord(cls, played_notes: Set[int], min_notes: int) -> Optional[Dict]:
        if len(played_notes) < min_notes:
            return None
        notes = sorted(played_notes)
        lowest_midi = notes[0]
        played_pcs = frozenset(note % 12 for note in notes)
        best_match = None
        best_score = 0.0
        for root_pc in range(12):
            for chord_type, (desc_name, intervals) in cls.CHORD_DEFINITIONS.items():
                expected_pcs = frozenset((root_pc + interval) % 12 for interval in intervals)
                if played_pcs.issubset(expected_pcs) or expected_pcs.issubset(played_pcs):
                    intersection = len(played_pcs & expected_pcs)
                    union = len(played_pcs | expected_pcs)
                    score = intersection / union if union else 0.0
                    if score > best_score:
                        best_score = score
                        root_name = cls.midi_to_pitch_class_name(root_pc)
                        bass_name = cls.midi_to_pitch_class_name(lowest_midi)
                        full_name = f"{root_name}{chord_type}"
                        if root_pc != lowest_midi % 12:
                            full_name += f"/{bass_name}"
                        best_match = {
                            'full_chord_name': full_name,
                            'played_notes_midi': notes
                        }
        if best_match:
            logger.info(f"Chord: {best_match['full_chord_name']}")
        return best_match

class MIDIChordRecognizer:
    def __init__(
        self,
        midi_port_name: Optional[str] = None,
        zmq_pub_port: int = DEFAULT_ZMQ_PUB_PORT,
        min_notes_for_chord: int = DEFAULT_MIN_NOTES_FOR_CHORD,
        chord_buffer_time_on: float = DEFAULT_CHORD_BUFFER_TIME_ON,
        chord_config_path: str = DEFAULT_CHORD_CONFIG_PATH
    ):
        self.midi_port_name = midi_port_name
        self.zmq_pub_port = zmq_pub_port
        self.min_notes = min_notes_for_chord
        self.chord_buffer_time = chord_buffer_time_on
        self.chord_config_path = chord_config_path
        self.active_notes: Set[int] = set()
        self.running = False
        self.midi_port = None
        self.zmq_context = None
        self.zmq_socket = None
        self.lock = threading.Lock()
        ChordTheory.load_chord_definitions(self.chord_config_path)

    def _setup_midi(self) -> bool:
        try:
            ports = mido.get_input_names()
            if not ports:
                logger.info("No MIDI ports found")
                return False
            port = self.midi_port_name or ports[0]
            if port not in ports:
                port = ports[0]
            self.midi_port = mido.open_input(port)
            logger.info(f"Opened MIDI port: {port}")
            return True
        except Exception as e:
            logger.info(f"Failed to open MIDI: {e}")
            return False

    def _setup_zmq(self) -> bool:
        try:
            self.zmq_context = zmq.Context()
            self.zmq_socket = self.zmq_context.socket(zmq.PUB)
            self.zmq_socket.bind(f"tcp://*:{self.zmq_pub_port}")
            logger.info(f"ZMQ publisher on port {self.zmq_pub_port}")
            return True
        except Exception as e:
            logger.info(f"Failed to setup ZMQ: {e}")
            return False

    def _midi_handler(self):
        while self.running:
            try:
                for msg in self.midi_port:
                    if not self.running:
                        break
                    with self.lock:
                        if msg.type == 'note_on' and msg.velocity > 0:
                            self.active_notes.add(msg.note)
                            logger.info(f"Note ON: {msg.note}")
                        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                            self.active_notes.discard(msg.note)
                            logger.info(f"Note OFF: {msg.note}")
                        self._update_chord()
            except Exception as e:
                if self.running:
                    logger.info(f"MIDI error: {e}")

    def _update_chord(self):
        chord = ChordTheory.recognize_chord(self.active_notes, self.min_notes)
        chord_name = chord['full_chord_name'] if chord else "N.C."
        self._publish({
            'full_chord_name': chord_name,
            'played_notes_midi': sorted(list(self.active_notes))
        })
        time.sleep(self.chord_buffer_time)

    def _publish(self, chord_data: Dict):
        if not self.zmq_socket or not self.running:
            return
        try:
            self.zmq_socket.send_json({'data': chord_data})
            logger.info(f"Published: {chord_data['full_chord_name']}")
        except Exception as e:
            logger.info(f"ZMQ publish error: {e}")

    def start(self) -> bool:
        with self.lock:
            if self.running:
                return True
            if not self._setup_midi() or not self._setup_zmq():
                self._cleanup()
                return False
            self.running = True
            self.midi_thread = threading.Thread(target=self._midi_handler, daemon=True)
            self.midi_thread.start()
            logger.info("Recognizer started")
            return True

    def stop(self):
        with self.lock:
            if not self.running:
                return
            self.running = False
            self._cleanup()
            if self.midi_thread and self.midi_thread.is_alive():
                self.midi_thread.join(timeout=1.0)
            logger.info("Recognizer stopped")

    def _cleanup(self):
        if self.midi_port:
            try:
                self.midi_port.close()
            except:
                pass
            self.midi_port = None
        if self.zmq_socket:
            try:
                self.zmq_socket.close()
            except:
                pass
            self.zmq_socket = None
        if self.zmq_context:
            try:
                self.zmq_context.term()
            except:
                pass
            self.zmq_context = None
        self.active_notes.clear()

if __name__ == "__main__":
    recognizer = MIDIChordRecognizer()
    if recognizer.start():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            recognizer.stop()