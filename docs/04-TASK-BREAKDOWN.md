# MIDI Chord Detector: Task Breakdown & Implementation Guide

## Document Overview

**Purpose**: Detailed, actionable tasks for implementing jazz chord detection enhancements  
**Format**: GitHub Issues / Jira-style task cards  
**Timeline**: 16-20 weeks (4-5 months)  
**Team Size**: 1-2 developers

---

## Task Organization

### Legend
- 🔴 **Critical Path**: Blocks other tasks
- 🟡 **High Priority**: Important for core functionality
- 🟢 **Medium Priority**: Enhances functionality
- 🔵 **Low Priority**: Nice-to-have
- ⚡ **Quick Win**: <4 hours
- 🏗️ **Foundation**: Infrastructure/setup
- 🧪 **Testing**: Test implementation
- 📚 **Documentation**: Docs/comments
- 🎨 **UI/UX**: User interface

---

## Phase 1: Fuzzy Matching & Time Window (Weeks 1-4)

### Sprint 1.1: Time Window Buffer (Week 1)

#### Task 1.1.1: Create TimeWindowBuffer Class
- **ID**: MIDI-101
- **Priority**: 🔴 Critical Path
- **Effort**: 6 hours
- **Type**: 🏗️ Foundation

**Description**: Implement time-window buffer for note aggregation

**Acceptance Criteria**:
- [ ] `TimeWindowBuffer` class in new file `core/time_window_buffer.py`
- [ ] Methods: `add_note()`, `remove_note()`, `get_weighted_notes()`, `_cleanup_old_notes()`
- [ ] Configurable `window_ms` and `decay_ms` parameters
- [ ] Exponential time decay weighting formula: `weight = e^(-t / decay)`
- [ ] Velocity factor in weighting: `final_weight = time_weight * (velocity / 127)`
- [ ] Thread-safe (use locks if needed)

**Implementation Notes**:
```python
# core/time_window_buffer.py
class TimeWindowBuffer:
    def __init__(self, window_ms=80, decay_ms=100):
        self.window_ms = window_ms
        self.decay_ms = decay_ms
        self.note_events = []  # List[(midi_note, timestamp, velocity)]
        self.lock = threading.Lock()
```

**Testing**:
- Unit test: add notes at different times, verify weights
- Unit test: old notes removed after window expires
- Unit test: multiple notes at same pitch (keep max weight)

---

#### Task 1.1.2: Integrate TimeWindowBuffer into MIDIChordRecognizer
- **ID**: MIDI-102
- **Priority**: 🔴 Critical Path
- **Effort**: 4 hours
- **Depends On**: MIDI-101

**Description**: Replace `active_notes` Set with TimeWindowBuffer in recognizer

**Acceptance Criteria**:
- [ ] Import and instantiate `TimeWindowBuffer` in `__init__`
- [ ] Replace `self.active_notes.add()` with `buffer.add_note()`
- [ ] Replace `self.active_notes.discard()` with `buffer.remove_note()`
- [ ] In `_update_chord_and_publish()`, call `buffer.get_weighted_notes(time.time())`
- [ ] Pass weighted notes dict to `chord_theory.recognize_chord()`
- [ ] Backward compatibility: handle both Set[int] and Dict[int, float]

**Testing**:
- Integration test: play rolled chord (C-E-G with 40ms gaps), verify detected
- Manual test: play fast arpeggios, ensure aggregation works

---

#### Task 1.1.3: Add Time Window Configuration
- **ID**: MIDI-103
- **Priority**: 🟡 High
- **Effort**: 2 hours
- **Type**: ⚡ Quick Win

**Description**: Add config options for time window parameters

**Acceptance Criteria**:
- [ ] Add `time_window_ms` and `time_decay_ms` to `MIDIChordRecognizer.__init__`
- [ ] Pass from config.yaml or CLI args
- [ ] Document in README.md with examples
- [ ] Sensible defaults: window=80ms, decay=100ms

**Testing**:
- Test with different window sizes (50ms, 100ms, 150ms)
- Verify configuration is applied correctly

---

#### Task 1.1.4: Unit Tests for Time Window
- **ID**: MIDI-104
- **Priority**: 🟡 High
- **Effort**: 4 hours
- **Type**: 🧪 Testing

**Description**: Comprehensive unit tests for TimeWindowBuffer

**Tests to Implement**:
```python
# tests/test_time_window_buffer.py

def test_add_note():
    """Test adding notes to buffer"""

def test_remove_note():
    """Test removing notes from buffer"""

def test_time_decay_weights():
    """Test exponential decay over time"""

def test_velocity_weighting():
    """Test velocity affects weight"""

def test_cleanup_old_notes():
    """Test old notes are removed"""

def test_multiple_same_pitch():
    """Test same pitch multiple times keeps max weight"""

def test_empty_buffer():
    """Test get_weighted_notes on empty buffer"""

def test_thread_safety():
    """Test concurrent adds/removes (if using threading)"""
```

