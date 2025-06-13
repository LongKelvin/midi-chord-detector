# --- ChordTheory Class ---
from collections import OrderedDict
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, FrozenSet, Optional, Set, Tuple, List

from utils.utils import resource_path

# --- Constants ---
DEFAULT_ZMQ_PUB_PORT = 5557
DEFAULT_MIN_NOTES_FOR_CHORD = 2
DEFAULT_CHORD_BUFFER_TIME_ON = 0.015

# Default path for chord definitions JSON file
DEFAULT_CHORD_CONFIG_PATH = resource_path(
    os.path.join("data", "chord_definitions.json")
)

# Default log level for the application
DEFAULT_LOG_LEVEL = "INFO"
MIN_ACCEPTABLE_CHORD_SCORE = 0.6  # Threshold for chord recognition

# --- Logging Setup ---
logger = logging.getLogger(__name__)  # Initial logger, will be configured in main

class ChordTheory:
    NOTE_PITCH_CLASSES = [
        "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
    ]

    # Interval weights for scoring
    INTERVAL_WEIGHTS = {
        0: 0.8,   # Root
        3: 1.0,   # m3
        4: 1.0,   # M3
        7: 0.5,   # P5
        10: 1.0,  # b7
        11: 1.0,  # M7
        1: 0.3,   # b9
        2: 0.3,   # 9
        5: 0.3,   # 11
        6: 0.3,   # #11/b5
        8: 0.3,   # #5/b13
        9: 0.3,   # 13
    }

    # CHORD_DEFINITIONS with core and optional intervals for jazz support
    CHORD_DEFINITIONS: Dict[str, Tuple[str, Dict[str, FrozenSet[int]]]] = OrderedDict(
        [
            # --- MAJOR ---
            ('maj', ("Major Triad", {'core': frozenset([0, 4, 7]), 'optional': frozenset([])})),
            ('add4', ("Major Add 4", {'core': frozenset([0, 4, 7]), 'optional': frozenset([5])})),
            ('6', ("Major Sixth", {'core': frozenset([0, 4, 7]), 'optional': frozenset([9])})),
            ('6/9', ("Major Six Nine", {'core': frozenset([0, 4, 7]), 'optional': frozenset([2, 9])})),
            ('maj7', ("Major 7th", {'core': frozenset([0, 4, 7, 11]), 'optional': frozenset([])})),
            ('maj9', ("Major 9th", {'core': frozenset([0, 4, 7, 11]), 'optional': frozenset([2])})),
            ('maj11', ("Major 11th", {'core': frozenset([0, 4, 7, 11]), 'optional': frozenset([2, 5])})),
            ('maj13', ("Major 13th", {'core': frozenset([0, 4, 7, 11]), 'optional': frozenset([2, 5, 9])})),
            ('maj7#11', ("Major 7th Sharp 11th", {'core': frozenset([0, 4, 7, 11]), 'optional': frozenset([6])})),
            ('majb5', ("Major Flat 5", {'core': frozenset([0, 4, 6]), 'optional': frozenset([])})),

            # --- MINOR ---
            ('min', ("Minor Triad", {'core': frozenset([0, 3, 7]), 'optional': frozenset([])})),
            ('madd4', ("Minor Add 4", {'core': frozenset([0, 3, 7]), 'optional': frozenset([5])})),
            ('min6', ("Minor Sixth", {'core': frozenset([0, 3, 7]), 'optional': frozenset([9])})),
            ('min7', ("Minor 7th", {'core': frozenset([0, 3, 7, 10]), 'optional': frozenset([])})),
            ('madd9', ("Minor Add 9", {'core': frozenset([0, 3, 7]), 'optional': frozenset([2])})),
            ('m6/9', ("Minor Six Nine", {'core': frozenset([0, 3, 7]), 'optional': frozenset([2, 9])})),
            ('min9', ("Minor 9th", {'core': frozenset([0, 3, 7, 10]), 'optional': frozenset([2])})),
            ('min11', ("Minor 11th", {'core': frozenset([0, 3, 7, 10]), 'optional': frozenset([2, 5])})),
            ('min13', ("Minor 13th", {'core': frozenset([0, 3, 7, 10]), 'optional': frozenset([2, 5, 9])})),
            ('minMaj7', ("Minor Major 7th", {'core': frozenset([0, 3, 7, 11]), 'optional': frozenset([])})),
            ('minMaj9', ("Minor Major 9th", {'core': frozenset([0, 3, 7, 11]), 'optional': frozenset([2])})),
            ('min7b5', ("Half-Diminished 7th", {'core': frozenset([0, 3, 6, 10]), 'optional': frozenset([])})),

            # --- DOMINANT ---
            ('7', ("Dominant 7th", {'core': frozenset([0, 4, 10]), 'optional': frozenset([7])})),
            ('9', ("Dominant 9th", {'core': frozenset([0, 4, 10]), 'optional': frozenset([2, 7])})),
            ('11', ("Dominant 11th", {'core': frozenset([0, 4, 10]), 'optional': frozenset([2, 5, 7])})),
            ('13', ("Dominant 13th", {'core': frozenset([0, 4, 10]), 'optional': frozenset([2, 7, 9])})),
            ('7#5', ("Dominant 7th Sharp 5", {'core': frozenset([0, 4, 10]), 'optional': frozenset([8])})),
            ('7b9', ("Dominant 7th Flat 9", {'core': frozenset([0, 4, 10]), 'optional': frozenset([1, 7])})),
            ('7#9', ("Dominant 7th Sharp 9", {'core': frozenset([0, 4, 10]), 'optional': frozenset([3, 7])})),
            ('7b13', ("Dominant 7th Flat 13", {'core': frozenset([0, 4, 10]), 'optional': frozenset([7, 8])})),
            ('7#5b9', ("Dominant 7th Sharp 5 Flat 9", {'core': frozenset([0, 4, 10]), 'optional': frozenset([1, 8])})),
            ('9#5', ("Dominant 9th Sharp 5", {'core': frozenset([0, 4, 10]), 'optional': frozenset([2, 8])})),

            # --- OTHER Common Chords ---
            ('sus4', ("Suspended 4th", {'core': frozenset([0, 5, 7]), 'optional': frozenset([])})),
            ('sus2', ("Suspended 2nd", {'core': frozenset([0, 2, 7]), 'optional': frozenset([])})),
            ('7sus4', ("Dominant 7th Suspended 4th", {'core': frozenset([0, 5, 10]), 'optional': frozenset([7])})),
            ('dim', ("Diminished Triad", {'core': frozenset([0, 3, 6]), 'optional': frozenset([])})),
            ('aug', ("Augmented Triad", {'core': frozenset([0, 4, 8]), 'optional': frozenset([])})),
            ('dim7', ("Diminished 7th", {'core': frozenset([0, 3, 6, 9]), 'optional': frozenset([])})),
            ('7b5', ("Dominant 7th Flat 5", {'core': frozenset([0, 4, 6, 10]), 'optional': frozenset([])})),
            ('5', ("Power Chord", {'core': frozenset([0, 7]), 'optional': frozenset([])})),
        ]
    )

    INTERVAL_NAMES = {
        0: "R", 1: "b2", 2: "2", 3: "b3", 4: "3", 5: "4", 6: "b5/#4",
        7: "5", 8: "#5/b6", 9: "6", 10: "b7", 11: "M7"
    }
    EXT_INTERVAL_NAMES = {
        0: "R", 1: "b9", 2: "9", 3: "m3/#9", 4: "M3", 5: "11/P4",
        6: "#11/b5", 7: "P5", 8: "#5/b13", 9: "13/M6", 10: "m7", 11: "M7"
    }

    def __init__(self, genre: str = 'jazz'):
        self.genre = genre
        self.recent_chords: List[Dict[str, Any]] = []  # Track last 3 chords for context
        self.load_chord_definitions()

    @classmethod
    def load_chord_definitions(cls, config_path: str = DEFAULT_CHORD_CONFIG_PATH) -> None:
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.info(f"Chord definition file not found at '{config_path}'. Using default definitions.")
                return

            with open(config_file, "r") as f:
                custom_chords = json.load(f)

            loaded_definitions = OrderedDict()
            for chord_type, data in custom_chords.items():
                core_intervals = data.get("core_intervals")
                optional_intervals = data.get("optional_intervals", [])
                name = data.get("name")
                if (
                    isinstance(core_intervals, list)
                    and all(isinstance(i, int) for i in core_intervals)
                    and isinstance(optional_intervals, list)
                    and all(isinstance(i, int) for i in optional_intervals)
                    and isinstance(name, str)
                ):
                    loaded_definitions[chord_type] = (
                        name, {'core': frozenset(core_intervals), 'optional': frozenset(optional_intervals)}
                    )
                    logger.debug(f"Loaded custom chord: {chord_type} - {name} {core_intervals} {optional_intervals}")
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
        if not (0 <= midi_note <= 127):
            return "Invalid"
        return ChordTheory.NOTE_PITCH_CLASSES[midi_note % 12]

    @classmethod
    def interval_to_name(cls, interval: int, use_extended_names: bool = False) -> str:
        names_map = cls.EXT_INTERVAL_NAMES if use_extended_names else cls.INTERVAL_NAMES
        return names_map.get(interval % 12, str(interval))

    def adjust_score_for_context(self, chord_type: str, score: float) -> float:
        """Adjust score based on genre and recent chords."""
        if self.genre == 'jazz' and chord_type in ['7b13', '7#5', '7b9', '7#9', '7#5b9', '9#5']:
            score *= 1.2  # Boost jazz altered chords
        if self.recent_chords and self.recent_chords[-1].get('chord_type') in ['min7', 'min9']:
            if chord_type in ['7', '9', '13', '7b13', '7#5', '7b9', '7#9', '7#5b9']:  # Likely V7 in ii-V
                score *= 1.1
        return score

    @classmethod
    def calculate_weighted_score(cls, played_pcs: FrozenSet[int], core_intervals: FrozenSet[int],
                                optional_intervals: FrozenSet[int]) -> float:
        """Calculate score with weights for core/optional intervals and capped extra note penalty."""
        matched_core = played_pcs & core_intervals
        matched_optional = played_pcs & optional_intervals
        extra_notes = played_pcs - (core_intervals | optional_intervals)

        # Weighted score for matched intervals
        core_score = sum(cls.INTERVAL_WEIGHTS.get(i % 12, 0.3) for i in matched_core)
        optional_score = sum(cls.INTERVAL_WEIGHTS.get(i % 12, 0.3) for i in matched_optional)
        total_defined_weight = sum(cls.INTERVAL_WEIGHTS.get(i % 12, 0.3) for i in core_intervals)

        # Base score: core match strength, boosted by optional matches
        base_score = core_score / total_defined_weight if total_defined_weight else 0.0
        if optional_intervals:
            base_score += optional_score / (total_defined_weight * 2)  # Optional intervals contribute less

        # Penalty for extra notes (capped)
        penalty = min(len(extra_notes) * 0.05, 0.15)  # Max penalty 0.15
        final_score = max(base_score - penalty, 0.0)

        # Require core intervals for non-triads
        if len(core_intervals) > 3 and not core_intervals.issubset(played_pcs):
            return 0.0

        return final_score

    def recognize_chord(
        self, played_midi_notes: Set[int], min_notes_for_chord: int
    ) -> Optional[Dict[str, Any]]:
        if len(played_midi_notes) < min_notes_for_chord:
            return None

        sorted_played_midi_notes = sorted(list(played_midi_notes))
        lowest_midi_note = sorted_played_midi_notes[0]
        played_pitch_classes = frozenset(note % 12 for note in sorted_played_midi_notes)

        best_match_info = {
            "score": -1.0,
            "root_pc": -1,
            "chord_type": None,
            "chord_desc": None,
            "defined_intervals": {'core': frozenset(), 'optional': frozenset()},
            "matched_core_intervals": frozenset(),
            "matched_optional_intervals": frozenset(),
            "extra_played_pcs_rel_to_root": frozenset(),
        }

        for root_pc_candidate in range(12):
            relative_played_pcs = frozenset(
                (pc - root_pc_candidate + 12) % 12 for pc in played_pitch_classes
            )
            for chord_type_def, (desc_name_def, intervals_def) in self.CHORD_DEFINITIONS.items():
                core_intervals = intervals_def['core']
                optional_intervals = intervals_def['optional']
                score = self.calculate_weighted_score(relative_played_pcs, core_intervals, optional_intervals)
                score = self.adjust_score_for_context(chord_type_def, score)

                if score > best_match_info["score"]:
                    best_match_info.update({
                        "score": score,
                        "root_pc": root_pc_candidate,
                        "chord_type": chord_type_def,
                        "chord_desc": desc_name_def,
                        "defined_intervals": intervals_def,
                        "matched_core_intervals": relative_played_pcs & core_intervals,
                        "matched_optional_intervals": relative_played_pcs & optional_intervals,
                        "extra_played_pcs_rel_to_root": relative_played_pcs - (core_intervals | optional_intervals),
                    })
                elif score == best_match_info["score"] and score > 0:
                    # Tie-breaker: prefer chord with more matched core intervals or more complex chord
                    current_match_strength = len(relative_played_pcs & core_intervals) + len(core_intervals) * 0.1
                    prev_match_strength = len(best_match_info["matched_core_intervals"]) + len(best_match_info["defined_intervals"]['core']) * 0.1
                    if current_match_strength > prev_match_strength:
                        best_match_info.update({
                            "score": score,
                            "root_pc": root_pc_candidate,
                            "chord_type": chord_type_def,
                            "chord_desc": desc_name_def,
                            "defined_intervals": intervals_def,
                            "matched_core_intervals": relative_played_pcs & core_intervals,
                            "matched_optional_intervals": relative_played_pcs & optional_intervals,
                            "extra_played_pcs_rel_to_root": relative_played_pcs - (core_intervals | optional_intervals),
                        })

        if best_match_info["score"] < MIN_ACCEPTABLE_CHORD_SCORE:
            return None

        recognized_root_pc = best_match_info["root_pc"]
        root_name = self.midi_to_pitch_class_name(recognized_root_pc)
        actual_bass_pc = lowest_midi_note % 12
        actual_bass_name = self.midi_to_pitch_class_name(actual_bass_pc)
        chord_type_name = best_match_info["chord_type"]
        full_chord_name = f"{root_name}{chord_type_name}"
        inversion_text = "Root Position"
        bass_interval_rel_to_root = (actual_bass_pc - recognized_root_pc + 12) % 12
        sorted_core_intervals = sorted(list(best_match_info["defined_intervals"]['core']))

        if bass_interval_rel_to_root != 0:
            full_chord_name += f"/{actual_bass_name}"
            try:
                inversion_index = sorted_core_intervals.index(bass_interval_rel_to_root)
                if inversion_index == 1:
                    inversion_text = "1st Inversion"
                elif inversion_index == 2:
                    inversion_text = "2nd Inversion"
                elif inversion_index == 3:
                    inversion_text = "3rd Inversion"
                else:
                    inversion_text = f"Inversion (bass is {inversion_index+1}th tone)"
            except ValueError:
                # Check if bass is an optional interval
                if bass_interval_rel_to_root in best_match_info["defined_intervals"]['optional']:
                    inversion_text = "Slash Chord (bass is extension)"
                else:
                    inversion_text = "Slash Chord (bass not a core tone)"

        octave_span = (sorted_played_midi_notes[-1] - lowest_midi_note) / 12.0
        voicing_density_text = "N/A"
        if len(sorted_played_midi_notes) >= 2:
            if len(sorted_played_midi_notes) == 2:
                voicing_density_text = "Interval"
            elif octave_span < 1.0:
                voicing_density_text = "Very Close Voicing"
            elif octave_span < 1.5:
                voicing_density_text = "Close Voicing"
            elif octave_span < 2.5:
                voicing_density_text = "Moderately Open Voicing"
            else:
                voicing_density_text = "Very Open (Spread) Voicing"

        intervals_from_actual_bass = sorted(
            list(frozenset((pc - actual_bass_pc + 12) % 12 for pc in played_pitch_classes))
        )

        played_root_midi_note = next(
            (note for note in sorted_played_midi_notes if note % 12 == recognized_root_pc), None
        )

        result = {
            "full_chord_name": full_chord_name,
            "root_note_pc": recognized_root_pc,
            "root_note_name": root_name,
            "played_root_midi_note": played_root_midi_note,
            "bass_note_midi": lowest_midi_note,
            "bass_note_pc": actual_bass_pc,
            "bass_note_name": actual_bass_name,
            "chord_type": chord_type_name,
            "chord_description": best_match_info["chord_desc"],
            "inversion_type": inversion_text,
            "score": round(best_match_info["score"], 3),
            "played_notes_midi": sorted_played_midi_notes,
            "played_pitch_classes": sorted(list(played_pitch_classes)),
            "defined_intervals_core": sorted_core_intervals,
            "defined_intervals_optional": sorted(list(best_match_info["defined_intervals"]['optional'])),
            "matched_core_intervals": sorted(list(best_match_info["matched_core_intervals"])),
            "matched_optional_intervals": sorted(list(best_match_info["matched_optional_intervals"])),
            "extra_played_intervals_rel_to_root": sorted(list(best_match_info["extra_played_pcs_rel_to_root"])),
            "all_played_intervals_rel_to_root": sorted(list((pc - recognized_root_pc + 12) % 12 for pc in played_pitch_classes)),
            "octave_span_played_notes": round(octave_span, 2),
            "voicing_density_description": voicing_density_text,
            "intervals_from_actual_bass_pc": intervals_from_actual_bass,
        }

        self.recent_chords.append(result)
        if len(self.recent_chords) > 3:
            self.recent_chords.pop(0)  # Keep last 3 chords for context

        return result