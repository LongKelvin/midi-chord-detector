"""
Advanced Chord Analyzer with AI-Enhanced Recognition
Handles complex chords, melody separation, and jazz voicings
"""

from typing import Dict, List, Set, Tuple, Optional, Any
from collections import Counter, defaultdict
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ChordComplexity(Enum):
    SIMPLE = 1      # Triads, basic 7ths
    INTERMEDIATE = 2 # Extensions (9th, 11th, 13th)
    ADVANCED = 3    # Altered chords, complex jazz voicings
    EXPERIMENTAL = 4 # Quartal, polychords, etc.

@dataclass
class VoiceContext:
    """Represents the musical context for voice separation"""
    bass_register: Tuple[int, int] = (21, 60)    # A0 to C4
    chord_register: Tuple[int, int] = (36, 84)   # C2 to C6  
    melody_register: Tuple[int, int] = (60, 108) # C4 to C8
    sustain_threshold: float = 0.5  # Minimum duration to be considered chord tone

@dataclass
class ChordCandidate:
    """Represents a potential chord match"""
    root_pc: int
    chord_type: str
    chord_name: str
    score: float
    confidence: float
    complexity: ChordComplexity
    voice_separation: Dict[str, List[int]]
    missing_expected: List[int]
    extra_notes: List[int]
    context_bonus: float = 0.0