**Acceptance Criteria**:
- [ ] 8+ unit tests
- [ ] >90% code coverage for TimeWindowBuffer
- [ ] All tests pass

---

### Sprint 1.2: Fuzzy Matching (Week 2)

#### Task 1.2.1: Create FuzzyChordMatcher Class
- **ID**: MIDI-105
- **Priority**: 🔴 Critical Path
- **Effort**: 8 hours
- **Type**: 🏗️ Foundation

**Description**: Implement fuzzy matching algorithm with interval weights

**Acceptance Criteria**:
- [ ] `FuzzyChordMatcher` class in `core/fuzzy_chord_matcher.py`
- [ ] Class variable `WEIGHTS` dict with interval importance (0-11)
- [ ] Method `calculate_score(played_pcs, chord_def)` returns `(score, details)`
- [ ] Score components:
  - Check required intervals (must be present)
  - Weighted core interval matching
  - Bonus for optional intervals
  - Penalty for missing important intervals (capped)
  - Penalty for extra notes (capped at 0.15)
- [ ] Details dict includes: matched_core, matched_optional, missing, extra, penalties

**Implementation**:
```python
# core/fuzzy_chord_matcher.py
class FuzzyChordMatcher:
    WEIGHTS = {
        0: 0.8,   # Root
        3: 1.0,   # m3 - ESSENTIAL
        4: 1.0,   # M3 - ESSENTIAL
        7: 0.5,   # P5 - optional
        10: 1.0,  # b7 - ESSENTIAL for 7ths
        11: 1.0,  # M7 - ESSENTIAL for maj7s
        # ... etc
    }
    
    @classmethod
    def calculate_score(cls, played_pcs, chord_def):
        # Implementation from technical design
```

**Testing**:
- Unit test: perfect match (all intervals) = 1.0 score
- Unit test: missing 5th = score ~0.85-0.90
- Unit test: missing root = score ~0.70-0.80
- Unit test: extra note = small penalty
- Unit test: missing required interval = score 0.0

---

#### Task 1.2.2: Update ChordTheory to Use Fuzzy Matcher
- **ID**: MIDI-106
- **Priority**: 🔴 Critical Path
- **Effort**: 4 hours
- **Depends On**: MIDI-105

**Description**: Integrate FuzzyChordMatcher into ChordTheory.recognize_chord()

**Acceptance Criteria**:
- [ ] Import FuzzyChordMatcher in music_theory.py
- [ ] Replace existing scoring logic with `FuzzyChordMatcher.calculate_score()`
- [ ] Use returned details for logging/debugging
- [ ] Maintain backward compatibility with existing tests

**Testing**:
- Integration test: verify existing test cases still pass
- Regression test: simple chords still detected at high confidence

---

#### Task 1.2.3: Update Chord Definitions with Required Intervals
- **ID**: MIDI-107
- **Priority**: 🟡 High
- **Effort**: 3 hours
- **Depends On**: MIDI-105

**Description**: Add `required_intervals` field to chord definitions

**Acceptance Criteria**:
- [ ] Update `chord_definitions.json` schema
- [ ] Add `required_intervals` for each chord type:
  - Triads: `[3]` or `[4]` (need 3rd to define quality)
  - 7th chords: `[3, 10]` or `[4, 10]` (need 3rd + 7th)
  - Extended: `[10]` + extension (e.g., 9th chord needs 7th + 9)
- [ ] Update loader in `ChordTheory.load_chord_definitions()`
- [ ] Default `required_intervals = []` for backward compat

**Example**:
```json
{
  "maj7": {
    "name": "Major 7th",
    "required_intervals": [4, 11],
    "core_intervals": [0, 4, 7, 11],
    "optional_intervals": []
  },
  "7": {
    "name": "Dominant 7th",
    "required_intervals": [4, 10],
    "core_intervals": [0, 4, 7, 10],
    "optional_intervals": [7]
  }
}
```

---

#### Task 1.2.4: Unit Tests for Fuzzy Matching
- **ID**: MIDI-108
- **Priority**: 🟡 High
- **Effort**: 6 hours
- **Type**: 🧪 Testing

**Description**: Comprehensive tests for fuzzy matching

**Tests**:
```python
# tests/test_fuzzy_matching.py

def test_perfect_match():
    """Full chord with all intervals"""

def test_omitted_fifth():
    """Chord with no 5th should still match"""

def test_omitted_root():
    """Rootless voicing (jazz)"""

def test_extra_9th():
    """Major chord + 9th"""

def test_missing_required_intervals():
    """No 3rd or 7th = no match"""

def test_score_range():
    """Scores always 0.0-1.0"""

def test_penalty_capping():
    """Many extra notes = max penalty 0.15"""

def test_real_jazz_voicing():
    """Test actual jazz piano voicing (e.g., [4, 10, 14, 17] = C9 omit root)"""
```

**Acceptance Criteria**:
- [ ] 10+ unit tests
- [ ] >90% code coverage
- [ ] All tests pass

---

