"""
Advanced Real-time MIDI Chord Recognition Library
=================================================

Enhanced Python library for recognizing chords from MIDI input with improved
features for real-time analysis and broadcasting via ZeroMQ.

New Features:
- Dynamic chord definitions via JSON configuration
- Rhythmic analysis for chord segmentation
- Contextual chord progression tracking
- Enhanced confidence scoring with musical context
- Robust error handling and resource cleanup
"""

import mido
import zmq
import json
import time
import threading
from typing import Set, Dict, List, Optional, Tuple, FrozenSet, Any
from collections import OrderedDict, deque
import logging
import math
import os
from pathlib import Path

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_ZMQ_PUB_PORT = 5557
DEFAULT_MIN_NOTES_FOR_CHORD = 2
DEFAULT_CHORD_BUFFER_TIME = 0.05
DEFAULT_RECOGNITION_CONFIDENCE_THRESHOLD = 0.60
DEFAULT_CHORD_CONFIG_PATH = "chord_definitions.json"
DEFAULT_PROGRESSION_MEMORY = 4  # Number of previous chords to track

# --- Chord Definition and Music Theory Core ---
class ChordTheory:
    NOTE_PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    # Default chord definitions
    CHORD_DEFINITIONS: Dict[str, Tuple[str, FrozenSet[int]]] = OrderedDict([
        ('P5', ("Perfect Fifth (Power Chord)", frozenset([0, 7]))),
        ('m3', ("Minor Third Dyad", frozenset([0, 3]))),
        ('M3', ("Major Third Dyad", frozenset([0, 4]))),
        ('maj', ("Major Triad", frozenset([0, 4, 7]))),
        ('min', ("Minor Triad", frozenset([0, 3, 7]))),
        ('dim', ("Diminished Triad", frozenset([0, 3, 6]))),
        ('aug', ("Augmented Triad", frozenset([0, 4, 8]))),
        ('sus2', ("Suspended 2nd", frozenset([0, 2, 7]))),
        ('sus4', ("Suspended 4th", frozenset([0, 5, 7]))),
        ('maj7', ("Major 7th", frozenset([0, 4, 7, 11]))),
        ('min7', ("Minor 7th", frozenset([0, 3, 7, 10]))),
        ('7', ("Dominant 7th", frozenset([0, 4, 7, 10]))),
        ('dim7', ("Diminished 7th", frozenset([0, 3, 6, 9]))),
        ('m7b5', ("Half-diminished 7th", frozenset([0, 3, 6, 10]))),
    ])

    CHORD_PITCH_CLASS_SETS: Dict[str, FrozenSet[int]] = {
        name: frozenset(interval % 12 for interval in intervals)
        for name, (_, intervals) in CHORD_DEFINITIONS.items()
    }

    @classmethod
    def load_chord_definitions(cls, config_path: str = DEFAULT_CHORD_CONFIG_PATH) -> None:
        """Load chord definitions from JSON configuration file."""
        try:
            if not Path(config_path).exists():
                logger.info(f"No chord config found at {config_path}, using defaults")
                return

            with open(config_path, 'r') as f:
                custom_chords = json.load(f)
            
            for chord_type, data in custom_chords.items():
                intervals = frozenset(data.get('intervals', []))
                if intervals and isinstance(data.get('name'), str):
                    cls.CHORD_DEFINITIONS[chord_type] = (data['name'], intervals)
                    cls.CHORD_PITCH_CLASS_SETS[chord_type] = frozenset(i % 12 for i in intervals)
                    logger.info(f"Loaded custom chord: {chord_type} ({data['name']})")
        except Exception as e:
            logger.error(f"Failed to load chord definitions: {e}", exc_info=True)

    @staticmethod
    def midi_to_pitch_class_name(midi_note: int) -> str:
        if not (0 <= midi_note <= 127): return "Invalid"
        return ChordTheory.NOTE_PITCH_CLASSES[midi_note % 12]

    @staticmethod
    def _calculate_match_score(
        played_intervals: FrozenSet[int],
        pattern_intervals: FrozenSet[int],
        played_note_count: int,
        rhythmic_stability: float,
        prev_chord: Optional[Dict[str, Any]] = None
    ) -> float:
        """Enhanced scoring with rhythmic and contextual factors."""
        if not pattern_intervals: return 0.0

        intersection = played_intervals.intersection(pattern_intervals)
        union = played_intervals.union(pattern_intervals)
        score = float(len(intersection)) / len(union) if union else 0.0

        # Bonuses and penalties
        if played_intervals == pattern_intervals:
            score += 0.2
        score += 0.05 * rhythmic_stability  # Reward rhythmic coherence
        
        extra_notes = len(played_intervals - pattern_intervals)
        if extra_notes > 0:
            score -= 0.1 * extra_notes

        missing_notes = len(pattern_intervals - played_intervals)
        if missing_notes > 0 and played_note_count < len(pattern_intervals):
            score -= 0.05 * missing_notes

        # Contextual bonus for common progressions
        if prev_chord and prev_chord.get('theoretical_root_pc') is not None:
            curr_root = played_intervals.pop() % 12 if played_intervals else 0
            prev_root = prev_chord['theoretical_root_pc']
            interval = (curr_root - prev_root) % 12
            if interval in [5, 7]:  # Perfect 4th/5th progressions
                score += 0.03

        return max(0.0, min(1.0, score))

    @classmethod
    def recognize_chord(
        cls,
        played_midi_notes: Set[int],
        min_notes_for_chord: int = DEFAULT_MIN_NOTES_FOR_CHORD,
        rhythmic_stability: float = 1.0,
        prev_chord: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        if len(played_midi_notes) < min_notes_for_chord:
            return None

        sorted_played_notes = sorted(list(played_midi_notes))
        lowest_played_midi = sorted_played_notes[0]
        played_pitch_classes = frozenset(note % 12 for note in sorted_played_notes)
        candidate_recognitions: List[Dict[str, Any]] = []

        for potential_root_pc in sorted(list(played_pitch_classes)):
            for chord_type, (desc_name, abs_intervals) in cls.CHORD_DEFINITIONS.items():
                expected_pcs = frozenset((interval + potential_root_pc) % 12 for interval in abs_intervals)
                
                if played_pitch_classes == expected_pcs:
                    bass_midi = lowest_played_midi
                    bass_name = cls.midi_to_pitch_class_name(bass_midi)
                    root_name = cls.NOTE_PITCH_CLASSES[potential_root_pc]
                    full_name = f"{root_name}{chord_type}"
                    if potential_root_pc != (bass_midi % 12):
                        full_name += f"/{bass_name}"

                    actual_root_midi = next((n for n in sorted_played_notes if n % 12 == potential_root_pc), -1)
                    ref_midi = actual_root_midi if actual_root_midi != -1 else lowest_played_midi
                    played_abs_intervals = frozenset(note - ref_midi for note in sorted_played_notes)

                    score = cls._calculate_match_score(
                        played_abs_intervals, abs_intervals, len(sorted_played_notes),
                        rhythmic_stability, prev_chord
                    )
                    score = (score + 1.5) / 2.5

                    candidate_recognitions.append({
                        'theoretical_root_name': root_name,
                        'chord_type': chord_type,
                        'descriptive_name': desc_name,
                        'bass_note_name': bass_name,
                        'full_chord_name': full_name,
                        'theoretical_root_pc': potential_root_pc,
                        'actual_theoretical_root_midi': actual_root_midi,
                        'bass_midi': bass_midi,
                        'played_notes_midi': sorted_played_notes,
                        'canonical_intervals_abs': sorted(list(abs_intervals)),
                        'confidence': min(1.0, score),
                        'rhythmic_stability': rhythmic_stability
                    })

        # Fallback recognition using lowest note
        if not candidate_recognitions:
            assumed_root_midi = lowest_played_midi
            assumed_root_name = cls.midi_to_pitch_class_name(assumed_root_midi)
            played_abs_intervals = frozenset(note - assumed_root_midi for note in sorted_played_notes)

            for chord_type, (desc_name, abs_intervals) in cls.CHORD_DEFINITIONS.items():
                score = cls._calculate_match_score(
                    played_abs_intervals, abs_intervals, len(sorted_played_notes),
                    rhythmic_stability, prev_chord
                )
                if score >= DEFAULT_RECOGNITION_CONFIDENCE_THRESHOLD / 1.5:
                    candidate_recognitions.append({
                        'theoretical_root_name': assumed_root_name,
                        'chord_type': chord_type,
                        'descriptive_name': desc_name,
                        'bass_note_name': assumed_root_name,
                        'full_chord_name': f"{assumed_root_name}{chord_type}",
                        'theoretical_root_pc': assumed_root_midi % 12,
                        'actual_theoretical_root_midi': assumed_root_midi,
                        'bass_midi': assumed_root_midi,
                        'played_notes_midi': sorted_played_notes,
                        'canonical_intervals_abs': sorted(list(abs_intervals)),
                        'confidence': score * 0.8,
                        'rhythmic_stability': rhythmic_stability
                    })

        if not candidate_recognitions:
            return None

        def sort_key(candidate: Dict[str, Any]) -> Tuple:
            return (
                candidate['confidence'],
                candidate['rhythmic_stability'],
                1 if candidate['actual_theoretical_root_midi'] != -1 else 0,
                1 if candidate['theoretical_root_pc'] == (candidate['bass_midi'] % 12) else 0,
                -len(candidate['canonical_intervals_abs'])
            )

        best_candidate = max(candidate_recognitions, key=sort_key)
        return best_candidate if best_candidate['confidence'] >= DEFAULT_RECOGNITION_CONFIDENCE_THRESHOLD else None

# --- MIDI Recognizer Class ---
class MIDIChordRecognizer:
    def __init__(
        self,
        midi_port_name: Optional[str] = None,
        zmq_pub_port: int = DEFAULT_ZMQ_PUB_PORT,
        min_notes_for_chord: int = DEFAULT_MIN_NOTES_FOR_CHORD,
        chord_buffer_time: float = DEFAULT_CHORD_BUFFER_TIME,
        chord_config_path: str = DEFAULT_CHORD_CONFIG_PATH
    ):
        self.midi_port_name = midi_port_name
        self.zmq_pub_port = zmq_pub_port
        self.min_notes_for_chord = min_notes_for_chord
        self.chord_buffer_time = chord_buffer_time
        self.chord_config_path = chord_config_path
        
        self.active_midi_notes: Set[int] = set()
        self.current_chord_recognition: Optional[Dict[str, Any]] = None
        self.chord_progression: deque = deque(maxlen=DEFAULT_PROGRESSION_MEMORY)
        self.note_timestamps: Dict[int, float] = {}
        
        self._last_note_event_timestamp: float = 0.0
        self._recognition_timer: Optional[threading.Timer] = None
        self._running: bool = False
        self._midi_input_thread: Optional[threading.Thread] = None
        self._midi_input_port: Optional[mido.ports.BaseInput] = None
        self._zmq_context: Optional[zmq.Context] = None
        self._zmq_publisher_socket: Optional[zmq.Socket] = None
        self._lock = threading.Lock()

        ChordTheory.load_chord_definitions(self.chord_config_path)

    def _calculate_rhythmic_stability(self) -> float:
        """Calculate rhythmic stability based on note onset timing."""
        if not self.note_timestamps:
            return 1.0
        timestamps = [t for n, t in self.note_timestamps.items() if n in self.active_midi_notes]
        if len(timestamps) < 2:
            return 1.0
        time_diffs = [abs(timestamps[i] - timestamps[i-1]) for i in range(1, len(timestamps))]
        avg_diff = sum(time_diffs) / len(time_diffs)
        variance = sum((d - avg_diff) ** 2 for d in time_diffs) / len(time_diffs) if time_diffs else 0
        return max(0.5, 1.0 - math.sqrt(variance) / 0.1)

    def _setup_midi_input(self) -> bool:
        try:
            available_ports = mido.get_input_names()
            if not available_ports:
                logger.error("No MIDI input ports found.")
                return False

            selected_port = self.midi_port_name or available_ports[0]
            if selected_port not in available_ports:
                logger.warning(f"Port '{selected_port}' not found, using {available_ports[0]}")
                selected_port = available_ports[0]

            self._midi_input_port = mido.open_input(selected_port)
            logger.info(f"Opened MIDI port: {self._midi_input_port.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to open MIDI port: {e}", exc_info=True)
            return False

    def _setup_zmq_publisher(self) -> bool:
        try:
            self._zmq_context = zmq.Context.instance()
            self._zmq_publisher_socket = self._zmq_context.socket(zmq.PUB)
            self._zmq_publisher_socket.bind(f"tcp://*:{self.zmq_pub_port}")
            logger.info(f"ZMQ publisher bound to port {self.zmq_pub_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to setup ZMQ publisher: {e}", exc_info=True)
            return False

    def _midi_message_handler_loop(self) -> None:
        if not self._midi_input_port:
            return

        try:
            for msg in self._midi_input_port:
                if not self._running:
                    break

                with self._lock:
                    note_changed = False
                    current_time = time.monotonic()
                    
                    if msg.type == 'note_on' and msg.velocity > 0:
                        if msg.note not in self.active_midi_notes:
                            self.active_midi_notes.add(msg.note)
                            self.note_timestamps[msg.note] = current_time
                            note_changed = True
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        if msg.note in self.active_midi_notes:
                            self.active_midi_notes.discard(msg.note)
                            self.note_timestamps.pop(msg.note, None)
                            note_changed = True

                    if note_changed:
                        self._last_note_event_timestamp = current_time
                        if self._recognition_timer:
                            self._recognition_timer.cancel()
                        self._recognition_timer = threading.Timer(
                            self.chord_buffer_time,
                            self._trigger_chord_recognition
                        )
                        self._recognition_timer.start()
        except Exception as e:
            if self._running:
                logger.error(f"MIDI loop error: {e}", exc_info=True)
        finally:
            logger.info("MIDI handler loop stopped.")

    def _trigger_chord_recognition(self) -> None:
        with self._lock:
            if not self._running:
                return

            current_notes = self.active_midi_notes.copy()
            rhythmic_stability = self._calculate_rhythmic_stability()
            prev_chord = self.chord_progression[-1] if self.chord_progression else None

            new_recognition = ChordTheory.recognize_chord(
                current_notes,
                self.min_notes_for_chord,
                rhythmic_stability,
                prev_chord
            )

            old_chord_name = self.current_chord_recognition.get('full_chord_name') if self.current_chord_recognition else None
            new_chord_name = new_recognition.get('full_chord_name') if new_recognition else "N.C."

            if new_chord_name != old_chord_name or not new_recognition:
                self.current_chord_recognition = new_recognition
                if new_recognition:
                    self.chord_progression.append(new_recognition)
                    logger.info(
                        f"Chord: {new_recognition['full_chord_name']} "
                        f"(Conf: {new_recognition['confidence']:.2f}, "
                        f"Stability: {rhythmic_stability:.2f})"
                    )
                    self._publish_chord_update(new_recognition)
                else:
                    reason = "Too few notes" if len(current_notes) < self.min_notes_for_chord else "Unrecognized"
                    logger.info(f"No Chord ({reason}). Notes: {sorted(list(current_notes))}")
                    self._publish_chord_update({
                        'full_chord_name': "N.C.",
                        'reason': reason,
                        'played_notes_midi': sorted(list(current_notes)),
                        'active_note_count': len(current_notes)
                    })

    def _publish_chord_update(self, chord_data: Dict[str, Any]) -> None:
        if not self._zmq_publisher_socket or not self._running:
            return

        message = {
            'timestamp': time.time(),
            'event_type': 'chord_update',
            'data': chord_data,
            'progression': [c.get('full_chord_name', 'N.C.') for c in self.chord_progression]
        }
        try:
            self._zmq_publisher_socket.send_json(message, flags=zmq.NOBLOCK)
        except zmq.Again:
            logger.warning("ZMQ socket busy, update skipped")
        except Exception as e:
            logger.error(f"ZMQ publish error: {e}", exc_info=True)

    def start(self) -> bool:
        with self._lock:
            if self._running:
                logger.warning("Recognizer already running")
                return True

            logger.info("Starting MIDI Chord Recognizer")
            if not self._setup_midi_input() or not self._setup_zmq_publisher():
                self._cleanup()
                return False

            self._running = True
            self._midi_input_thread = threading.Thread(
                target=self._midi_message_handler_loop,
                daemon=True,
                name="MIDIInputHandler"
            )
            self._midi_input_thread.start()
            logger.info("Recognizer started")
            return True

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return

            logger.info("Stopping Recognizer")
            self._running = False
            if self._recognition_timer:
                self._recognition_timer.cancel()
                self._recognition_timer = None

            self._cleanup()
            if self._midi_input_thread and self._midi_input_thread.is_alive():
                self._midi_input_thread.join(timeout=1.0)
            logger.info("Recognizer stopped")

    def _cleanup(self) -> None:
        if self._midi_input_port:
            try:
                self._midi_input_port.close()
            except Exception as e:
                logger.error(f"MIDI close error: {e}")
            self._midi_input_port = None

        if self._zmq_publisher_socket:
            try:
                self._zmq_publisher_socket.close(linger=0)
            except Exception as e:
                logger.error(f"ZMQ close error: {e}")
            self._zmq_publisher_socket = None

    def get_current_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'is_running': self._running,
                'midi_port': self._midi_input_port.name if self._midi_input_port else None,
                'zmq_port': self.zmq_pub_port,
                'active_notes': sorted(list(self.active_midi_notes)),
                'current_chord': self.current_chord_recognition,
                'progression': [c.get('full_chord_name', 'N.C.') for c in self.chord_progression]
            }