class AdvancedChordAnalyzer:
    """
    Advanced chord recognition with AI-enhanced features:
    - Voice separation (bass, chord tones, melody)
    - Context-aware scoring
    - Fuzzy matching for incomplete chords
    - Jazz voicing recognition
    - Machine learning-inspired pattern matching
    """
    
    def __init__(self):
        self.voice_context = VoiceContext()
        self.chord_history: List[ChordCandidate] = []
        self.pattern_weights = self._initialize_pattern_weights()
        self.jazz_substitutions = self._initialize_jazz_substitutions()
        
        # Enhanced chord definitions with flexibility scores
        self.enhanced_chord_defs = self._build_enhanced_definitions()
        
    def _initialize_pattern_weights(self) -> Dict[str, float]:
        """Initialize ML-inspired pattern weights for common musical contexts"""
        return {
            # Voice leading patterns
            'stepwise_bass': 1.2,
            'fifth_movement': 1.1,
            'chromatic_approach': 1.15,
            
            # Chord progression patterns  
            'ii_V_I': 1.3,
            'vi_ii_V': 1.25,
            'circle_of_fifths': 1.2,
            
            # Jazz patterns
            'tritone_sub': 1.4,
            'altered_dominant': 1.35,
            'extended_harmony': 1.25,
            
            # Classical patterns
            'secondary_dominant': 1.2,
            'neapolitan': 1.15,
            'augmented_sixth': 1.3,
        }
    
    def _initialize_jazz_substitutions(self) -> Dict[str, List[str]]:
        """Common jazz chord substitutions and equivalencies"""
        return {
            'm7': ['m6', 'm6/9', 'm9', 'm11'],
            '7': ['7sus4', '9', '13', '7alt'],
            'maj7': ['maj9', 'maj7#11', 'maj13'],
            'm7b5': ['dim7', 'ø7'],
            'dim7': ['7b9', '7#9b5'],
        }
    
    def _build_enhanced_definitions(self) -> Dict[str, Dict]:
        """Build enhanced chord definitions with flexibility and priority"""
        enhanced_defs = {}
        
        # Basic triads - very flexible
        enhanced_defs['maj'] = {
            'core': [0, 4],           # Root and third are essential
            'important': [7],          # Fifth is important but not critical
            'optional': [],
            'flexibility': 0.9,        # High flexibility for omitted notes
            'priority_order': [0, 4, 7],
            'complexity': ChordComplexity.SIMPLE
        }
        
        enhanced_defs['min'] = {
            'core': [0, 3],
            'important': [7], 
            'optional': [],
            'flexibility': 0.9,
            'priority_order': [0, 3, 7],
            'complexity': ChordComplexity.SIMPLE
        }
        
        enhanced_defs['aug'] = {
            'core': [0, 4, 8],           # Root, major third, augmented fifth
            'important': [],
            'optional': [],
            'flexibility': 0.9,
            'priority_order': [0, 4, 8],
            'complexity': ChordComplexity.INTERMEDIATE
        }
        
        enhanced_defs['add9'] = {
            'core': [0, 4, 7, 2],        # Major triad + 9th (no 7th) - all notes required
            'important': [],
            'optional': [],
            'flexibility': 0.6,          # Less flexible - all 4 notes should be present
            'priority_order': [0, 4, 7, 2],
            'complexity': ChordComplexity.INTERMEDIATE  # Higher complexity to prefer over simple triads
        }
        
        enhanced_defs['6'] = {
            'core': [0, 4, 9],           # Root, major third, 6th - essential for maj6
            'important': [7],            # Fifth is important 
            'optional': [],
            'flexibility': 0.7,          # Less flexible to avoid confusion with m7 chords
            'priority_order': [0, 4, 9, 7],
            'complexity': ChordComplexity.SIMPLE
        }
        
        enhanced_defs['m6'] = {
            'core': [0, 3, 7, 9],        # Minor triad + 6th
            'important': [],
            'optional': [],
            'flexibility': 0.7,          # Less flexible to avoid confusion with basic minor
            'priority_order': [0, 3, 7, 9],
            'complexity': ChordComplexity.SIMPLE
        }
        
        enhanced_defs['sus2'] = {
            'core': [0, 2, 7],           # Root, 2nd, 5th
            'important': [],
            'optional': [],
            'flexibility': 0.8,          # Slightly more flexible than before
            'priority_order': [0, 2, 7],
            'complexity': ChordComplexity.SIMPLE
        }
        
        # Seventh chords - moderately flexible
        enhanced_defs['7'] = {
            'core': [0, 4, 10],        # Root, third, seventh
            'important': [7],          # Fifth often omitted in jazz
            'optional': [],
            'flexibility': 0.8,
            'priority_order': [0, 4, 10, 7],
            'complexity': ChordComplexity.SIMPLE
        }
        
        enhanced_defs['maj7'] = {
            'core': [0, 4, 11],
            'important': [7],
            'optional': [],
            'flexibility': 0.8,
            'priority_order': [0, 4, 11, 7],
            'complexity': ChordComplexity.SIMPLE
        }
        
        enhanced_defs['m7'] = {
            'core': [0, 3, 10],
            'important': [7],
            'optional': [],
            'flexibility': 0.8,
            'priority_order': [0, 3, 10, 7],
            'complexity': ChordComplexity.SIMPLE
        }
        
        # Extended chords - more specific but allow omissions
        enhanced_defs['9'] = {
            'core': [0, 4, 10, 2],     # Include 9th as core for 9th chords
            'important': [],
            'optional': [7],           # Fifth is often omitted
            'flexibility': 0.7,
            'priority_order': [0, 4, 10, 2, 7],
            'complexity': ChordComplexity.INTERMEDIATE
        }
        
        enhanced_defs['m9'] = {
            'core': [0, 3, 10, 2],
            'important': [],
            'optional': [7],
            'flexibility': 0.7,
            'priority_order': [0, 3, 10, 2, 7],
            'complexity': ChordComplexity.INTERMEDIATE
        }
        
        enhanced_defs['maj9'] = {
            'core': [0, 4, 11, 2],
            'important': [],
            'optional': [7],
            'flexibility': 0.7,
            'priority_order': [0, 4, 11, 2, 7],
            'complexity': ChordComplexity.INTERMEDIATE
        }
        
        # Advanced jazz chords
        enhanced_defs['7alt'] = {
            'core': [0, 4, 10],
            'important': [1, 3, 6, 8], # b9, #9, b5, #5
            'optional': [7],
            'flexibility': 0.6,
            'priority_order': [0, 4, 10, 1, 8, 3, 6],
            'complexity': ChordComplexity.ADVANCED
        }
        
        enhanced_defs['m11'] = {
            'core': [0, 3, 10, 2, 5],
            'important': [],
            'optional': [7],
            'flexibility': 0.6,
            'priority_order': [0, 3, 10, 2, 5, 7],
            'complexity': ChordComplexity.INTERMEDIATE
        }
        
        enhanced_defs['13'] = {
            'core': [0, 4, 10, 9],       # Root, 3rd, 7th, 13th - essential for 13th chord
            'important': [2],            # 9th is important in 13th chords
            'optional': [7, 5],          # Fifth and eleventh often omitted
            'flexibility': 0.7,          # More flexible to allow omissions
            'priority_order': [0, 4, 10, 9, 2, 7, 5],
            'complexity': ChordComplexity.ADVANCED  # Higher complexity for better priority
        }
        
        # Add more complex chords...
        enhanced_defs.update(self._add_complex_jazz_chords())
        
        return enhanced_defs
    
    def _add_complex_jazz_chords(self) -> Dict[str, Dict]:
        """Add complex jazz chord definitions"""
        complex_chords = {}
        
        # Altered dominant variations
        complex_chords['7b9'] = {
            'core': [0, 4, 10, 1],
            'important': [],
            'optional': [7],
            'flexibility': 0.7,
            'priority_order': [0, 4, 10, 1, 7],
            'complexity': ChordComplexity.ADVANCED
        }
        
        complex_chords['7#9'] = {
            'core': [0, 4, 10, 3],
            'important': [],
            'optional': [7],
            'flexibility': 0.7,
            'priority_order': [0, 4, 10, 3, 7],
            'complexity': ChordComplexity.ADVANCED
        }
        
        complex_chords['7#5'] = {
            'core': [0, 4, 10, 8],
            'important': [],
            'optional': [],
            'flexibility': 0.8,
            'priority_order': [0, 4, 10, 8],
            'complexity': ChordComplexity.ADVANCED
        }
        
        # Suspended chords
        complex_chords['sus4'] = {
            'core': [0, 5, 7],
            'important': [],
            'optional': [],
            'flexibility': 0.8,          # Less flexible to ensure exact match
            'priority_order': [0, 5, 7],
            'complexity': ChordComplexity.SIMPLE
        }
        
        complex_chords['7sus4'] = {
            'core': [0, 5, 10],          # Root, 4th, 7th - ALL required for 7sus4
            'important': [],             # No important intervals
            'optional': [7],             # Fifth is optional
            'flexibility': 0.5,          # Very strict - must have the 7th
            'priority_order': [0, 5, 10, 7],
            'complexity': ChordComplexity.INTERMEDIATE
        }
        
        # Half-diminished and diminished
        complex_chords['m7b5'] = {
            'core': [0, 3, 6, 10],
            'important': [],
            'optional': [],
            'flexibility': 0.8,
            'priority_order': [0, 3, 6, 10],
            'complexity': ChordComplexity.INTERMEDIATE
        }
        
        complex_chords['dim7'] = {
            'core': [0, 3, 6, 9],
            'important': [],
            'optional': [],
            'flexibility': 0.8,
            'priority_order': [0, 3, 6, 9],
            'complexity': ChordComplexity.INTERMEDIATE
        }
        
        return complex_chords
    
    def separate_voices(self, midi_notes: List[int], 
                       note_durations: Optional[Dict[int, float]] = None) -> Dict[str, List[int]]:
        """
        Intelligent voice separation using register analysis and duration
        """
        if not midi_notes:
            return {'bass': [], 'chord': [], 'melody': []}
        
        # Sort notes by pitch
        sorted_notes = sorted(midi_notes)
        
        # Basic register separation
        bass_notes = [n for n in sorted_notes if n <= self.voice_context.bass_register[1]]
        melody_notes = [n for n in sorted_notes if n >= self.voice_context.melody_register[0]]
        chord_notes = [n for n in sorted_notes 
                      if self.voice_context.chord_register[0] <= n <= self.voice_context.chord_register[1]]
        
        # Advanced separation logic
        voices = {'bass': [], 'chord': [], 'melody': []}
        
        # Bass: usually the lowest note(s)
        if bass_notes:
            # Take lowest note and any notes within a perfect fifth
            bass_root = bass_notes[0]
            voices['bass'] = [n for n in bass_notes if n - bass_root <= 7]
        
        # Melody: identify outliers in upper register or notes with short duration
        if note_durations:
            # Notes with short duration likely melody
            short_notes = [n for n, dur in note_durations.items() 
                          if dur < self.voice_context.sustain_threshold]
            melody_candidates = list(set(melody_notes + short_notes))
        else:
            melody_candidates = melody_notes
        
        # Remove statistical outliers from chord consideration
        if len(sorted_notes) > 4:
            # If we have many notes, the highest ones are likely melody
            potential_melody = sorted_notes[-2:] if len(sorted_notes) > 6 else sorted_notes[-1:]
            melody_candidates.extend(potential_melody)
        
        voices['melody'] = list(set(melody_candidates))
        
        # Chord: everything else, but prioritize the middle register
        chord_candidates = [n for n in sorted_notes 
                           if n not in voices['bass'] and n not in voices['melody']]
        
        # Add back some melody notes if they form good chord intervals
        for melody_note in voices['melody'][:]:
            # Check if melody note forms good intervals with chord notes
            if self._forms_chord_intervals(melody_note, chord_candidates):
                chord_candidates.append(melody_note)
                voices['melody'].remove(melody_note)
        
        voices['chord'] = chord_candidates
        
        return voices
    
    def _forms_chord_intervals(self, note: int, chord_notes: List[int]) -> bool:
        """Check if a note forms good chord intervals with existing chord notes"""
        if not chord_notes:
            return False
        
        good_intervals = {3, 4, 7, 9, 10, 11}  # m3, M3, P5, M6, m7, M7
        
        for chord_note in chord_notes:
            interval = abs(note - chord_note) % 12
            if interval in good_intervals:
                return True
        return False
    
    def analyze_chord_fuzzy(self, midi_notes: List[int], 
                          note_durations: Optional[Dict[int, float]] = None) -> Optional[ChordCandidate]:
        """
        Advanced fuzzy chord recognition with voice separation
        """
        if len(midi_notes) < 2:
            return None
        
        # Separate voices
        voices = self.separate_voices(midi_notes, note_durations)
        
        # Focus on bass + chord notes for chord identification
        chord_analysis_notes = voices['bass'] + voices['chord']
        
        if len(chord_analysis_notes) < 2:
            # Fall back to all notes if separation doesn't work
            chord_analysis_notes = midi_notes
            voices = {'bass': [min(midi_notes)], 'chord': midi_notes, 'melody': []}
        
        # Convert to pitch classes
        played_pcs = set(note % 12 for note in chord_analysis_notes)
        
        best_candidates = []
        
        # Try each possible root with bass note preference
        bass_note_pc = min(chord_analysis_notes) % 12 if chord_analysis_notes else 0
        
        # Prioritize bass note and common roots
        root_candidates = []
        
        # First priority: bass note as root
        root_candidates.append((bass_note_pc, 1.0))
        
        # Second priority: other notes as potential roots
        for note in chord_analysis_notes:
            pc = note % 12
            if pc != bass_note_pc:
                # Give higher weight to lower notes (more likely to be roots)
                weight = 0.7 if note <= (min(chord_analysis_notes) + 12) else 0.5
                root_candidates.append((pc, weight))
        
        # Third priority: any other pitch class (for slash chords)
        for pc in range(12):
            if pc not in [candidate[0] for candidate in root_candidates]:
                root_candidates.append((pc, 0.3))
        
        for root_pc, root_weight in root_candidates:
            relative_pcs = set((pc - root_pc) % 12 for pc in played_pcs)
            
            # Check each chord type
            for chord_type, definition in self.enhanced_chord_defs.items():
                candidate = self._evaluate_chord_candidate(
                    root_pc, chord_type, definition, relative_pcs, voices, midi_notes, root_weight
                )
                if candidate and candidate.score > 0.3:  # Lower threshold for fuzzy matching
                    best_candidates.append(candidate)
        
        if not best_candidates:
            return None
        
        # Enhanced candidate selection: prefer more complete/complex chords in close ties
        def candidate_sort_key(candidate):
            # Primary: score + context_bonus
            # Secondary: prefer exact matches (no missing notes, no extra notes)
            # Tertiary: complexity (more complex chords preferred in ties)
            # Quaternary: confidence
            
            exact_match_bonus = 0.0
            if not candidate.missing_expected and not candidate.extra_notes:
                exact_match_bonus = 0.03  # Increased bonus for exact matches
            
            # Prefer simpler chord names when bass note is the root (no slash chords)
            simple_chord_bonus = 0.0
            if '/' not in candidate.chord_name:  # Not a slash chord
                simple_chord_bonus = 0.02
            
            complexity_weight = {
                ChordComplexity.SIMPLE: 0.0,
                ChordComplexity.INTERMEDIATE: 0.005,  # Reduced to not override exact matches
                ChordComplexity.ADVANCED: 0.01,
                ChordComplexity.EXPERIMENTAL: 0.015
            }.get(candidate.complexity, 0.0)
            
            total_score = (candidate.score + candidate.context_bonus + 
                          exact_match_bonus + simple_chord_bonus + complexity_weight)
            
            return (total_score, candidate.confidence, -len(candidate.missing_expected))
        
        # Sort candidates and check for close ties
        best_candidates.sort(key=candidate_sort_key, reverse=True)
        
        # If there's a close tie between top candidates, prefer the more complex chord
        if len(best_candidates) > 1:
            first_candidate = best_candidates[0]
            second_candidate = best_candidates[1]
            
            # Calculate actual scores
            first_total = first_candidate.score + first_candidate.context_bonus
            second_total = second_candidate.score + second_candidate.context_bonus
            score_diff = first_total - second_total
            
            # If scores are very close (within 0.05), prefer more complex chord
            if (score_diff < 0.05 and 
                second_candidate.complexity.value > first_candidate.complexity.value and
                second_candidate.confidence >= first_candidate.confidence - 0.1):
                final_candidate = self._apply_context_bonus(second_candidate)
            else:
                final_candidate = self._apply_context_bonus(first_candidate)
        else:
            final_candidate = self._apply_context_bonus(best_candidates[0])
        
        # Update history
        self.chord_history.append(final_candidate)
        if len(self.chord_history) > 10:
            self.chord_history.pop(0)
        
        return final_candidate
    
    def _evaluate_chord_candidate(self, root_pc: int, chord_type: str, 
                                definition: Dict, relative_pcs: Set[int],
                                voices: Dict[str, List[int]], 
                                all_notes: List[int], root_weight: float = 1.0) -> Optional[ChordCandidate]:
        """Evaluate how well the played notes match a chord definition"""
        
        core_intervals = set(definition['core'])
        important_intervals = set(definition.get('important', []))
        optional_intervals = set(definition.get('optional', []))
        flexibility = definition['flexibility']
        
        all_expected = core_intervals | important_intervals | optional_intervals
        
        # Calculate matches
        matched_core = relative_pcs & core_intervals
        matched_important = relative_pcs & important_intervals  
        matched_optional = relative_pcs & optional_intervals
        extra_notes = relative_pcs - all_expected
        
        # Missing notes
        missing_core = core_intervals - relative_pcs
        missing_important = important_intervals - relative_pcs
        
        # Fuzzy scoring algorithm with enhanced completeness bonus
        score = 0.0
        
        # Core intervals score (essential)
        if core_intervals:
            core_score = len(matched_core) / len(core_intervals)
            # Apply flexibility - allow some missing core intervals with penalty
            if missing_core:
                # Missing core intervals are heavily penalized
                missing_penalty = len(missing_core) * 0.3  # Increased penalty per missing core interval
                flexibility_bonus = flexibility * (len(matched_core) / len(core_intervals))
                core_score = max(0.0, min(1.0, core_score + flexibility_bonus - missing_penalty))
            score += core_score * 0.6
        
        # Important intervals score
        if important_intervals:
            important_score = len(matched_important) / len(important_intervals)
            score += important_score * 0.25
        
        # Optional intervals bonus
        if optional_intervals and matched_optional:
            optional_score = len(matched_optional) / len(optional_intervals)
            score += optional_score * 0.1
        
        # ENHANCED: Bonus for complete chords (all expected notes present)
        total_expected_notes = len(all_expected)
        total_matched_notes = len(matched_core) + len(matched_important) + len(matched_optional)
        
        if total_expected_notes > 0:
            completeness_ratio = total_matched_notes / total_expected_notes
            # Significant bonus for complete chords, especially complex ones
            if completeness_ratio >= 1.0:  # All expected notes present
                completeness_bonus = 0.15 + (len(all_expected) - 3) * 0.05  # More bonus for complex chords
                score += completeness_bonus
            elif completeness_ratio >= 0.8:  # Most notes present
                score += 0.08
        
        # ENHANCED: Bonus for exact matches (no extra notes)
        if not extra_notes and total_matched_notes >= 3:
            exact_match_bonus = 0.1  # Increased bonus for clean, exact matches
            score += exact_match_bonus
        
        # ENHANCED: Bonus for having the exact expected number of notes
        if len(relative_pcs) == len(all_expected) and not extra_notes:
            perfect_match_bonus = 0.05  # Additional bonus for perfect note count
            score += perfect_match_bonus
        
        # Penalty for extra notes (but not too harsh)
        if extra_notes:
            extra_penalty = min(len(extra_notes) * 0.04, 0.12)  # Reduced penalty
            score = max(0, score - extra_penalty)
        
        # Bonus for voice separation quality
        voice_bonus = self._calculate_voice_separation_bonus(voices, all_notes)
        score += voice_bonus * 0.05
        
        # Root weight bonus (prefer bass note as root)
        root_bonus = (root_weight - 0.3) * 0.35  # Much stronger bonus for bass note as root
        score += root_bonus
        
        # ENHANCED: Prefer more complex chords when they fit better
        complexity_bonus = 0.0
        if definition['complexity'] == ChordComplexity.INTERMEDIATE and total_matched_notes >= 4:
            complexity_bonus = 0.02
        elif definition['complexity'] == ChordComplexity.ADVANCED and total_matched_notes >= 5:
            complexity_bonus = 0.03
        elif definition['complexity'] == ChordComplexity.EXPERIMENTAL and total_matched_notes >= 6:
            complexity_bonus = 0.04
        score += complexity_bonus
        
        if score < 0.2:  # Very low scores are not useful
            return None
        
        # Calculate confidence based on completeness and clarity
        confidence = self._calculate_confidence(
            matched_core, missing_core, matched_important, missing_important, extra_notes
        )
        
        # Create candidate
        root_name = self._pc_to_name(root_pc)
        chord_name = f"{root_name}{chord_type}"
        
        return ChordCandidate(
            root_pc=root_pc,
            chord_type=chord_type,
            chord_name=chord_name,
            score=score,
            confidence=confidence,
            complexity=definition['complexity'],
            voice_separation=voices,
            missing_expected=list(missing_core | missing_important),
            extra_notes=list(extra_notes)
        )
    
    def _calculate_voice_separation_bonus(self, voices: Dict[str, List[int]], 
                                        all_notes: List[int]) -> float:
        """Calculate bonus for good voice separation"""
        bonus = 0.0
        
        # Bonus for clear bass note
        if len(voices['bass']) == 1:
            bonus += 0.3
        elif len(voices['bass']) == 2:
            bonus += 0.2
        
        # Bonus for reasonable chord density
        chord_span = 0
        if len(voices['chord']) > 1:
            chord_span = max(voices['chord']) - min(voices['chord'])
            if 12 <= chord_span <= 24:  # Good chord span (1-2 octaves)
                bonus += 0.2
        
        # Bonus for melody separation
        if voices['melody'] and max(voices['melody']) > max(voices['chord'] + voices['bass']):
            bonus += 0.1
        
        return min(bonus, 0.6)
    
    def _calculate_confidence(self, matched_core: Set, missing_core: Set, 
                            matched_important: Set, missing_important: Set, 
                            extra_notes: Set) -> float:
        """Calculate confidence score for the chord recognition"""
        confidence = 0.5  # Base confidence
        
        # High confidence for complete core intervals
        if not missing_core:
            confidence += 0.3
        elif len(missing_core) == 1:
            confidence += 0.1
        
        # Bonus for matched important intervals
        if matched_important:
            confidence += 0.15
        
        # Penalty for many extra notes
        if len(extra_notes) > 2:
            confidence -= 0.2
        elif len(extra_notes) == 1:
            confidence -= 0.05
        
        return max(0.0, min(1.0, confidence))
    
    def _apply_context_bonus(self, candidate: ChordCandidate) -> ChordCandidate:
        """Apply musical context bonuses based on chord history"""
        bonus = 0.0
        
        if len(self.chord_history) >= 2:
            prev_chord = self.chord_history[-1]
            
            # Common progression bonuses
            interval = (candidate.root_pc - prev_chord.root_pc) % 12
            
            # ii-V-I progression
            if interval == 7:  # Perfect fifth up (or fourth down)
                bonus += 0.1
            
            # Stepwise bass movement
            if interval in [1, 11]:  # Semitone movement
                bonus += 0.05
            
            # Circle of fifths
            if interval == 7:
                bonus += 0.08
        
        candidate.context_bonus = bonus
        return candidate
    
    def _pc_to_name(self, pc: int) -> str:
        """Convert pitch class to note name"""
        note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        return note_names[pc % 12]

    def get_analysis_summary(self, candidate: ChordCandidate) -> Dict[str, Any]:
        """Get detailed analysis summary"""
        if not candidate:
            return {}
        
        return {
            'chord_name': candidate.chord_name,
            'confidence': round(candidate.confidence, 3),
            'score': round(candidate.score, 3),
            'complexity': candidate.complexity.name,
            'voice_separation': {
                'bass': [self._pc_to_name(n % 12) for n in candidate.voice_separation['bass']],
                'chord': [self._pc_to_name(n % 12) for n in candidate.voice_separation['chord']],
                'melody': [self._pc_to_name(n % 12) for n in candidate.voice_separation['melody']]
            },
            'analysis': {
                'missing_expected': candidate.missing_expected,
                'extra_notes': candidate.extra_notes,
                'context_bonus': round(candidate.context_bonus, 3)
            }
        }