### Sprint 1.3: Enhanced Chord Definitions (Week 3)

#### Task 1.3.1: Add Jazz Chord Types to Definitions
- **ID**: MIDI-109
- **Priority**: 🔴 Critical Path
- **Effort**: 6 hours
- **Type**: 📚 Documentation

**Description**: Expand chord_definitions.json with comprehensive jazz chords

**Chord Types to Add**:
- **Altered Dominants**: 7alt, 7b5b9, 7b5#9, 7#5b9, 7#5#9, 7#9#11, 7b9#11, 7b9b13
- **Extended Dominants**: 9#11, 9b13, 13#11, 13b9, 13#9
- **Minor Extensions**: m9, m11, m13, m6/9, mMaj9
- **Special**: dim7, hdim7 (m7b5), aug7, 5 (power chord)

**Acceptance Criteria**:
- [ ] Add 20+ new chord types
- [ ] Each has: name, required, core, optional intervals
- [ ] Validate JSON schema
- [ ] Test each chord type manually (play it, verify detection)

**Example**:
```json
{
  "7b9": {
    "name": "Dominant 7th Flat 9",
    "required_intervals": [4, 10],
    "core_intervals": [0, 4, 7, 10],
    "optional_intervals": [7],
    "alterations": [1]
  }
}
```

---

#### Task 1.3.2: Create Chord Definition Validator
- **ID**: MIDI-110
- **Priority**: 🟡 High
- **Effort**: 3 hours
- **Type**: ⚡ Quick Win

**Description**: Validate chord definitions on load

**Acceptance Criteria**:
- [ ] Function `validate_chord_definition(chord_type, definition)` in music_theory.py
- [ ] Checks:
  - Required/core/optional are lists of ints (0-11)
  - No duplicate intervals
  - Required ⊆ core
  - Name is non-empty string
- [ ] Warn (don't crash) on invalid definitions
- [ ] Log validation errors with line numbers

**Testing**:
- Test with invalid JSON (missing fields, wrong types)
- Test with valid definitions (no warnings)

---

#### Task 1.3.3: Document Chord Definitions Format
- **ID**: MIDI-111
- **Priority**: 🟢 Medium
- **Effort**: 2 hours
- **Type**: 📚 Documentation

**Description**: Document chord definition schema for users

**Acceptance Criteria**:
- [ ] Create `docs/CHORD-DEFINITIONS.md`
- [ ] Explain schema fields (required, core, optional, alterations)
- [ ] Provide examples for each chord family
- [ ] Explain how to add custom chords
- [ ] Link from README.md

---

#### Task 1.3.4: Unit Tests for Enhanced Definitions
- **ID**: MIDI-112
- **Priority**: 🟡 High
- **Effort**: 8 hours
- **Type**: 🧪 Testing

**Description**: Test each new chord type

**Acceptance Criteria**:
- [ ] Test case for each of 20+ new chord types
- [ ] Test perfect voicing (all intervals)
- [ ] Test with omitted 5th
- [ ] Test with omitted root (if applicable)
- [ ] Verify correct chord name returned

**Example**:
```python
def test_dominant_7b9():
    """Test G7b9 = [G, B, D, F, Ab]"""
    notes = {55, 59, 62, 65, 68}  # G, B, D, F, Ab
    result = chord_theory.recognize_chord(notes, min_notes=3)
    assert result['chord_type'] == '7b9'
    assert result['root_note_name'] == 'G'
```

---

### Sprint 1.4: Integration & Polish (Week 4)

#### Task 1.4.1: Integration Testing with MIDI Files
- **ID**: MIDI-113
- **Priority**: 🔴 Critical Path
- **Effort**: 6 hours
- **Type**: 🧪 Testing

**Description**: Test against real MIDI files with known chords

**Acceptance Criteria**:
- [ ] Create `tests/test_data/` directory
- [ ] Add 3-5 MIDI files with chord annotations
  - Simple pop progression (I-V-vi-IV)
  - Jazz standard (e.g., Autumn Leaves)
  - Blues progression
- [ ] Implement `MIDIChordRecognizer.analyze_midi_file(path)`
- [ ] Compare detected chords to annotations
- [ ] Calculate accuracy (% correct)
- [ ] Log confusion matrix (what was detected vs. expected)

**Testing**:
- Target: >85% accuracy on pop, >70% on jazz

---

#### Task 1.4.2: Performance Benchmarking
- **ID**: MIDI-114
- **Priority**: 🟡 High
- **Effort**: 4 hours
- **Type**: 🧪 Testing

**Description**: Ensure real-time performance

**Acceptance Criteria**:
- [ ] Benchmark script: `tests/benchmark_performance.py`
- [ ] Measure detection latency (1000 runs)
- [ ] Measure CPU usage
- [ ] Measure memory usage
- [ ] Targets:
  - Average latency: <5ms
  - 95th percentile: <10ms
  - CPU: <10% single core
  - Memory: <50MB

**Testing**:
- Profile with cProfile, identify bottlenecks
- Optimize hot paths if needed

---

#### Task 1.4.3: Update Documentation
- **ID**: MIDI-115
- **Priority**: 🟢 Medium
- **Effort**: 3 hours
- **Type**: 📚 Documentation

**Description**: Update README and docs for Phase 1 features

**Acceptance Criteria**:
- [ ] Update README.md with new features
- [ ] Add "Fuzzy Matching" section
- [ ] Add "Time Window" section
- [ ] Update configuration examples
- [ ] Add troubleshooting section

---

#### Task 1.4.4: Bug Fixes & Refinement
- **ID**: MIDI-116
- **Priority**: 🟡 High
- **Effort**: 8 hours

**Description**: Address bugs found during testing

**Acceptance Criteria**:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] No regressions in simple chord detection
- [ ] Code review completed
- [ ] Git branch merged to main

