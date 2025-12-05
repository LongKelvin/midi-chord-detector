# MIDI Chord Detector: Technical Design Document

## Document Overview

**Purpose**: Define the technical architecture, algorithms, and implementation details for jazz chord detection enhancements  
**Audience**: Developers implementing the requirements  
**References**: `01-PROBLEM-ANALYSIS.md`, `02-REQUIREMENTS.md`

---

## 1. System Architecture

### 1.1 High-Level Architecture (Enhanced)

```
┌─────────────────────────────────────────────────────────────────┐
│                         MIDI Input Layer                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  MIDIChordRecognizer (chord_recognition_engine.py)       │   │
│  │  - MIDI port management                                  │   │
│  │  - Sustain pedal handling                                │   │
│  │  - Note on/off event processing                          │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Time Window Aggregator (NEW)                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  TimeWindowBuffer                                         │   │
│  │  - Collect notes over configurable window (50-150ms)     │   │
│  │  - Apply time decay weighting                            │   │
│  │  - Filter out expired notes                              │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Voice Separator (NEW)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  VoiceSeparator                                           │   │
│  │  - Separate bass, chord tones, melody by register        │   │
│  │  - Detect lowest note as bass                            │   │
│  │  - Optionally filter melody notes                        │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Chord Recognition Engine                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ChordTheory (music_theory.py) - ENHANCED                │   │
│  │                                                            │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │  Basic Recognition (existing)                    │    │   │
│  │  │  - Pattern matching with fuzzy scoring           │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                                                            │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │  Advanced Recognition (enhanced)                 │    │   │
│  │  │  - AdvancedChordAnalyzer                         │    │   │
│  │  │  - Fuzzy matching with interval priority         │    │   │
│  │  │  - Candidate generation & ranking                │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                                                            │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │  Context Analyzer (NEW)                          │    │   │
│  │  │  - Chord history tracking                        │    │   │
│  │  │  - Progression pattern matching                  │    │   │
│  │  │  - Key detection (optional)                      │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  │                                                            │   │
│  │  ┌──────────────────────────────────────────────────┐    │   │
│  │  │  Chord Definition Manager                        │    │   │
│  │  │  - Load JSON definitions (enhanced schema)       │    │   │
│  │  │  - Merge user definitions                        │    │   │
│  │  │  - Validate definitions                          │    │   │
│  │  └──────────────────────────────────────────────────┘    │   │
│  └────────────────┬─────────────────────────────────────────┘   │
└───────────────────┼─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Output Layer                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  - ZMQ Publisher (real-time streaming)                   │   │
│  │  - UI Callback (PyQt6 - ENHANCED)                        │   │
│  │    * Multi-candidate display                             │   │
│  │    * Explanation panel                                   │   │
│  │    * Manual correction UI                                │   │
│  │    * Voice-colored piano keyboard                        │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

```
MIDI Note Events
      ↓
[Time Window Buffer] → Aggregated Note Set (with time weights)
      ↓
[Voice Separator] → {bass_notes, chord_notes, melody_notes}
      ↓
[Chord Recognition]
      ├─→ [Generate Candidates] → List[ChordCandidate]
      ├─→ [Score Each Candidate]
      │     ├─→ Interval match score
      │     ├─→ Voicing quality score
      │     └─→ Context score (from history)
      ├─→ [Rank Candidates] → Sorted List[ChordCandidate]
      └─→ [Select Best] → Primary Chord + Alternates
      ↓
[Output] → UI + ZMQ + Logging
```

---

## 2. Core Algorithms

### 2.1 Time Window Aggregation Algorithm

**Purpose**: Collect notes over time to handle rolled/arpeggiated chords

**Algorithm**:
```python
class TimeWindowBuffer:
    def __init__(self, window_ms=80, decay_ms=100):
        self.window_ms = window_ms
        self.decay_ms = decay_ms
        self.note_events = []  # List[(midi_note, timestamp, velocity)]
    
    def add_note(self, midi_note: int, timestamp: float, velocity: int):
        """Add note to buffer with timestamp"""
        self.note_events.append((midi_note, timestamp, velocity))
        self._cleanup_old_notes(timestamp)
    
    def remove_note(self, midi_note: int, timestamp: float):
        """Remove note from buffer"""
        self.note_events = [(n, t, v) for n, t, v in self.note_events 
                            if n != midi_note]
    
    def _cleanup_old_notes(self, current_time: float):
        """Remove notes older than window"""
        cutoff = current_time - (self.window_ms / 1000.0)
        self.note_events = [(n, t, v) for n, t, v in self.note_events 
                            if t >= cutoff]
    
    def get_weighted_notes(self, current_time: float) -> Dict[int, float]:
        """Return notes with time-decay weights"""
        weighted = {}
        for midi_note, timestamp, velocity in self.note_events:
            age_ms = (current_time - timestamp) * 1000
            
            # Exponential decay
            weight = math.exp(-age_ms / self.decay_ms)
            
            # Also factor in velocity
            velocity_factor = velocity / 127.0
            
            final_weight = weight * velocity_factor
            
            # Keep highest weight if note appears multiple times
            weighted[midi_note] = max(weighted.get(midi_note, 0), final_weight)
        
        return weighted
