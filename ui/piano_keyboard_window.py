# --- PianoKeyboardWidget ---
from typing import Dict, List
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QSizePolicy, QSpacerItem


from core.music_theory import ChordTheory
from ui.piano_keyboard_widget import PianoKeyWidget

class PianoKeyboardWidget(QFrame):
    START_MIDI_NOTE = 21  # A0
    END_MIDI_NOTE = 108 # C8 (88 keys)

    # Standard pattern of black keys in an octave (C=0, C#=1, etc.)
    BLACK_KEY_PATTERN = [1, 3, -1, 6, 8, 10, -1] # -1 for no black key next

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PianoKeyboardFrame")
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame#PianoKeyboardFrame {
                background-color: #1E1E1E; /* Dark background for the keyboard holder */
                border: 2px solid #444444;
                border-radius: 5px;
            }
        """)

        self.keys: Dict[int, PianoKeyWidget] = {} # midi_note -> PianoKeyWidget
        self._setup_keyboard_ui()

    def _is_black_key(self, midi_note: int) -> bool:
        return ChordTheory.midi_to_pitch_class_name(midi_note).endswith("#")

    def _setup_keyboard_ui(self):
        # Using a QHBoxLayout to arrange "octave groups" or sections can be complex
        # A simpler initial approach might be to use absolute positioning or a custom layout,
        # but QGraphicsView is often best for complex interactive graphics.
        # For now, let's try a simplified layout with QGridLayout or manual positioning
        # within a fixed-size widget.

        # A common approach for piano keyboard layout:
        # 1. Lay out all white keys.
        # 2. Overlay black keys on top of them at appropriate positions.
        # This is tricky with standard Qt layouts directly. QGraphicsScene is better.
        # Let's attempt a simplified version by overriding paintEvent for the whole keyboard
        # or carefully managing fixed sizes and positions.

        # Alternative: Fixed size and manual paint or QGraphicsScene
        # For simplicity in this example, we'll use a QHBoxLayout and try to manage sizes.
        # This will NOT give a perfect piano look without significant tweaking or custom layout.

        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(0) # No space between key widgets themselves

        # Define key widths (these are approximate and need tuning for visual appeal)
        white_key_width = 23
        black_key_width = int(white_key_width * 0.6)
        white_key_height = 120
        black_key_height = int(white_key_height * 0.65)

        # We'll create white keys and then position black keys relative to them.
        # This is where QGraphicsScene would shine. With QLayouts, it's harder.

        # Create all key widgets first
        for midi_note in range(self.START_MIDI_NOTE, self.END_MIDI_NOTE + 1):
            is_black = self._is_black_key(midi_note)
            key_widget = PianoKeyWidget(midi_note, is_black, self)
            self.keys[midi_note] = key_widget

            # Initial sizing (will be imperfect with simple QHBoxLayout for piano)
            if is_black:
                key_widget.setFixedSize(black_key_width, black_key_height)
                key_widget.setStyleSheet("background-color: #222222; border: 1px solid black;")
            else:
                key_widget.setFixedSize(white_key_width, white_key_height)
                key_widget.setStyleSheet("background-color: white; border: 1px solid #777777;")
            
            # This simple addition to QHBoxLayout will just put them side-by-side.
            # self.main_layout.addWidget(key_widget) # DON'T DO THIS YET for black keys

        # Manual layout (simplified - for a real piano, this needs to be more precise)
        # This part is the most complex for a realistic look without QGraphicsScene.
        current_x = 0
        for midi_note in range(self.START_MIDI_NOTE, self.END_MIDI_NOTE + 1):
            key_widget = self.keys[midi_note]
            if not key_widget.is_black:
                key_widget.setGeometry(current_x, 0, white_key_width, white_key_height)
                key_widget.raise_() # Ensure white keys are generally behind
                current_x += white_key_width
        
        # Now position black keys (this needs to be relative to the white keys)
        # This is a very simplified positioning logic.
        white_key_idx = 0
        for midi_note in range(self.START_MIDI_NOTE, self.END_MIDI_NOTE + 1):
            is_black = self._is_black_key(midi_note)
            pitch_class = midi_note % 12

            if not is_black:
                 # Find the white key widget that this black key might be 'between'
                # This logic is rough.
                white_key_ref_note = midi_note 
                # If we are C, black key is C#. If D, black is D#. If E, NO black.
                # If F, black is F#. If G, black is G#. If A, black is A#. If B, NO black.

                # Find the white key that this black key is "attached" to.
                # A C# is attached to C. A D# to D. F# to F. G# to G. A# to A.
                
                # We need to find the x-position of the white key to the left (or current if it's C,F)
                # This is where a proper geometric calculation based on key patterns is needed.
                # For example, a C# key starts roughly 2/3 of the way into a C key.
                if self._is_black_key(midi_note + 1): # Is there a black key to my right?
                    black_key_widget = self.keys.get(midi_note + 1)
                    if black_key_widget:
                        # Position black_key_widget partially over current white_key_widget
                        white_key_widget_geom = self.keys[midi_note].geometry()
                        # Position black key slightly offset from the right edge of the white key
                        # This needs to be calculated based on the white key it sits "between"
                        # For C#, it's over C and D. Position relative to C.
                        
                        # Simplified: position based on the white key it's "mostly" over
                        # C# (1) is after C (0). D# (3) is after D (2). F# (6) is after F (5). etc.
                        
                        pk_left_white = self.keys.get(midi_note) # The white key to its "logical" left
                        
                        if pk_left_white and not pk_left_white.is_black: # Ensure it's a white key
                            x_pos_black = pk_left_white.x() + white_key_width - (black_key_width // 2) -2 # approx
                            # Check if the next key is not also black (e.g. E-F gap)
                            # This positioning is very tricky with fixed geometry and no graphics scene.
                            # Standard pattern of offsets:
                            # C#: +0.66 * WKW from C
                            # D#: +0.66 * WKW from D
                            # F#: +0.66 * WKW from F
                            # G#: +0.66 * WKW from G
                            # A#: +0.66 * WKW from A
                            if pitch_class in [0, 2, 5, 7, 9]: # C, D, F, G, A (notes that can have a black key to their right)
                                if (midi_note + 1) <= self.END_MIDI_NOTE and self.keys[midi_note+1].is_black:
                                    black_key_to_place = self.keys[midi_note+1]
                                    black_key_to_place.setGeometry(
                                        pk_left_white.x() + int(white_key_width * 0.55), # Fine tune this
                                        0,
                                        black_key_width,
                                        black_key_height
                                    )
                                    black_key_to_place.raise_() # Black keys on top
                white_key_idx +=1


        # Set a fixed height for the keyboard based on white key height
        self.setFixedHeight(white_key_height + 10) # +10 for margins/border
        self.setMinimumWidth(current_x + 10) # Total width of white keys


    def handle_note_on(self, midi_note: int):
        if key_widget := self.keys.get(midi_note):
            key_widget.set_pressed(True)

    def handle_note_off(self, midi_note: int):
        if key_widget := self.keys.get(midi_note):
            key_widget.set_pressed(False)

    def update_active_notes(self, active_notes_midi: List[int]):
        """
        Updates the keyboard based on a list of currently active MIDI notes.
        """
        all_notes_on_keyboard = set(self.keys.keys())
        pressed_notes = set(active_notes_midi)

        for note in all_notes_on_keyboard:
            key_widget = self.keys[note]
            if note in pressed_notes:
                if not key_widget.is_pressed:
                    key_widget.set_pressed(True)
            else:
                if key_widget.is_pressed:
                    key_widget.set_pressed(False)