# --- Chord Event Subscriber ---
class ChordEventSubscriber:
    def __init__(self, zmq_port: int = DEFAULT_ZMQ_PUB_PORT):
        self.zmq_port = zmq_port
        self._context = zmq.Context.instance()
        self._socket = self._context.socket(zmq.SUB)
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._socket.connect(f"tcp://localhost:{self.zmq_port}")
        self._socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self._thread = threading.Thread(target=self._listen_loop, daemon=True, name="ZMQSubscriber")
        self._thread.start()
        logger.info("Subscriber started")

    def _listen_loop(self):
        while self._running:
            try:
                if self._socket.poll(timeout=500):
                    message = self._socket.recv_json()
                    chord_data = message.get('data', {})
                    full_name = chord_data.get('full_chord_name', 'N.C.')
                    notes = chord_data.get('played_notes_midi', [])
                    confidence = chord_data.get('confidence', -1.0)
                    progression = message.get('progression', [])

                    print(f"♪ RX: {full_name} (Notes: {notes}, Conf: {confidence:.2f}, Prog: {progression})")
            except zmq.error.ZMQError as e:
                if self._running and e.errno != zmq.ETERM:
                    logger.error(f"Subscriber error: {e}", exc_info=True)
                    time.sleep(1)
            except Exception as e:
                logger.error(f"Subscriber error: {e}", exc_info=True)
                time.sleep(1)

    def stop(self):
        if not self._running:
            return
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if hasattr(self._socket, 'close'):
            self._socket.close(linger=0)
        logger.info("Subscriber stopped")

