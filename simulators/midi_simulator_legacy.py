"""
MIDI simulator to create a virtual MIDI port and send note messages.
Simulates playing chords to test the chord detection GUI without external applications.
"""

import mido
import time
import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MIDISimulator:
    def __init__(self, port_name: str = "Virtual MIDI"):
        self.port_name = port_name
        self.output_port = None

    def setup(self) -> bool:
        """Create a virtual MIDI output port."""
        try:
            # Create a virtual MIDI port
            self.output_port = mido.open_output(self.port_name, virtual=True)
            logger.info(f"Created virtual MIDI output port: {self.port_name}")
            logger.info(f"Available input ports: {mido.get_input_names()}")
            return True
        except Exception as e:
            logger.error(f"Failed to create virtual MIDI port: {e}", exc_info=True)
            return False

    def send_chord(self, notes: List[int], duration: float = 1.0, velocity: int = 64):
        """Send a chord (list of MIDI notes) with specified duration and velocity."""
        try:
            # Send note-on messages
            for note in notes:
                msg = mido.Message('note_on', note=note, velocity=velocity)
                self.output_port.send(msg)
                logger.debug(f"Sent note_on: note={note}, velocity={velocity}")
            # Hold the chord
            time.sleep(duration)
            # Send note-off messages
            for note in notes:
                msg = mido.Message('note_off', note=note, velocity=0)
                self.output_port.send(msg)
                logger.debug(f"Sent note_off: note={note}")
        except Exception as e:
            logger.error(f"Error sending chord: {e}", exc_info=True)

    def simulate_sequence(self, sequence: List[Tuple[List[int], float]]):
        """Simulate a sequence of chords with durations."""
        if not self.output_port:
            logger.error("MIDI port not initialized")
            return
        for notes, duration in sequence:
            logger.info(f"Playing chord: {notes}")
            self.send_chord(notes, duration)
            time.sleep(0.1)  # Small pause between chords

    def close(self):
        """Close the MIDI output port."""
        if self.output_port:
            try:
                self.output_port.close()
                logger.info("Virtual MIDI output port closed")
            except Exception as e:
                logger.error(f"Error closing MIDI port: {e}", exc_info=True)
            finally:
                self.output_port = None

if __name__ == "__main__":
    # Example chord sequence: C major, G7, A minor, pause
    chord_sequence = [
        ([60, 64, 67], 1.0),  # Cmaj: C4, E4, G4
        ([55, 59, 62, 65], 1.0),  # G7: G3, B3, D4, F4
        ([57, 60, 64], 1.0),  # Amin: A3, C4, E4
        ([], 1.0),  # No chord (pause)
    ]

    simulator = MIDISimulator(port_name="Virtual MIDI")
    if simulator.setup():
        try:
            logger.info("Starting chord simulation. Run the GUI and select 'Virtual MIDI' as the input.")
            time.sleep(2)  # Give time to start the GUI
            simulator.simulate_sequence(chord_sequence)
        except KeyboardInterrupt:
            logger.info("Simulation stopped by user")
        finally:
            simulator.close()