---

## Phase 2: Voice Separation & Candidate Ranking (Weeks 5-12)

### Sprint 2.1: Voice Separation (Weeks 5-6)

#### Task 2.1.1: Create VoiceSeparator Class
- **ID**: MIDI-201
- **Priority**: 🔴 Critical Path
- **Effort**: 6 hours
- **Type**: 🏗️ Foundation

**Description**: Implement voice separation by register

**Acceptance Criteria**:
- [ ] `VoiceSeparator` class in `core/voice_separator.py`
- [ ] `VoiceRanges` dataclass for configurable ranges
- [ ] Method `separate(midi_notes, filter_melody)` returns dict
- [ ] Bass: lowest note in bass range (21-60)
- [ ] Chord: notes in chord range (36-84), excluding bass
- [ ] Melody: notes in melody range (60-108), or highest if large gap
- [ ] Optional melody filtering (toggle)

**Implementation**:
```python
# core/voice_separator.py
@dataclass
class VoiceRanges:
    bass_min: int = 21
    bass_max: int = 60
    chord_min: int = 36
    chord_max: int = 84
    melody_min: int = 60
    melody_max: int = 108

class VoiceSeparator:
    def separate(self, midi_notes, filter_melody=False):
        # Implementation from technical design
        return {'bass': [], 'chord': [], 'melody': [], 'all': []}
```

**Testing**:
- Test: bass + chord → bass=[lowest], chord=[rest]
- Test: wide voicing with melody → melody filtered out
- Test: close voicing → no melody filtering

---

#### Task 2.1.2: Integrate Voice Separation into Recognition
- **ID**: MIDI-202
- **Priority**: 🔴 Critical Path
- **Effort**: 4 hours
- **Depends On**: MIDI-201

**Description**: Use separated voices in chord recognition

**Acceptance Criteria**:
- [ ] Instantiate `VoiceSeparator` in `ChordTheory.__init__`
- [ ] In `recognize_chord()`, call `separator.separate(notes)`
- [ ] Use `voices['chord']` for chord detection
- [ ] Use `voices['bass'][0]` for bass note
- [ ] Pass voice separation to output dict

**Testing**:
- Test: slash chord (bass ≠ root)
- Test: melody note excluded from chord

---

#### Task 2.1.3: Slash Chord Detection
- **ID**: MIDI-203
- **Priority**: 🟡 High
- **Effort**: 4 hours
- **Depends On**: MIDI-202

**Description**: Detect and format slash chords (e.g., C/E)

**Acceptance Criteria**:
- [ ] If bass note ≠ chord root, format as "ChordName/BassName"
- [ ] Detect standard inversions:
  - 1st inversion: bass = 3rd
  - 2nd inversion: bass = 5th
  - 3rd inversion: bass = 7th (for 7th chords)
- [ ] Add `inversion` field to output: 0=root, 1=1st, 2=2nd, 3=3rd
- [ ] Score bonus for matching inversions (+0.1)

**Testing**:
- Test: Cmaj with bass=E → "Cmaj/E" (1st inversion)
- Test: Cmaj with bass=G → "Cmaj/G" (2nd inversion)
- Test: Cmaj7 with bass=B → "Cmaj7/B" (3rd inversion)

---

#### Task 2.1.4: Configurable Voice Ranges
- **ID**: MIDI-204
- **Priority**: 🟢 Medium
- **Effort**: 2 hours
- **Type**: ⚡ Quick Win

**Description**: Allow configuration of voice ranges

**Acceptance Criteria**:
- [ ] Add voice ranges to config.yaml
- [ ] Different presets: piano, guitar, bass
- [ ] UI to adjust ranges (Phase 3)

---

#### Task 2.1.5: Unit Tests for Voice Separation
- **ID**: MIDI-205
- **Priority**: 🟡 High
- **Effort**: 4 hours
- **Type**: 🧪 Testing

**Tests**:
```python
def test_bass_chord_separation():
    """Test basic bass + chord separation"""

def test_melody_filtering():
    """Test melody note excluded from chord"""

def test_slash_chord_detection():
    """Test slash chord formatting"""

def test_inversion_detection():
    """Test inversion numbers (0, 1, 2, 3)"""

def test_empty_voices():
    """Test with no notes"""

def test_single_note():
    """Test with single note (bass only)"""
```