```

**Integration Point**: 
- Called in `MIDIChordRecognizer._update_chord_and_publish()`
- Replace `self.active_notes` with `self.time_buffer.get_weighted_notes(time.time())`

---

### 2.2 Voice Separation Algorithm

**Purpose**: Separate bass, chord tones, and melody by register

**Algorithm**:
```python
from dataclasses import dataclass
from typing import List, Dict

@dataclass
class VoiceRanges:
    bass_min: int = 21   # A0
    bass_max: int = 60   # C4
    chord_min: int = 36  # C2
    chord_max: int = 84  # C6
    melody_min: int = 60 # C4
    melody_max: int = 108 # C8

class VoiceSeparator:
    def __init__(self, ranges: VoiceRanges = VoiceRanges()):
        self.ranges = ranges
    
    def separate(self, midi_notes: Dict[int, float], 
                 filter_melody: bool = False) -> Dict[str, List[int]]:
        """
        Separate notes into bass, chord, melody
        
        Returns: {
            'bass': [lowest_note],
            'chord': [chord_notes],
            'melody': [melody_notes],
            'all': [all_notes_sorted]
        }
        """
        if not midi_notes:
            return {'bass': [], 'chord': [], 'melody': [], 'all': []}
        
        sorted_notes = sorted(midi_notes.keys())
        
        # Bass: lowest note in bass range
        bass_candidates = [n for n in sorted_notes 
                          if self.ranges.bass_min <= n <= self.ranges.bass_max]
        bass = [bass_candidates[0]] if bass_candidates else []
        
        # Chord: notes in chord range (excluding bass if already assigned)
        chord = [n for n in sorted_notes 
                if self.ranges.chord_min <= n <= self.ranges.chord_max
                and (not bass or n != bass[0])]
        
        # Melody: notes in melody range
        melody = [n for n in sorted_notes 
                 if n >= self.ranges.melody_min]
        
        # If filtering melody, check for large gap
        if filter_melody and len(sorted_notes) > 2:
            # If highest note is >12 semitones above next highest, it's melody
            if sorted_notes[-1] - sorted_notes[-2] > 12:
                melody_note = sorted_notes[-1]
                chord = [n for n in chord if n != melody_note]
                melody = [melody_note]
        
        return {
            'bass': bass,
            'chord': chord,
            'melody': melody,
            'all': sorted_notes
        }
    
    def get_bass_note(self, midi_notes: Dict[int, float]) -> Optional[int]:
        """Quick helper to get bass note"""
        voices = self.separate(midi_notes)
        return voices['bass'][0] if voices['bass'] else None
```

**Integration**:
- Called after time window aggregation
- Use `voices['chord']` as input to chord recognition
- Use `voices['bass'][0]` for bass note detection & slash chords

---

### 2.3 Fuzzy Chord Matching Algorithm

**Purpose**: Match chords even with omitted/extra notes

**Enhanced Scoring Function**:
```python
from typing import FrozenSet, Dict, Tuple

