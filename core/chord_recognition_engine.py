import os
import mido
import zmq
import time
import threading
import logging
import argparse
from typing import Callable, Set, Dict, Optional, Any

from core.music_theory import ChordTheory
from utils.utils import resource_path

# --- Constants ---
DEFAULT_ZMQ_PUB_PORT = 5557
DEFAULT_MIN_NOTES_FOR_CHORD = 2
DEFAULT_CHORD_BUFFER_TIME_ON = 0.015
DEFAULT_CHORD_CONFIG_PATH = resource_path(os.path.join("data", "chord_definitions.json"))
DEFAULT_LOG_LEVEL = "INFO"

# --- Logging Setup ---
logger = logging.getLogger(__name__)  # Initial logger


# --- MIDIChordRecognizer Class ---
class MIDIChordRecognizer:
    def __init__(
        self,
        midi_port_name: Optional[str] = None,
        zmq_pub_port: int = DEFAULT_ZMQ_PUB_PORT,
        min_notes_for_chord: int = DEFAULT_MIN_NOTES_FOR_CHORD,
        chord_buffer_time_on: float = DEFAULT_CHORD_BUFFER_TIME_ON,
        chord_config_path: str = DEFAULT_CHORD_CONFIG_PATH,
        use_zmq: bool = True,
        update_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.midi_port_name = midi_port_name
        self.zmq_pub_port = zmq_pub_port
        self.min_notes = min_notes_for_chord
        self.chord_buffer_time = chord_buffer_time_on
        self.chord_config_path = chord_config_path
        self.active_notes: Set[int] = set()
        self.sustain_pedal_on: bool = False
        self.sustained_notes_pending_release: Set[int] = set()
        self.running = False
        self.midi_port: Optional[mido.ports.BaseInput] = None
        self.zmq_context: Optional[zmq.Context] = None
        self.zmq_socket: Optional[zmq.Socket] = None
        self.lock = threading.Lock()
        self.midi_thread: Optional[threading.Thread] = None
        self.use_zmq = use_zmq
        self.update_callback = update_callback
        ChordTheory.load_chord_definitions(self.chord_config_path)

    def _setup_midi(self) -> bool:
        try:
            available_ports = mido.get_input_names()
            if not available_ports:
                logger.error("No MIDI input ports found.")
                return False
            port_to_open: Optional[str] = None
            if self.midi_port_name:
                if self.midi_port_name in available_ports:
                    port_to_open = self.midi_port_name
                else:
                    logger.warning(
                        f"Specified MIDI port '{self.midi_port_name}' not found. "
                        f"Available ports: {available_ports}. Using first available: '{available_ports[0]}'."
                    )
                    port_to_open = available_ports[0]
            else:
                port_to_open = available_ports[0]
                logger.info(
                    f"No MIDI port specified. Using first available: '{port_to_open}'."
                )
            self.midi_port = mido.open_input(port_to_open)
            logger.info(f"Successfully opened MIDI port: '{self.midi_port.name}'.")
            return True
        except mido.MidiIOError as e:
            logger.error(f"Mido MIDI I/O Error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to open MIDI port: {e}")
            return False

    def _setup_zmq(self) -> bool:
        try:
            if not self.use_zmq:
                self.zmq_context = None  # Ensure these are None if ZMQ is off
                self.zmq_socket = None
                logger.info("ZMQ publishing is disabled for this recognizer instance.")
                return (
                    True  # Return True to indicate setup (of "nothing") was successful
                )

            self.zmq_context = zmq.Context()
            self.zmq_socket = self.zmq_context.socket(zmq.PUB)
            self.zmq_socket.bind(f"tcp://*:{self.zmq_pub_port}")
            logger.info(f"ZMQ publisher bound to tcp://*:{self.zmq_pub_port}")
            return True
        except zmq.ZMQError as e:
            logger.error(f"ZMQ Error during setup: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to setup ZMQ: {e}")
            return False

    def _process_midi_message(self, msg: mido.Message) -> bool:
        changed = False
        if msg.type == "note_on" and msg.velocity > 0:
            if msg.note not in self.active_notes:
                self.active_notes.add(msg.note)
                changed = True
            if msg.note in self.sustained_notes_pending_release:
                self.sustained_notes_pending_release.discard(msg.note)
            logger.debug(
                f"Note ON: {msg.note} Vel: {msg.velocity} | Active: {sorted(list(self.active_notes))}"
            )
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            if self.sustain_pedal_on:
                if (
                    msg.note in self.active_notes
                    and msg.note not in self.sustained_notes_pending_release
                ):
                    self.sustained_notes_pending_release.add(msg.note)
                    logger.debug(
                        f"Note OFF (sustained): {msg.note} | Pending: {sorted(list(self.sustained_notes_pending_release))}"
                    )
            else:
                if msg.note in self.active_notes:
                    self.active_notes.discard(msg.note)
                    changed = True
                if msg.note in self.sustained_notes_pending_release:
                    self.sustained_notes_pending_release.discard(
                        msg.note
                    )  # Should be empty if sustain just went off
                logger.debug(
                    f"Note OFF: {msg.note} | Active: {sorted(list(self.active_notes))}"
                )
        elif msg.type == "control_change" and msg.control == 64:  # Sustain Pedal
            pedal_just_turned_off = False
            if msg.value >= 64:  # Sustain ON
                if not self.sustain_pedal_on:
                    self.sustain_pedal_on = True
                    logger.debug(
                        f"Sustain Pedal ON | Active: {sorted(list(self.active_notes))}"
                    )
            else:  # Sustain OFF
                if self.sustain_pedal_on:
                    self.sustain_pedal_on = False
                    pedal_just_turned_off = True
                    logger.debug("Sustain Pedal OFF")
            if pedal_just_turned_off:
                notes_to_remove = self.sustained_notes_pending_release.copy()
                if notes_to_remove:
                    for note_rm in notes_to_remove:
                        self.active_notes.discard(note_rm)
                    changed = True
                    logger.debug(
                        f"Post Sustain OFF, removed: {sorted(list(notes_to_remove))} | Active: {sorted(list(self.active_notes))}"
                    )
                self.sustained_notes_pending_release.clear()
        return changed

    def _midi_handler(self):
        logger.info("MIDI handler thread started.")
        while self.running:
            try:
                if not self.midi_port:
                    logger.error("MIDI port is not open in handler loop.")
                    time.sleep(1)
                    continue
                msg = self.midi_port.receive(block=True)
                if not self.running:
                    break
                with self.lock:
                    if self._process_midi_message(msg):
                        self._update_chord_and_publish()
            except Exception as e:
                if self.running:
                    logger.error(f"Error in MIDI handler thread: {e}", exc_info=True)
                    time.sleep(0.1)
        logger.info("MIDI handler thread stopped.")

    def _update_chord_and_publish(self):
        chord_info = ChordTheory.recognize_chord(self.active_notes, self.min_notes)
        publish_data: Dict[str, Any] = {
            "timestamp": time.time(),
            "full_chord_name": "N.C.",
            "played_notes_midi": sorted(list(self.active_notes)),
            "root_note_name": None,
            "bass_note_name": None,
            "inversion_type": None,
            "score": 0.0,
        }
        if (
            self.active_notes
        ):  # Set bass_note_name if notes are played, even if no chord
            publish_data["bass_note_name"] = ChordTheory.midi_to_pitch_class_name(
                sorted(list(self.active_notes))[0]
            )

        if chord_info:
            publish_data.update(chord_info)
            logger.info(
                f"Chord: {publish_data['full_chord_name']} "
                f"({publish_data.get('inversion_type', 'N/A')}), "
                f"Score: {publish_data.get('score', 0.0):.2f}, "
                f"Notes: {publish_data['played_notes_midi']}"
            )
        else:
            logger.info(f"N.C. Active notes: {publish_data['played_notes_midi']}")

        # Call the callback if it exist
        if self.update_callback:
            try:
                self.update_callback(publish_data)
            except Exception as e:
                logger.error(f"Error in update_callback: {e}", exc_info=True)

        if self.use_zmq:  # Only publish to ZMQ if enabled
            self._publish(publish_data)  # _publish now only handles ZMQ

        if self.chord_buffer_time > 0:
            time.sleep(self.chord_buffer_time)

    def _publish(self, data_to_publish: Dict):
        if not self.zmq_socket or not self.running:
            return
        try:
            self.zmq_socket.send_json(data_to_publish)
            logger.debug(
                f"ZMQ Published: {data_to_publish.get('full_chord_name', 'N.C.')}"
            )
        except zmq.ZMQError as e:
            logger.warning(f"ZMQ publish error: {e}")
        except Exception as e:
            logger.warning(f"Unexpected error during ZMQ publish: {e}")

    def start(self) -> bool:
        with self.lock:
            if self.running:
                logger.info("Recognizer already running.")
                return True
            logger.info("Starting MIDI Chord Recognizer...")
            if not self._setup_midi() or not self._setup_zmq():
                logger.error("Setup failed. Cleaning up and aborting start.")
                self._cleanup()
                return False
            self.running = True
            self.midi_thread = threading.Thread(
                target=self._midi_handler, name="MIDIHandlerThread", daemon=True
            )
            self.midi_thread.start()
            logger.info("Recognizer started successfully.")
            return True

    def stop(self):
        logger.info("Stopping MIDI Chord Recognizer...")
        with self.lock:
            if not self.running:
                logger.info("Recognizer already stopped.")
                return
            self.running = False
        if self.midi_thread and self.midi_thread.is_alive():
            logger.debug("Waiting for MIDI handler thread to join...")
            if self.midi_port:
                try:
                    self.midi_port.close()
                    logger.debug("MIDI port closed to help thread unblock.")
                except Exception as e:
                    logger.warning(f"Exception closing MIDI port during stop: {e}")
            self.midi_thread.join(timeout=2.0)
            if self.midi_thread.is_alive():
                logger.warning("MIDI handler thread did not join in time.")
        with self.lock:
            self._cleanup()
        logger.info("Recognizer stopped.")

    def _cleanup(self):
        logger.debug("Cleaning up resources...")
        if self.midi_port and not self.midi_port.closed:
            try:
                self.midi_port.close()
                logger.debug("MIDI port closed.")
            except Exception as e:
                logger.warning(f"Error closing MIDI port: {e}")
        self.midi_port = None
        if self.zmq_socket:
            try:
                self.zmq_socket.close(linger=0)
                logger.debug("ZMQ socket closed.")
            except Exception as e:
                logger.warning(f"Error closing ZMQ socket: {e}")
        self.zmq_socket = None
        if self.zmq_context:
            try:
                self.zmq_context.term()
                logger.debug("ZMQ context terminated.")
            except Exception as e:
                logger.warning(f"Error terminating ZMQ context: {e}")
        self.zmq_context = None
        self.active_notes.clear()
        self.sustained_notes_pending_release.clear()
        self.sustain_pedal_on = False
        logger.debug("Internal state cleared.")


# --- Main Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="MIDI Chord Recognizer with ZMQ Publisher."
    )
    parser.add_argument(
        "--midi-port", type=str, default=None, help="Name of the MIDI input port."
    )
    parser.add_argument(
        "--zmq-port",
        type=int,
        default=DEFAULT_ZMQ_PUB_PORT,
        help=f"ZMQ port (default: {DEFAULT_ZMQ_PUB_PORT}).",
    )
    parser.add_argument(
        "--min-notes",
        type=int,
        default=DEFAULT_MIN_NOTES_FOR_CHORD,
        help=f"Min notes for chord (default: {DEFAULT_MIN_NOTES_FOR_CHORD}).",
    )
    parser.add_argument(
        "--buffer-time",
        type=float,
        default=DEFAULT_CHORD_BUFFER_TIME_ON,
        help=f"Buffer time (s) (default: {DEFAULT_CHORD_BUFFER_TIME_ON}).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CHORD_CONFIG_PATH,
        help=f"Chord definitions JSON (default: '{DEFAULT_CHORD_CONFIG_PATH}').",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=DEFAULT_LOG_LEVEL,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=f"Logging level (default: {DEFAULT_LOG_LEVEL}).",
    )
    parser.add_argument(
        "--list-midi-ports", action="store_true", help="List MIDI input ports and exit."
    )
    args = parser.parse_args()

    log_level_numeric = getattr(logging, args.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level_numeric,
        format="%(asctime)s - %(levelname)s - [%(threadName)s] %(name)s.%(funcName)s:%(lineno)d - %(message)s",
    )

    if args.list_midi_ports:
        try:
            available_ports = mido.get_input_names()
            if available_ports:
                print("Available MIDI input ports:")
                [print(f'  - "{p}"') for p in available_ports]
            else:
                print("No MIDI input ports found.")
        except Exception as e:
            logger.error(f"Could not list MIDI ports: {e}")
        exit()

    recognizer = MIDIChordRecognizer(
        midi_port_name=args.midi_port,
        zmq_pub_port=args.zmq_port,
        min_notes_for_chord=args.min_notes,
        chord_buffer_time_on=args.buffer_time,
        chord_config_path=args.config,
    )

    if recognizer.start():
        logger.info("MIDI Chord Recognizer running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received.")
        finally:
            recognizer.stop()
    else:
        logger.error("Failed to start MIDI Chord Recognizer.")
        exit(1)