---

### Sprint 2.2: Candidate Generation (Weeks 7-8)

#### Task 2.2.1: Create CandidateGenerator Class
- **ID**: MIDI-206
- **Priority**: 🔴 Critical Path
- **Effort**: 10 hours
- **Type**: 🏗️ Foundation

**Description**: Implement multi-candidate generation and ranking

**Acceptance Criteria**:
- [ ] `CandidateGenerator` class in `core/candidate_generator.py`
- [ ] `ChordCandidate` dataclass with all fields
- [ ] Method `generate_candidates()` tries all 12 roots × all chord types
- [ ] Score components:
  - `interval_score` (fuzzy matching)
  - `voicing_score` (spacing, range quality)
  - `context_score` (progression awareness)
  - `frequency_score` (common chord boost)
  - `bass_match_score` (bass alignment)
- [ ] Weighted total score
- [ ] Return top N candidates (default 5)

**Implementation**: See technical design document

**Testing**:
- Test: Cmaj7 → top candidate is "Cmaj7"
- Test: Ambiguous notes → multiple candidates with close scores
- Test: Rare chord → low frequency score

---

#### Task 2.2.2: Implement Scoring Components
- **ID**: MIDI-207
- **Priority**: 🔴 Critical Path
- **Effort**: 8 hours
- **Depends On**: MIDI-206

**Description**: Implement each scoring method

**Methods to Implement**:
- `_score_voicing(midi_notes, chord_def)`: Spacing & range quality
- `_score_context(root, type, context)`: Progression patterns (placeholder, Phase 3)
- `_score_frequency(chord_type)`: Common chord boost
- `_score_bass_match(root, bass, intervals, def)`: Bass alignment
- `_detect_inversion(root, bass, intervals, def)`: Inversion number
- `_generate_reason(details, score)`: Human-readable explanation

**Testing**:
- Test each scoring method independently
- Verify score ranges (0.0-1.0)

---

#### Task 2.2.3: Integrate Candidate Generation
- **ID**: MIDI-208
- **Priority**: 🔴 Critical Path
- **Effort**: 4 hours
- **Depends On**: MIDI-207

**Description**: Use CandidateGenerator in ChordTheory

**Acceptance Criteria**:
- [ ] Instantiate `CandidateGenerator` in `ChordTheory.__init__`
- [ ] In `recognize_chord_advanced()`, call `generator.generate_candidates()`
- [ ] Return top candidate as primary
- [ ] Include alternate candidates (2-4) in output
- [ ] Format output with new fields: confidence, alternates, reason

**Testing**:
- Integration test: verify multiple candidates returned
- Test: top candidate has highest score

---

#### Task 2.2.4: Unit Tests for Candidate Generation
- **ID**: MIDI-209
- **Priority**: 🟡 High
- **Effort**: 6 hours
- **Type**: 🧪 Testing

**Tests**:
```python
def test_generate_candidates_cmaj7():
    """Test Cmaj7 generates correct top candidate"""

def test_multiple_candidates():
    """Test returns 3-5 candidates"""

def test_candidate_ranking():
    """Test candidates sorted by score"""

def test_ambiguous_notes():
    """Test ambiguous voicing has close candidate scores"""

def test_voicing_score():
    """Test voicing score calculation"""

def test_frequency_score():
    """Test common chords boosted"""

def test_bass_match_score():
    """Test bass alignment scoring"""
```

---

### Sprint 2.3: UI Enhancements Part 1 (Weeks 9-10)

#### Task 2.3.1: Multi-Candidate Display in UI
- **ID**: MIDI-210
- **Priority**: 🔴 Critical Path
- **Effort**: 8 hours
- **Type**: 🎨 UI/UX

**Description**: Show top 3 chord candidates in PyQt UI

**Acceptance Criteria**:
- [ ] Update `main_window.py` to display candidate list
- [ ] Show: rank, chord name, confidence %, reason
- [ ] Highlight primary candidate (bold, green)
- [ ] Clickable alternates (user can select)
- [ ] Update in real-time