class FuzzyChordMatcher:
    # Interval importance weights
    WEIGHTS = {
        0: 0.8,   # Root - important but can be omitted in jazz
        1: 0.6,   # b9 - tension
        2: 0.5,   # 9 - extension
        3: 1.0,   # m3/b3 - ESSENTIAL (defines quality)
        4: 1.0,   # M3 - ESSENTIAL (defines quality)
        5: 0.4,   # 11 - extension
        6: 0.6,   # #11/b5 - tension/alteration
        7: 0.3,   # P5 - often omitted
        8: 0.7,   # #5/b13 - alteration
        9: 0.5,   # 13/6 - extension
        10: 1.0,  # m7 - ESSENTIAL for 7th chords
        11: 1.0,  # M7 - ESSENTIAL for maj7 chords
    }
    
    @classmethod
    def calculate_score(cls, 
                       played_pcs: FrozenSet[int],
                       chord_def: Dict) -> Tuple[float, Dict]:
        """
        Calculate fuzzy match score for chord definition
        
        Returns: (score, details_dict)
        """
        required = frozenset(chord_def.get('required_intervals', []))
        core = frozenset(chord_def.get('core_intervals', []))
        optional = frozenset(chord_def.get('optional_intervals', []))
        
        # Check required intervals - MUST be present
        if required and not required.issubset(played_pcs):
            return 0.0, {'reason': 'Missing required intervals'}
        
        # Calculate matched/missing/extra
        all_expected = core | optional
        matched_core = played_pcs & core
        matched_optional = played_pcs & optional
        missing = all_expected - played_pcs
        extra = played_pcs - all_expected
        
        # Weighted score calculation
        matched_score = sum(cls.WEIGHTS.get(i % 12, 0.5) for i in matched_core)
        total_core_weight = sum(cls.WEIGHTS.get(i % 12, 0.5) for i in core)
        
        if total_core_weight == 0:
            return 0.0, {'reason': 'Invalid chord definition'}
        
        # Base score: how much of core is matched
        base_score = matched_score / total_core_weight
        
        # Bonus for matched optional intervals
        if optional:
            optional_score = sum(cls.WEIGHTS.get(i % 12, 0.5) 
                               for i in matched_optional)
            optional_weight = sum(cls.WEIGHTS.get(i % 12, 0.5) 
                                for i in optional)
            base_score += (optional_score / optional_weight) * 0.2
        
        # Penalty for missing important intervals (but not required)
        important_missing = missing & core
        penalty_missing = 0
        for interval in important_missing:
            weight = cls.WEIGHTS.get(interval % 12, 0.5)
            if weight >= 0.8:  # Important intervals (root, 3rd, 7th)
                penalty_missing += 0.1
            else:
                penalty_missing += 0.05
        
        # Penalty for extra notes (but capped)
        penalty_extra = min(len(extra) * 0.05, 0.15)
        
        # Final score
        final_score = max(base_score - penalty_missing - penalty_extra, 0.0)
        
        details = {
            'matched_core': list(matched_core),
            'matched_optional': list(matched_optional),
            'missing': list(missing),
            'extra': list(extra),
            'base_score': base_score,
            'penalty_missing': penalty_missing,
            'penalty_extra': penalty_extra,
            'final_score': final_score
        }
        
        return final_score, details
```

---

### 2.4 Candidate Generation & Ranking Algorithm

**Purpose**: Generate multiple chord candidates and rank them

**Algorithm**:
```python
from dataclasses import dataclass
from typing import List, Set
import itertools

@dataclass
class ChordCandidate:
    root_pc: int              # 0-11
    root_name: str            # "C", "F#", etc.
    chord_type: str           # "maj7", "9", "7alt"
    chord_name: str           # "Cmaj7"
    full_name: str            # "Cmaj7/E" (with bass if slash chord)
    bass_note: Optional[int]  # MIDI note
    bass_name: str            # "E"
    
    # Scoring
    interval_score: float     # 0-1
    voicing_score: float      # 0-1
    context_score: float      # 0-1
    frequency_score: float    # 0-1
    bass_match_score: float   # 0-1
    total_score: float        # Weighted sum
    confidence: int           # 0-100%
    
    # Details
    matched_intervals: List[int]
    missing_intervals: List[int]
    extra_intervals: List[int]
    inversion: Optional[int]  # 0=root, 1=1st, 2=2nd, etc.
    reason: str               # Human-readable explanation