# --- Example Chord Definitions JSON ---
CHORD_CONFIG_EXAMPLE = {
    "maj9": {
        "name": "Major 9th",
        "intervals": [0, 4, 7, 11, 14]
    },
    "min9": {
        "name": "Minor 9th",
        "intervals": [0, 3, 7, 10, 14]
    }
}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Advanced MIDI Chord Recognizer")
    parser.add_argument("--midi-port", type=str)
    parser.add_argument("--zmq-port", type=int, default=DEFAULT_ZMQ_PUB_PORT)
    parser.add_argument("--min-notes", type=int, default=DEFAULT_MIN_NOTES_FOR_CHORD)
    parser.add_argument("--buffer-time", type=float, default=DEFAULT_CHORD_BUFFER_TIME)
    parser.add_argument("--confidence-threshold", type=float, default=DEFAULT_RECOGNITION_CONFIDENCE_THRESHOLD)
    parser.add_argument("--chord-config", type=str, default=DEFAULT_CHORD_CONFIG_PATH)
    parser.add_argument("--subscribe", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--create-config", action="store_true", help="Create sample chord config")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    if args.create_config:
        with open(args.chord_config, 'w') as f:
            json.dump(CHORD_CONFIG_EXAMPLE, f, indent=2)
        logger.info(f"Created sample chord config at {args.chord_config}")
        exit(0)

    DEFAULT_RECOGNITION_CONFIDENCE_THRESHOLD = args.confidence_threshold

    if args.subscribe:
        subscriber = ChordEventSubscriber(zmq_port=args.zmq_port)
        subscriber.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            subscriber.stop()
    else:
        recognizer = MIDIChordRecognizer(
            midi_port_name=args.midi_port,
            zmq_pub_port=args.zmq_port,
            min_notes_for_chord=args.min_notes,
            chord_buffer_time=args.buffer_time,
            chord_config_path=args.chord_config
        )
        if recognizer.start():
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                recognizer.stop()