**UI Mockup**:
```
Detected Chords:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ★ Cmaj7         [92%]
   Root: C  Bass: E
   Strong match; Missing: none

2.   C6/9          [85%]
   Root: C  Bass: E
   Good match; Missing: 6

3.   Am7/C         [78%]
   Root: A  Bass: C
   Possible match; Extra: E
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Testing**:
- Manual test: play various chords, verify display updates
- Test: click alternate candidate, verify selection

---

#### Task 2.3.2: Explanation Panel
- **ID**: MIDI-211
- **Priority**: 🟡 High
- **Effort**: 6 hours
- **Type**: 🎨 UI/UX

**Description**: Add expandable panel showing detection details

**Acceptance Criteria**:
- [ ] Collapsible panel below candidate list
- [ ] Show matched intervals (green): ✓ R, ✓ 3, ✓ 7
- [ ] Show missing intervals (yellow): ∅ 5
- [ ] Show extra intervals (gray): + 9
- [ ] Show score breakdown:
  - Interval match: 0.85
  - Voicing: 0.90
  - Context: 0.60
  - Total: 0.87
- [ ] Show bass note and inversion info

**Testing**:
- Manual test: expand/collapse panel
- Test: intervals displayed correctly

---

#### Task 2.3.3: Voice-Colored Piano Keyboard
- **ID**: MIDI-212
- **Priority**: 🟢 Medium
- **Effort**: 8 hours
- **Type**: 🎨 UI/UX

**Description**: Color piano keys by voice role

**Acceptance Criteria**:
- [ ] Update `piano_keyboard_widget.py`
- [ ] Color coding:
  - Bass notes: Red
  - Chord tones: Blue
  - Melody notes: Yellow
  - Omitted expected notes: Gray outline
- [ ] Legend explaining colors
- [ ] Toggle: "Show Expected Notes" (gray outlines)

**Testing**:
- Manual test: play chord with bass, verify bass key is red
- Test: play melody + chord, verify melody is yellow

---

#### Task 2.3.4: Configuration UI
- **ID**: MIDI-213
- **Priority**: 🟢 Medium
- **Effort**: 6 hours
- **Type**: 🎨 UI/UX

**Description**: Add settings panel for configuration

**Settings to Expose**:
- [ ] Time window (ms): slider 0-200ms
- [ ] Voice ranges: bass/chord/melody (MIDI note spinboxes)
- [ ] Filter melody: checkbox
- [ ] Max candidates: spinner 1-10
- [ ] Context awareness: checkbox (Phase 3)
- [ ] Key detection: checkbox (Phase 3)

**Testing**:
- Manual test: adjust settings, verify applied
- Test: settings persist (save/load)

---

### Sprint 2.4: Testing & Refinement (Weeks 11-12)

#### Task 2.4.1: Integration Tests with Voice Separation
- **ID**: MIDI-214
- **Priority**: 🟡 High
- **Effort**: 6 hours
- **Type**: 🧪 Testing

**Tests**:
- Test: Bass + chord voicing (slash chord)
- Test: Piano style (bass + chord + melody)
- Test: Guitar voicing (close position)
- Test: Wide voicing (>2 octaves)

---

#### Task 2.4.2: Accuracy Measurements
- **ID**: MIDI-215
- **Priority**: 🟡 High
- **Effort**: 8 hours
- **Type**: 🧪 Testing

**Description**: Measure detection accuracy on test corpus

**Acceptance Criteria**:
- [ ] Test against 10+ annotated MIDI files
- [ ] Calculate metrics:
  - Exact match accuracy (chord name)
  - Top-3 accuracy (correct chord in top 3)
  - Root accuracy (correct root)
  - Quality accuracy (major/minor/dom/etc.)
- [ ] Generate confusion matrix
- [ ] Identify failure patterns

**Targets**:
- Simple chords: ≥90% exact match
- Extended chords: ≥75% exact match
- Top-3 accuracy: ≥90%

---

#### Task 2.4.3: Performance Optimization
- **ID**: MIDI-216
- **Priority**: 🟡 High
- **Effort**: 6 hours

**Description**: Optimize hot paths for real-time performance

**Acceptance Criteria**:
- [ ] Profile with cProfile
- [ ] Optimize candidate generation (cache lookups)
- [ ] Optimize scoring (vectorize if needed)
- [ ] Target: <10ms latency maintained

---

#### Task 2.4.4: Bug Fixes & Code Review
- **ID**: MIDI-217
- **Priority**: 🔴 Critical
- **Effort**: 8 hours

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] Code review completed
- [ ] No regressions
- [ ] Documentation updated
- [ ] Merge Phase 2 to main

---

## Phase 3: Context Awareness (Weeks 13-20)

### Sprint 3.1: Context Tracking (Weeks 13-14)

#### Task 3.1.1: Create ChordContext Class
- **ID**: MIDI-301
- **Priority**: 🔴 Critical Path
- **Effort**: 6 hours
- **Type**: 🏗️ Foundation

**Description**: Implement chord history tracking

**Acceptance Criteria**:
- [ ] `ChordContext` class in `core/chord_context.py`
- [ ] Methods: `add_chord()`, `_cleanup_old()`, `get_progression_pattern()`
- [ ] Track last 10 chords with timestamps
- [ ] Remove chords older than 10 seconds
- [ ] Thread-safe

**Testing**:
- Test: add chords, verify history
- Test: old chords removed after timeout

---

#### Task 3.1.2: Key Detection Algorithm
- **ID**: MIDI-302
- **Priority**: 🟡 High
- **Effort**: 8 hours
- **Depends On**: MIDI-301

**Description**: Implement Krumhansl-Schmuckler key detection

**Acceptance Criteria**:
- [ ] Method `ChordContext._update_key_detection()`
- [ ] Use pitch class distribution from chord history
- [ ] Compare to major/minor key profiles
- [ ] Return detected key + confidence (0-1)
- [ ] Update on each new chord (if 4+ chords in history)

**Testing**:
- Test: C major progression → key = "C major"
- Test: A minor progression → key = "A minor"
- Test: Mixed chromatic → low confidence

---

#### Task 3.1.3: Integrate Context into Recognition
- **ID**: MIDI-303
- **Priority**: 🔴 Critical Path
- **Effort**: 4 hours
- **Depends On**: MIDI-301

**Description**: Pass context to candidate generator

**Acceptance Criteria**:
- [ ] Instantiate `ChordContext` in `ChordTheory.__init__`
- [ ] After each chord detection, call `context.add_chord(result)`
- [ ] Pass context to `generator.generate_candidates()`
- [ ] Include context info in output (detected key, progression)

---

#### Task 3.1.4: Unit Tests for Context
- **ID**: MIDI-304
- **Priority**: 🟡 High
- **Effort**: 4 hours
- **Type**: 🧪 Testing

**Tests**:
```python
def test_add_chord_to_context():
def test_cleanup_old_chords():
def test_key_detection_c_major():
def test_key_detection_a_minor():
def test_key_confidence():
```

---

### Sprint 3.2: Progression Recognition (Weeks 15-16)

#### Task 3.2.1: Implement Progression Pattern Matching
- **ID**: MIDI-305
- **Priority**: 🟡 High
- **Effort**: 8 hours
- **Depends On**: MIDI-303

**Description**: Detect common chord progressions

**Patterns to Detect**:
- [ ] ii-V-I (jazz)
- [ ] I-vi-ii-V
- [ ] V-I (cadence)
- [ ] IV-V-I
- [ ] Circle of 5ths
- [ ] Secondary dominants
- [ ] Tritone substitutions

**Implementation**:
```python
def get_progression_pattern(self) -> Optional[str]:
    # Check last 2-4 chords for patterns
    # Return pattern name or None