class CandidateGenerator:
    def __init__(self, chord_definitions: Dict, matcher: FuzzyChordMatcher):
        self.chord_defs = chord_definitions
        self.matcher = matcher
    
    def generate_candidates(self,
                          chord_notes: List[int],
                          bass_note: Optional[int],
                          context: 'ChordContext',
                          max_candidates: int = 5) -> List[ChordCandidate]:
        """
        Generate and rank chord candidates
        """
        if not chord_notes:
            return []
        
        # Convert to pitch classes
        notes_pcs = frozenset(n % 12 for n in chord_notes)
        
        candidates = []
        
        # Try each possible root (0-11)
        for root_pc in range(12):
            # Calculate intervals from this root
            intervals = frozenset((pc - root_pc) % 12 for pc in notes_pcs)
            
            # Try each chord type
            for chord_type, chord_def in self.chord_defs.items():
                # Score this candidate
                interval_score, details = self.matcher.calculate_score(
                    intervals, chord_def
                )
                
                # Skip if score too low
                if interval_score < 0.4:
                    continue
                
                # Calculate other score components
                voicing_score = self._score_voicing(chord_notes, chord_def)
                context_score = self._score_context(root_pc, chord_type, context)
                frequency_score = self._score_frequency(chord_type)
                bass_match_score = self._score_bass_match(
                    root_pc, bass_note, intervals, chord_def
                )
                
                # Weighted total
                total_score = (
                    interval_score * 0.40 +
                    voicing_score * 0.20 +
                    context_score * 0.20 +
                    frequency_score * 0.10 +
                    bass_match_score * 0.10
                )
                
                # Build candidate
                root_name = self._pc_to_name(root_pc)
                chord_name = f"{root_name}{chord_type}"
                
                # Check for slash chord
                full_name = chord_name
                inversion = None
                if bass_note is not None:
                    bass_pc = bass_note % 12
                    if bass_pc != root_pc:
                        bass_name = self._pc_to_name(bass_pc)
                        full_name = f"{chord_name}/{bass_name}"
                        
                        # Detect inversion
                        inversion = self._detect_inversion(
                            root_pc, bass_pc, intervals, chord_def
                        )
                
                candidate = ChordCandidate(
                    root_pc=root_pc,
                    root_name=root_name,
                    chord_type=chord_type,
                    chord_name=chord_name,
                    full_name=full_name,
                    bass_note=bass_note,
                    bass_name=self._pc_to_name(bass_note % 12) if bass_note else root_name,
                    interval_score=interval_score,
                    voicing_score=voicing_score,
                    context_score=context_score,
                    frequency_score=frequency_score,
                    bass_match_score=bass_match_score,
                    total_score=total_score,
                    confidence=int(total_score * 100),
                    matched_intervals=details['matched_core'] + details['matched_optional'],
                    missing_intervals=details['missing'],
                    extra_intervals=details['extra'],
                    inversion=inversion,
                    reason=self._generate_reason(details, total_score)
                )
                
                candidates.append(candidate)
        
        # Sort by total score (descending)
        candidates.sort(key=lambda c: c.total_score, reverse=True)
        
        # Return top N
        return candidates[:max_candidates]
    
    def _score_voicing(self, midi_notes: List[int], chord_def: Dict) -> float:
        """Score based on voicing quality (spacing, range)"""
        if len(midi_notes) < 2:
            return 0.5
        
        sorted_notes = sorted(midi_notes)
        
        # Prefer close voicings (within 1.5 octaves)
        span = sorted_notes[-1] - sorted_notes[0]
        if span <= 18:  # 1.5 octaves
            span_score = 1.0
        elif span <= 24:  # 2 octaves
            span_score = 0.8
        else:
            span_score = 0.6
        
        # Prefer typical jazz voicing ranges (C3-C5 for chords)
        mid_note = sorted_notes[len(sorted_notes) // 2]
        if 48 <= mid_note <= 72:  # C3-C5
            range_score = 1.0
        else:
            range_score = 0.7
        
        return (span_score + range_score) / 2
    
    def _score_context(self, root_pc: int, chord_type: str, 
                      context: 'ChordContext') -> float:
        """Score based on chord progression context"""
        if not context or not context.history:
            return 0.5  # Neutral if no context
        
        prev_chord = context.history[-1]
        prev_root = prev_chord.get('root_pc')
        prev_type = prev_chord.get('chord_type')
        
        if prev_root is None:
            return 0.5
        
        # Calculate root movement
        root_movement = (root_pc - prev_root) % 12
        
        # Common progressions boost
        # ii-V: perfect 5th up (7 semitones)
        if root_movement == 7 and prev_type in ['min7', 'm7']:
            if chord_type in ['7', '9', '13', '7b9', '7#9', '7alt']:
                return 1.0  # Strong ii-V
        
        # V-I: perfect 5th up (7 semitones) or half-step up (1 semitone)
        if root_movement in [7, 1]:
            if prev_type in ['7', '9', '13'] and chord_type in ['maj', 'maj7']:
                return 1.0
        
        # IV-V: whole step up (2 semitones)
        if root_movement == 2:
            return 0.8
        
        # Diatonic movement (2, 3, 5, 7 semitones)
        if root_movement in [2, 3, 5, 7]:
            return 0.7
        
        # Chromatic movement (1, 11 semitones)
        if root_movement in [1, 11]:
            return 0.6
        
        # Tritone substitution (6 semitones)
        if root_movement == 6 and 'alt' in chord_type:
            return 0.9
        
        return 0.5
    
    def _score_frequency(self, chord_type: str) -> float:
        """Boost common chord types slightly"""
        common_chords = {
            'maj': 1.0, 'min': 1.0, '7': 1.0, 'maj7': 0.9, 'min7': 0.9,
            '9': 0.8, 'sus4': 0.7, 'dim': 0.6, 'aug': 0.5
        }
        return common_chords.get(chord_type, 0.5)
    
    def _score_bass_match(self, root_pc: int, bass_note: Optional[int],
                         intervals: FrozenSet[int], chord_def: Dict) -> float:
        """Score how well bass note matches chord"""
        if bass_note is None:
            return 0.5
        
        bass_pc = bass_note % 12
        
        # Perfect if bass = root
        if bass_pc == root_pc:
            return 1.0
        
        # Good if bass = known inversion (3rd, 5th, 7th)
        bass_interval = (bass_pc - root_pc) % 12
        if bass_interval in [4, 3]:  # Major/minor 3rd
            return 0.9
        if bass_interval == 7:  # Perfect 5th
            return 0.8
        if bass_interval in [10, 11]:  # m7/M7
            return 0.8
        
        # Okay if bass is in chord
        if bass_interval in intervals:
            return 0.7
        
        # Bad if bass is not in chord
        return 0.3
    
    def _detect_inversion(self, root_pc: int, bass_pc: int,
                         intervals: FrozenSet[int], chord_def: Dict) -> Optional[int]:
        """Detect inversion number (0=root, 1=1st, 2=2nd, etc.)"""
        if bass_pc == root_pc:
            return 0  # Root position
        
        bass_interval = (bass_pc - root_pc) % 12
        
        # Standard triads/7ths
        core = chord_def.get('core_intervals', [])
        sorted_core = sorted(core)
        
        if bass_interval in sorted_core:
            return sorted_core.index(bass_interval)
        
        return None
    
    def _generate_reason(self, details: Dict, total_score: float) -> str:
        """Generate human-readable explanation"""
        reasons = []
        
        if total_score >= 0.9:
            reasons.append("Strong match")
        elif total_score >= 0.7:
            reasons.append("Good match")
        else:
            reasons.append("Possible match")
        
        if details['missing']:
            missing_names = [self._interval_name(i) for i in details['missing'][:2]]
            reasons.append(f"Missing: {', '.join(missing_names)}")
        
        if details['extra']:
            extra_names = [self._interval_name(i) for i in details['extra'][:2]]
            reasons.append(f"Extra: {', '.join(extra_names)}")
        
        return "; ".join(reasons)
    
    def _interval_name(self, interval: int) -> str:
        names = {
            0: 'R', 1: 'b9', 2: '9', 3: 'm3', 4: 'M3', 5: '11',
            6: '#11', 7: '5', 8: '#5', 9: '13', 10: 'b7', 11: 'M7'
        }
        return names.get(interval % 12, str(interval))
    
    def _pc_to_name(self, pc: int) -> str:
        names = ['C', 'C#', 'D', 'D#', 'E', 'F', 
                'F#', 'G', 'G#', 'A', 'A#', 'B']
        return names[pc % 12]
```

---

### 2.5 Context Analysis Algorithm

**Purpose**: Track chord history and detect progressions

**Algorithm**:
```python
from collections import deque
from typing import Optional, List, Dict
import time

class ChordContext:
    def __init__(self, max_history: int = 10, timeout_sec: float = 10.0):
        self.history = deque(maxlen=max_history)
        self.timeout = timeout_sec
        self.detected_key: Optional[str] = None
        self.key_confidence: float = 0.0
    
    def add_chord(self, chord_info: Dict):
        """Add detected chord to history"""
        chord_info['timestamp'] = time.time()
        self.history.append(chord_info)
        self._cleanup_old()
        self._update_key_detection()
    
    def _cleanup_old(self):
        """Remove chords older than timeout"""
        current = time.time()
        while self.history and (current - self.history[0]['timestamp']) > self.timeout:
            self.history.popleft()
    
    def _update_key_detection(self):
        """Simple key detection based on pitch class distribution"""
        if len(self.history) < 4:
            return
        
        # Count pitch class occurrences (weighted by recency)
        pc_counts = [0] * 12
        total_weight = 0
        
        for i, chord in enumerate(self.history):
            # Recent chords weighted more
            weight = 1.0 + (i / len(self.history)) * 0.5
            
            root_pc = chord.get('root_pc')
            if root_pc is not None:
                pc_counts[root_pc] += weight
                total_weight += weight
        
        if total_weight == 0:
            return
        
        # Normalize
        pc_probs = [count / total_weight for count in pc_counts]
        
        # Compare to major/minor key profiles (Krumhansl-Schmuckler)
        major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 
                        2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                        2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
        
        # Calculate correlation for each key
        best_key = None
        best_score = -1
        
        for tonic in range(12):
            # Rotate profiles
            major_rotated = major_profile[tonic:] + major_profile[:tonic]
            minor_rotated = minor_profile[tonic:] + minor_profile[:tonic]
            
            # Correlation
            major_corr = sum(a * b for a, b in zip(pc_probs, major_rotated))
            minor_corr = sum(a * b for a, b in zip(pc_probs, minor_rotated))
            
            if major_corr > best_score:
                best_score = major_corr
                best_key = f"{self._pc_name(tonic)} major"
            
            if minor_corr > best_score:
                best_score = minor_corr
                best_key = f"{self._pc_name(tonic)} minor"
        
        self.detected_key = best_key
        self.key_confidence = min(best_score / 10.0, 1.0)  # Normalize
    
    def _pc_name(self, pc: int) -> str:
        return ['C', 'C#', 'D', 'Eb', 'E', 'F', 
                'F#', 'G', 'Ab', 'A', 'Bb', 'B'][pc]
    
    def get_progression_pattern(self) -> Optional[str]:
        """Detect if current chords match known progression"""
        if len(self.history) < 2:
            return None
        
        # Get last few chord types and root movements
        recent = list(self.history)[-4:]  # Last 4 chords
        
        if len(recent) >= 3:
            # Check for ii-V-I
            if (self._is_minor_7th(recent[-3]['chord_type']) and
                self._is_dominant(recent[-2]['chord_type']) and
                self._is_major(recent[-1]['chord_type'])):
                
                # Verify root movements (up 5th, up 5th)
                root1 = recent[-3]['root_pc']
                root2 = recent[-2]['root_pc']
                root3 = recent[-1]['root_pc']
                
                if ((root2 - root1) % 12 == 7 and 
                    (root3 - root2) % 12 == 7):
                    return "ii-V-I"
        
        if len(recent) >= 2:
            # Check for V-I
            if (self._is_dominant(recent[-2]['chord_type']) and
                self._is_major(recent[-1]['chord_type'])):
                
                root1 = recent[-2]['root_pc']
                root2 = recent[-1]['root_pc']
                
                if (root2 - root1) % 12 in [7, 1]:  # Up 5th or half-step
                    return "V-I"
        
        return None
    
    def _is_minor_7th(self, chord_type: str) -> bool:
        return chord_type in ['min7', 'm7', 'min9', 'm9']
    
    def _is_dominant(self, chord_type: str) -> bool:
        return chord_type in ['7', '9', '11', '13', '7b9', '7#9', '7alt']
    
    def _is_major(self, chord_type: str) -> bool:
        return chord_type in ['maj', 'maj7', 'maj9', '6']
```

---

## 3. Data Structures

### 3.1 Enhanced Chord Definition Schema

**File**: `chord_definitions_v2.json`

```json
{
  "chord_type_id": {
    "name": "Human-readable name",
    "symbol": "Short symbol (e.g., '7b9')",
    
    "required_intervals": [3, 10],
    "core_intervals": [0, 4, 7, 10],
    "optional_intervals": [7],
    "alterations": [1],
    
    "interval_weights": {
      "0": 0.7,
      "3": 1.0,
      "7": 0.5,
      "10": 1.0,
      "1": 0.9
    },
    
    "typical_voicings": [
      {"notes": [0, 4, 10, 1], "name": "root position"},
      {"notes": [4, 10, 1, 12], "name": "rootless"}
    ],
    
    "complexity": "basic|intermediate|advanced",
    "genre_tags": ["jazz", "blues", "classical"],
    "function": "tonic|subdominant|dominant|diminished",
    "resolution_tendency": ["maj", "min"]
  }
}
```

### 3.2 Internal Data Structures

```python
@dataclass
class NoteEvent:
    midi_note: int
    timestamp: float
    velocity: int
    is_on: bool  # True for note-on, False for note-off

@dataclass
class VoiceSeparation:
    bass: List[int]
    chord: List[int]
    melody: List[int]
    all_notes: List[int]

@dataclass
class ChordDetectionResult:
    primary_candidate: ChordCandidate
    alternate_candidates: List[ChordCandidate]
    voice_separation: VoiceSeparation
    context_info: Dict[str, Any]
    timestamp: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp,
            'full_chord_name': self.primary_candidate.full_name,
            'root_note_name': self.primary_candidate.root_name,
            'bass_note_name': self.primary_candidate.bass_name,
            'chord_type': self.primary_candidate.chord_type,
            'inversion': self.primary_candidate.inversion,
            'confidence': self.primary_candidate.confidence,
            'score': self.primary_candidate.total_score,
            'played_notes_midi': self.voice_separation.all_notes,
            'chord_notes_midi': self.voice_separation.chord,
            'bass_note_midi': self.voice_separation.bass[0] if self.voice_separation.bass else None,
            'melody_notes_midi': self.voice_separation.melody,
            'alternates': [
                {
                    'name': c.full_name,
                    'confidence': c.confidence,
                    'reason': c.reason
                }
                for c in self.alternate_candidates
            ],
            'context': self.context_info
        }
