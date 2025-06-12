# --- ChordTheory Class ---
from collections import OrderedDict
import json
import logging
from pathlib import Path
from typing import Any, Dict, FrozenSet, Optional, Set, Tuple



# --- Constants ---
DEFAULT_ZMQ_PUB_PORT = 5557
DEFAULT_MIN_NOTES_FOR_CHORD = 2
DEFAULT_CHORD_BUFFER_TIME_ON = 0.015

# Default path for chord definitions JSON file
# load from data folder one level back from this module 
DEFAULT_CHORD_CONFIG_PATH = str(Path(__file__).resolve().parent.parent / "data" / "chord_definitions.json")

# Default log level for the application
DEFAULT_LOG_LEVEL = "INFO"
MIN_ACCEPTABLE_CHORD_SCORE = 0.6 # Threshold for chord recognition

# --- Logging Setup ---
logger = logging.getLogger(__name__) # Initial logger, will be configured in main

class ChordTheory:
    NOTE_PITCH_CLASSES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    
    # CHORD_DEFINITIONS based on the formula image and discussion
    CHORD_DEFINITIONS: Dict[str, Tuple[str, FrozenSet[int]]] = OrderedDict([
        # --- MAJOR ---
        ('maj', ("Major Triad", frozenset([0, 4, 7]))),
        ('add4', ("Major Add 4", frozenset([0, 4, 5, 7]))),
        ('6', ("Major Sixth", frozenset([0, 4, 7, 9]))),
        ('6/9', ("Major Six Nine", frozenset([0, 2, 4, 7, 9]))),
        ('maj7', ("Major 7th", frozenset([0, 4, 7, 11]))),
        ('maj9', ("Major 9th", frozenset([0, 2, 4, 7, 11]))),
        ('maj11_formula', ("Major 11th (Formula)", frozenset([0, 2, 4, 5, 7, 11]))),
        ('maj13_formula', ("Major 13th (Formula)", frozenset([0, 2, 4, 5, 7, 9, 11]))),
        ('maj7#11', ("Major 7th Sharp 11th", frozenset([0, 4, 6, 7, 11]))),
        ('majb5', ("Major Flat 5", frozenset([0, 4, 6]))),

        # --- MINOR ---
        ('min', ("Minor Triad", frozenset([0, 3, 7]))),
        ('madd4', ("Minor Add 4", frozenset([0, 3, 5, 7]))),
        ('min6', ("Minor Sixth", frozenset([0, 3, 7, 9]))),
        ('min7', ("Minor 7th", frozenset([0, 3, 7, 10]))),
        ('madd9', ("Minor Add 9", frozenset([0, 2, 3, 7]))),
        ('m6/9', ("Minor Six Nine", frozenset([0, 2, 3, 7, 9]))),
        ('min9', ("Minor 9th", frozenset([0, 2, 3, 7, 10]))),
        ('min11_formula', ("Minor 11th (Formula)", frozenset([0, 2, 3, 5, 7, 10]))),
        ('min13_formula', ("Minor 13th (Formula)", frozenset([0, 2, 3, 5, 7, 9, 10]))),
        ('minMaj7', ("Minor Major 7th", frozenset([0, 3, 7, 11]))),
        ('minMaj9', ("Minor Major 9th", frozenset([0, 2, 3, 7, 11]))),
        ('minMaj11_formula', ("Minor Major 11th (Formula)", frozenset([0, 2, 3, 5, 7, 11]))),
        ('minMaj13_formula', ("Minor Major 13th (Formula)", frozenset([0, 2, 3, 5, 7, 9, 11]))),
        ('min7b5', ("Half-Diminished 7th", frozenset([0, 3, 6, 10]))), # ø or m7-5

        # --- DOMINANT ---
        ('7', ("Dominant 7th", frozenset([0, 4, 7, 10]))),
        ('9', ("Dominant 9th", frozenset([0, 2, 4, 7, 10]))),
        ('11', ("Dominant 11th (no 3rd)", frozenset([0, 2, 5, 7, 10]))), # Common practical
        ('dom11_formula', ("Dominant 11th (Formula, with 3rd)", frozenset([0, 2, 4, 5, 7, 10]))),
        ('13', ("Dominant 13th (no 11th)", frozenset([0, 2, 4, 7, 9, 10]))), # Common practical
        ('dom13_formula', ("Dominant 13th (Formula, with P11)", frozenset([0, 2, 4, 5, 7, 9, 10]))),
        ('7#5', ("Dominant 7th Sharp 5", frozenset([0, 4, 8, 10]))), # aug7

        # --- OTHER Common Chords ---
        ('sus4', ("Suspended 4th", frozenset([0, 5, 7]))),
        ('sus2', ("Suspended 2nd", frozenset([0, 2, 7]))),
        ('7sus4', ("Dominant 7th Suspended 4th", frozenset([0, 5, 7, 10]))),
        ('dim', ("Diminished Triad", frozenset([0, 3, 6]))),
        ('aug', ("Augmented Triad", frozenset([0, 4, 8]))),
        ('dim7', ("Diminished 7th", frozenset([0, 3, 6, 9]))),
        ('7b5', ("Dominant 7th Flat 5", frozenset([0, 4, 6, 10]))),
        ('7b9', ("Dominant 7th Flat 9", frozenset([0, 1, 4, 7, 10]))),
        ('7#9', ("Dominant 7th Sharp 9", frozenset([0, 3, 4, 7, 10]))), # #9 is same PC as m3
        ('5', ("Power Chord", frozenset([0, 7]))),
    ])

    INTERVAL_NAMES = {
        0: "R", 1: "b2", 2: "2", 3: "b3", 4: "3", 5: "4",
        6: "b5/#4", 7: "5", 8: "#5/b6", 9: "6", 10: "b7", 11: "M7"
    }
    EXT_INTERVAL_NAMES = { # For extensions, often more specific naming is used
        0: "R", 1: "b9", 2: "9", 3: "m3/#9", 4: "M3", 5: "11/P4", # P4 for perfect 4th
        6: "#11/b5", 7: "P5", 8: "#5/b13", 9: "13/M6", 10: "m7", 11: "M7"
    }

    @classmethod
    def load_chord_definitions(cls, config_path: str = DEFAULT_CHORD_CONFIG_PATH) -> None:
        # (Identical to previous enhanced script - no changes needed here)
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.info(f"Chord definition file not found at '{config_path}'. Using default definitions.")
                return

            with open(config_file, 'r') as f:
                custom_chords = json.load(f)
            
            loaded_definitions = OrderedDict()
            for chord_type, data in custom_chords.items():
                intervals = data.get('intervals')
                name = data.get('name')
                if isinstance(intervals, list) and all(isinstance(i, int) for i in intervals) and isinstance(name, str):
                    loaded_definitions[chord_type] = (name, frozenset(intervals))
                    logger.debug(f"Loaded custom chord: {chord_type} - {name} {intervals}")
                else:
                    logger.warning(f"Skipping invalid chord definition for '{chord_type}' in '{config_path}'.")
            
            if loaded_definitions:
                cls.CHORD_DEFINITIONS = loaded_definitions
                logger.info(f"Successfully loaded {len(loaded_definitions)} chord definitions from '{config_path}'.")
            else:
                logger.warning(f"No valid chord definitions found in '{config_path}'. Using default definitions.")

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from '{config_path}': {e}. Using default definitions.")
        except Exception as e:
            logger.error(f"Failed to load chord definitions from '{config_path}': {e}. Using default definitions.")


    @staticmethod
    def midi_to_pitch_class_name(midi_note: int) -> str:
        # (Identical)
        if not (0 <= midi_note <= 127):
            return "Invalid"
        return ChordTheory.NOTE_PITCH_CLASSES[midi_note % 12]

    @classmethod
    def interval_to_name(cls, interval: int, use_extended_names: bool = False) -> str:
        # (Identical)
        names_map = cls.EXT_INTERVAL_NAMES if use_extended_names else cls.INTERVAL_NAMES
        return names_map.get(interval % 12, str(interval))

    @classmethod
    def recognize_chord(cls, played_midi_notes: Set[int], min_notes_for_chord: int) -> Optional[Dict[str, Any]]:
        # (Identical to previous enhanced script - logic for recognition, scoring, and output structure is the same)
        if len(played_midi_notes) < min_notes_for_chord:
            return None

        sorted_played_midi_notes = sorted(list(played_midi_notes))
        lowest_midi_note = sorted_played_midi_notes[0]
        
        played_pitch_classes = frozenset(note % 12 for note in sorted_played_midi_notes)

        best_match_info = {
            'score': -1.0, 'root_pc': -1, 'chord_type': None, 'chord_desc': None,
            'defined_intervals': frozenset(), 'matched_defined_intervals': frozenset(),
            'extra_played_pcs_rel_to_root': frozenset()
        }

        for root_pc_candidate in range(12):
            relative_played_pcs = frozenset((pc - root_pc_candidate + 12) % 12 for pc in played_pitch_classes)
            for chord_type_def, (desc_name_def, defined_intervals_def) in cls.CHORD_DEFINITIONS.items():
                intersection = relative_played_pcs & defined_intervals_def
                union = relative_played_pcs | defined_intervals_def
                score = len(intersection) / len(union) if union else 0.0

                if score > best_match_info['score']:
                    best_match_info.update({
                        'score': score, 'root_pc': root_pc_candidate, 'chord_type': chord_type_def,
                        'chord_desc': desc_name_def, 'defined_intervals': defined_intervals_def,
                        'matched_defined_intervals': intersection,
                        'extra_played_pcs_rel_to_root': relative_played_pcs - defined_intervals_def
                    })
                elif score == best_match_info['score'] and score > 0:
                    current_match_strength = len(intersection) + len(defined_intervals_def) * 0.1
                    prev_match_strength = len(best_match_info['matched_defined_intervals']) + \
                                          len(best_match_info['defined_intervals']) * 0.1
                    if current_match_strength > prev_match_strength:
                        best_match_info.update({
                            'score': score, 'root_pc': root_pc_candidate, 'chord_type': chord_type_def,
                            'chord_desc': desc_name_def, 'defined_intervals': defined_intervals_def,
                            'matched_defined_intervals': intersection,
                            'extra_played_pcs_rel_to_root': relative_played_pcs - defined_intervals_def
                        })
        
        if best_match_info['score'] < MIN_ACCEPTABLE_CHORD_SCORE:
            return None

        recognized_root_pc = best_match_info['root_pc']
        root_name = cls.midi_to_pitch_class_name(recognized_root_pc)
        actual_bass_pc = lowest_midi_note % 12
        actual_bass_name = cls.midi_to_pitch_class_name(actual_bass_pc)
        chord_type_name = best_match_info['chord_type']
        full_chord_name = f"{root_name}{chord_type_name}"
        inversion_text = "Root Position"
        bass_interval_rel_to_root = (actual_bass_pc - recognized_root_pc + 12) % 12
        sorted_defined_intervals = sorted(list(best_match_info['defined_intervals']))

        if bass_interval_rel_to_root != 0:
            full_chord_name += f"/{actual_bass_name}"
            try:
                inversion_index = sorted_defined_intervals.index(bass_interval_rel_to_root)
                if inversion_index == 1: inversion_text = "1st Inversion"
                elif inversion_index == 2: inversion_text = "2nd Inversion"
                elif inversion_index == 3: inversion_text = "3rd Inversion"
                else: inversion_text = f"Inversion (bass is {inversion_index+1}th tone)"
            except ValueError:
                inversion_text = "Slash Chord (bass not a core tone of root chord)"
        
        octave_span = (sorted_played_midi_notes[-1] - lowest_midi_note) / 12.0
        voicing_density_text = "N/A"
        if len(sorted_played_midi_notes) >= 2:
            if len(sorted_played_midi_notes) == 2 : voicing_density_text = "Interval"
            elif octave_span < 1.0: voicing_density_text = "Very Close Voicing"
            elif octave_span < 1.5: voicing_density_text = "Close Voicing"
            elif octave_span < 2.5: voicing_density_text = "Moderately Open Voicing"
            else: voicing_density_text = "Very Open (Spread) Voicing"

        intervals_from_actual_bass = sorted(list(frozenset(
            (pc - actual_bass_pc + 12) % 12 for pc in played_pitch_classes )))
        
        played_root_midi_note = next((note for note in sorted_played_midi_notes if note % 12 == recognized_root_pc), None)
        
        result = {
            'full_chord_name': full_chord_name, 'root_note_pc': recognized_root_pc, 'root_note_name': root_name,
            'played_root_midi_note': played_root_midi_note, 'bass_note_midi': lowest_midi_note,
            'bass_note_pc': actual_bass_pc, 'bass_note_name': actual_bass_name, 'chord_type': chord_type_name,
            'chord_description': best_match_info['chord_desc'], 'inversion_type': inversion_text,
            'score': round(best_match_info['score'], 3), 'played_notes_midi': sorted_played_midi_notes,
            'played_pitch_classes': sorted(list(played_pitch_classes)),
            'defined_intervals_of_matched_chord': sorted_defined_intervals,
            'matched_defined_intervals_rel_to_root': sorted(list(best_match_info['matched_defined_intervals'])),
            'extra_played_intervals_rel_to_root': sorted(list(best_match_info['extra_played_pcs_rel_to_root'])),
            'all_played_intervals_rel_to_root': sorted(list( (pc - recognized_root_pc + 12) % 12 for pc in played_pitch_classes)),
            'octave_span_played_notes': round(octave_span, 2), 'voicing_density_description': voicing_density_text,
            'intervals_from_actual_bass_pc': intervals_from_actual_bass,
        }
        return result