```

**Testing**:
- Test: Dm7 → G7 → Cmaj7 → pattern = "ii-V-I"
- Test: C → A7 → Dm → pattern = "I-V/ii-ii" (secondary dom)

---

#### Task 3.2.2: Context-Based Score Adjustment
- **ID**: MIDI-306
- **Priority**: 🔴 Critical Path
- **Effort**: 6 hours
- **Depends On**: MIDI-305

**Description**: Boost expected chords based on context

**Acceptance Criteria**:
- [ ] In `_score_context()`, check for progression patterns
- [ ] If ii-V in progress: boost dom7/9/13 candidates by +0.2
- [ ] If V-I expected: boost tonic candidates by +0.2
- [ ] Penalize unlikely jumps (e.g., C → F# unless explained)
- [ ] Configurable: "Strict mode" (no boost) vs. "Jazz mode" (full boost)

**Testing**:
- Test: ii-V progression → V chord boosted
- Test: Random progression → no boost (neutral)

---

#### Task 3.2.3: Tritone Substitution Detection
- **ID**: MIDI-307
- **Priority**: 🟢 Medium
- **Effort**: 4 hours

**Description**: Detect tritone subs (Db7 instead of G7)

**Acceptance Criteria**:
- [ ] If expecting V chord, also consider bII7 (tritone sub)
- [ ] Boost tritone sub candidate if context suggests V

**Testing**:
- Test: ii-V-I with Db7 instead of G7 → still recognized as V function

---

#### Task 3.2.4: Unit Tests for Progression Recognition
- **ID**: MIDI-308
- **Priority**: 🟡 High
- **Effort**: 4 hours
- **Type**: 🧪 Testing

**Tests**:
```python
def test_ii_v_i_detection():
def test_v_i_detection():
def test_secondary_dominant():
def test_tritone_substitution():
def test_context_score_boost():
```

---

### Sprint 3.3: User Features (Weeks 17-18)

#### Task 3.3.1: Manual Chord Correction UI
- **ID**: MIDI-309
- **Priority**: 🟡 High
- **Effort**: 6 hours
- **Type**: 🎨 UI/UX

**Description**: Allow user to override detected chord

**Acceptance Criteria**:
- [ ] Dropdown in UI to select from candidate list
- [ ] Text input for custom chord name
- [ ] "Save Correction" button
- [ ] Visual indicator when chord is overridden (yellow border)

**Testing**:
- Manual test: override chord, verify displayed
- Test: correction persists until notes change

---

#### Task 3.3.2: Save Corrections to File
- **ID**: MIDI-310
- **Priority**: 🟢 Medium
- **Effort**: 4 hours
- **Depends On**: MIDI-309

**Description**: Save user corrections for future learning

**Acceptance Criteria**:
- [ ] File: `data/corrections.json`
- [ ] Format: `{notes_hash: {detected: "Cmaj7", corrected: "C6/9", timestamp: ...}}`
- [ ] Append new corrections (don't overwrite)
- [ ] Option to "Improve Detection" using corrections (Phase 4)

---

#### Task 3.3.3: User-Defined Chord Definitions
- **ID**: MIDI-311
- **Priority**: 🟢 Medium
- **Effort**: 8 hours
- **Type**: 🎨 UI/UX

**Description**: UI for adding/editing chord definitions

**Acceptance Criteria**:
- [ ] "Chord Editor" dialog in UI
- [ ] Fields: chord type, name, required/core/optional intervals
- [ ] Validate input (no duplicates, valid ranges)
- [ ] Save to `data/user_chord_definitions.json`
- [ ] User defs override defaults
- [ ] Import/export custom definition sets (JSON files)

**Testing**:
- Manual test: add new chord type, verify detected
- Test: edit existing chord, verify changes applied

---

#### Task 3.3.4: Settings Persistence
- **ID**: MIDI-312
- **Priority**: 🟢 Medium
- **Effort**: 3 hours
- **Type**: ⚡ Quick Win

**Description**: Save/load user settings

**Acceptance Criteria**:
- [ ] Save settings to `config.yaml` or `settings.json`
- [ ] Load on startup
- [ ] Apply to all configurable parameters

---

### Sprint 3.4: Final Testing & Release (Weeks 19-20)

#### Task 3.4.1: Comprehensive Integration Tests
- **ID**: MIDI-313
- **Priority**: 🔴 Critical
- **Effort**: 8 hours
- **Type**: 🧪 Testing

**Description**: Test all features end-to-end

**Test Scenarios**:
- [ ] Play jazz standard (ii-V-I progressions)
- [ ] Play pop song (I-V-vi-IV)
- [ ] Play blues (12-bar blues)
- [ ] Play with melody (filter melody notes)
- [ ] Override chord manually
- [ ] Add custom chord definition
- [ ] Adjust settings

---

#### Task 3.4.2: Accuracy Validation
- **ID**: MIDI-314
- **Priority**: 🔴 Critical
- **Effort**: 6 hours
- **Type**: 🧪 Testing

**Description**: Final accuracy measurements

**Acceptance Criteria**:
- [ ] Test on 20+ MIDI files (10 jazz, 10 pop/other)
- [ ] Measure accuracy (exact, top-3, root, quality)
- [ ] Compare Phase 3 vs. Phase 2 vs. Phase 1
- [ ] Document accuracy improvements

**Targets**:
- Simple chords: ≥95%
- Extended chords: ≥80%
- Altered chords: ≥70%
- Top-3 accuracy: ≥90%

---

#### Task 3.4.3: Performance Validation
- **ID**: MIDI-315
- **Priority**: 🟡 High
- **Effort**: 4 hours
- **Type**: 🧪 Testing

**Acceptance Criteria**:
- [ ] Benchmark latency (<10ms maintained)
- [ ] Benchmark CPU (<10% maintained)
- [ ] Benchmark memory (<100MB)
- [ ] Profile and optimize if needed

---

#### Task 3.4.4: Documentation Finalization
- **ID**: MIDI-316
- **Priority**: 🟡 High
- **Effort**: 8 hours
- **Type**: 📚 Documentation

**Documents to Create/Update**:
- [ ] README.md (features, installation, usage)
- [ ] CHANGELOG.md (v2.0 release notes)
- [ ] USER-GUIDE.md (how to use, screenshots)
- [ ] API-REFERENCE.md (for developers)
- [ ] CONTRIBUTING.md (how to contribute)
- [ ] LICENSE (if not exists)

---

#### Task 3.4.5: Release v2.0
- **ID**: MIDI-317
- **Priority**: 🔴 Critical
- **Effort**: 4 hours

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] All documentation complete
- [ ] Code reviewed and merged
- [ ] Tag release: `v2.0.0`
- [ ] GitHub release with notes
- [ ] Optional: Package and distribute (PyPI, exe)

---

## Summary

### Total Tasks: 67
### Estimated Effort: 320-380 hours (20-24 weeks for 1 developer, 16-20 weeks for 2)

### Phase Breakdown:
- **Phase 1** (4 weeks): 16 tasks, ~60 hours
- **Phase 2** (8 weeks): 17 tasks, ~120 hours
- **Phase 3** (8 weeks): 17 tasks, ~100 hours

### Task Type Distribution:
- 🏗️ Foundation: 8 tasks
- 🧪 Testing: 15 tasks
- 🎨 UI/UX: 10 tasks
- 📚 Documentation: 7 tasks
- ⚡ Quick Wins: 5 tasks
- 🔴 Critical Path: 22 tasks

---

## Next Steps

1. **Review this task breakdown** with stakeholders
2. **Prioritize** tasks based on business value
3. **Set up project tracking** (GitHub Projects, Jira, Trello)
4. **Create task cards** for each task (copy from here)
5. **Assign tasks** to developers
6. **Begin Phase 1** Sprint 1.1

---

**Document Version**: 1.0  
**Last Updated**: December 5, 2025  
**Next Document**: `05-TESTING-STRATEGY.md` (optional)