```

---

## 4. Implementation Plan

### Phase 1: Fuzzy Matching & Time Window (Month 1)

**Week 1: Time Window Buffer**
- [ ] Implement `TimeWindowBuffer` class
- [ ] Integrate into `MIDIChordRecognizer`
- [ ] Add configuration options (window_ms, decay_ms)
- [ ] Unit tests for time aggregation

**Week 2: Fuzzy Matching**
- [ ] Implement `FuzzyChordMatcher` with interval weights
- [ ] Update chord definitions with `required_intervals`
- [ ] Scoring algorithm with omitted/extra note handling
- [ ] Unit tests for fuzzy scoring

**Week 3: Enhanced Chord Definitions**
- [ ] Extend `chord_definitions.json` with jazz chords
- [ ] Add altered dominants (7b9, 7#9, 7alt, etc.)
- [ ] Add extended chords (9, 11, 13 variants)
- [ ] Validate all definitions

**Week 4: Integration & Testing**
- [ ] Integrate fuzzy matcher into `ChordTheory.recognize_chord()`
- [ ] Comprehensive unit tests (200+ test cases)
- [ ] Performance benchmarks
- [ ] Bug fixes and optimization

### Phase 2: Voice Separation & Candidate Ranking (Months 2-3)

**Week 5-6: Voice Separation**
- [ ] Implement `VoiceSeparator` class
- [ ] Register-based bass/chord/melody separation
- [ ] Slash chord detection (bass ≠ root)
- [ ] Configurable voice ranges
- [ ] Unit tests for voice separation

**Week 7-8: Candidate Generation**
- [ ] Implement `CandidateGenerator` class
- [ ] Multi-root candidate generation
- [ ] Scoring: interval + voicing + context + frequency + bass
- [ ] Ranking algorithm
- [ ] Unit tests for candidate generation

**Week 9-10: UI Enhancements**
- [ ] Multi-candidate display in PyQt UI
- [ ] Explanation panel (matched/missing/extra intervals)
- [ ] Voice-colored piano keyboard
- [ ] Allow manual candidate selection
- [ ] UI for configuration (time window, voice ranges)

**Week 11-12: Testing & Refinement**
- [ ] Integration tests with MIDI files
- [ ] Accuracy measurements
- [ ] Performance optimization
- [ ] User testing and feedback

### Phase 3: Context Awareness (Months 3-4)

**Week 13-14: Context Tracking**
- [ ] Implement `ChordContext` class
- [ ] Chord history buffer
- [ ] Key detection algorithm (Krumhansl-Schmuckler)
- [ ] Unit tests for context

**Week 15-16: Progression Recognition**
- [ ] Progression pattern matching (ii-V-I, V-I, etc.)
- [ ] Context-based scoring adjustments
- [ ] Tritone substitution detection
- [ ] Integration into candidate scoring

**Week 17-18: User Features**
- [ ] Manual correction UI
- [ ] Save/load corrections to `corrections.json`
- [ ] User-defined chord definitions editor
- [ ] Import/export custom definitions

**Week 19-20: Final Testing & Release**
- [ ] Comprehensive test suite with jazz MIDI files
- [ ] Performance benchmarks
- [ ] Documentation (API, user guide)
- [ ] Release v2.0

---

## 5. Testing Strategy

### 5.1 Unit Tests

```python
# test_time_window.py
def test_time_window_aggregation():
    buffer = TimeWindowBuffer(window_ms=100)
    
    # Add notes over time
    buffer.add_note(60, 0.000, 100)  # C4
    buffer.add_note(64, 0.030, 100)  # E4
    buffer.add_note(67, 0.060, 100)  # G4
    
    # Get weighted notes
    weighted = buffer.get_weighted_notes(0.080)
    
    assert 60 in weighted
    assert weighted[60] > weighted[64]  # Older note has less weight
    assert weighted[64] > weighted[67]

# test_fuzzy_matching.py
def test_omitted_fifth():
    matcher = FuzzyChordMatcher()
    played = frozenset([0, 4])  # C, E (no G)
    chord_def = {
        'required_intervals': [],
        'core_intervals': [0, 4, 7],
        'optional_intervals': [7]
    }
    
    score, details = matcher.calculate_score(played, chord_def)
    
    assert score > 0.7  # Should still recognize as major
    assert 7 in details['missing']  # 5th is missing

# test_candidate_ranking.py
def test_candidate_generation():
    generator = CandidateGenerator(chord_definitions, matcher)
    
    # C major 7th: C, E, G, B
    candidates = generator.generate_candidates(
        chord_notes=[60, 64, 67, 71],
        bass_note=60,
        context=ChordContext()
    )
    
    assert len(candidates) > 0
    assert candidates[0].chord_name == "Cmaj7"
    assert candidates[0].confidence > 80
```

### 5.2 Integration Tests (MIDI Files)

```python
# test_jazz_midi.py
def test_autumn_leaves_progression():
    """Test against Autumn Leaves MIDI file"""
    midi_file = "test_data/autumn_leaves.mid"
    expected_chords = [
        (0.0, "Cm7"),
        (2.0, "F7"),
        (4.0, "Bbmaj7"),
        (6.0, "Ebmaj7"),
        # ... etc
    ]
    
    recognizer = MIDIChordRecognizer(use_advanced=True)
    detected = recognizer.analyze_midi_file(midi_file)
    
    accuracy = calculate_accuracy(detected, expected_chords)
    assert accuracy > 0.75  # 75% accuracy threshold
```

### 5.3 Performance Benchmarks

```python
# benchmark_performance.py
def benchmark_detection_latency():
    """Ensure <10ms detection latency"""
    recognizer = MIDIChordRecognizer()
    
    # Simulate rapid note events
    notes = [60, 64, 67, 71]  # Cmaj7
    
    times = []
    for _ in range(1000):
        start = time.perf_counter()
        recognizer.chord_theory.recognize_chord(set(notes), 3)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # ms
    
    avg_latency = statistics.mean(times)
    p95_latency = statistics.quantiles(times, n=20)[18]  # 95th percentile
    
    assert avg_latency < 5.0  # <5ms average
    assert p95_latency < 10.0  # <10ms p95
```

---

## 6. Configuration

### 6.1 Configuration File Schema

**File**: `config.yaml`

```yaml
midi:
  port_name: null  # Auto-detect if null
  zmq_port: 5557
  
detection:
  min_notes_for_chord: 2
  use_advanced_analyzer: true
  
  time_window:
    enabled: true
    window_ms: 80
    decay_ms: 100
  
  voice_separation:
    enabled: true
    filter_melody: false
    bass_range: [21, 60]
    chord_range: [36, 84]
    melody_range: [60, 108]
  
  fuzzy_matching:
    min_score_threshold: 0.4
    max_penalty_extra_notes: 0.15
  
  candidate_ranking:
    max_candidates: 5
    score_weights:
      interval_match: 0.40
      voicing_quality: 0.20
      context: 0.20
      frequency: 0.10
      bass_match: 0.10
  
  context:
    enabled: true
    max_history: 10
    timeout_sec: 10.0
    detect_key: true
    progression_aware: true

ui:
  show_alternates: true
  show_explanation: true
  voice_colored_keyboard: true
  allow_manual_correction: true

logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  file: logs/chord_detector.log

chord_definitions:
  default_path: data/chord_definitions.json
  user_path: data/user_chord_definitions.json
  corrections_path: data/corrections.json
```

---

## 7. API Reference

### 7.1 Public API (for external integrations)

```python
class MIDIChordRecognizer:
    def __init__(self, config: Dict = None):
        """Initialize with optional config dict (overrides config.yaml)"""
        pass
    
    def start(self) -> bool:
        """Start MIDI listening and detection"""
        pass
    
    def stop(self):
        """Stop detection"""
        pass
    
    def get_current_chord(self) -> ChordDetectionResult:
        """Get current detected chord"""
        pass
    
    def register_callback(self, callback: Callable[[ChordDetectionResult], None]):
        """Register callback for chord changes"""
        pass
    
    def analyze_midi_file(self, filepath: str) -> List[ChordDetectionResult]:
        """Analyze MIDI file offline (batch processing)"""
        pass
```

### 7.2 Example Usage

```python
from core.chord_recognition_engine import MIDIChordRecognizer

def on_chord_detected(result: ChordDetectionResult):
    print(f"Detected: {result.primary_candidate.full_name} "
          f"({result.primary_candidate.confidence}%)")
    
    if len(result.alternate_candidates) > 0:
        print(f"  Alternates: {[c.full_name for c in result.alternate_candidates]}")

# Initialize
recognizer = MIDIChordRecognizer(config={
    'detection': {
        'time_window': {'window_ms': 100},
        'context': {'enabled': True}
    }
})

# Register callback
recognizer.register_callback(on_chord_detected)

# Start
if recognizer.start():
    print("Listening for MIDI input...")
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        recognizer.stop()
```

---

## 8. Performance Considerations

### 8.1 Optimization Strategies

**1. Candidate Generation Optimization**
- Cache chord definition lookups
- Pre-compute interval sets for each chord type
- Limit candidate search space (skip unlikely roots)

**2. Time Window Optimization**
- Use efficient data structures (sorted list for time-ordered events)
- Batch cleanup of old notes (not on every add)

**3. Context Analysis Optimization**
- Lazy key detection (only when needed)
- Cache progression patterns

**4. UI Optimization**
- Debounce UI updates (max 30 FPS)
- Batch ZMQ publishes
- Async UI rendering

### 8.2 Memory Management

**Limits**:
- Time window buffer: max 100 notes
- Chord history: max 10 chords
- Candidate list: max 5 candidates per detection

**Cleanup**:
- Expire old events from time buffer
- Prune chord history beyond timeout
- Limit log file size (rotate at 10MB)

---

## 9. Future Enhancements (Post-Phase 3)

### 9.1 Machine Learning Integration

**Approach**: Train a classifier on labeled jazz MIDI data
- **Features**: pitch classes, intervals, voicing spread, time distribution
- **Labels**: Chord names (annotated by human)
- **Model**: Random Forest or simple Neural Network
- **Integration**: Use ML model as additional "candidate generator" alongside rule-based

### 9.2 Music21 Integration

**Rationale**: Leverage music21's chord naming as fallback

```python
from music21 import chord

def music21_fallback(midi_notes: List[int]) -> str:
    """Use music21 for chord naming when own detector unsure"""
    note_names = [f"{pitch_name}{octave}" 
                  for midi_note in midi_notes
                  for pitch_name, octave in [(midi_to_name(midi_note % 12), 
                                             midi_note // 12)]]
    
    c = chord.Chord(note_names)
    return c.commonName  # e.g., "major seventh chord"
```

### 9.3 Real-time Performance Visualization

- **Harmonic rhythm tracker**: Show when chords change
- **Voicing analyzer**: Visualize note spacing
- **Progression graph**: Show chord progression over time

---

**Document Version**: 1.0  
**Last Updated**: December 5, 2025  
**Next Document**: `04-TASK-BREAKDOWN.md`
