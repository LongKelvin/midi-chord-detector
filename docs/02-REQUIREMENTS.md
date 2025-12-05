# MIDI Chord Detector: Detailed Requirements

## Document Overview

**Purpose**: Define specific, actionable requirements for enhancing the MIDI chord detector to support jazz/complex chords  
**Scope**: Phase 1-3 improvements (fuzzy matching → context awareness)  
**Target Timeline**: 3-4 months of development  
**Priority**: Essential features for jazz chord detection

---

## 1. Functional Requirements

### FR-1: Fuzzy Chord Matching

**ID**: FR-1  
**Priority**: **CRITICAL** (Phase 1)  
**Description**: Detect chords even when notes are omitted or extra notes are present

#### FR-1.1: Support Omitted Notes
- **Requirement**: Recognize chords when optional intervals are missing
- **Examples**:
  - C major with no 5th: [C, E] → detect as "Cmaj (no5)"
  - Cmaj7 with no 5th: [C, E, B] → detect as "Cmaj7 (no5)"
  - C13 with only [E, Bb, D, A] → detect as "C13 (omit root, omit 5)"
  
- **Acceptance Criteria**:
  - ✅ Detect all major/minor triads with omitted 5th
  - ✅ Detect 7th chords with omitted 5th
  - ✅ Detect extended chords (9,11,13) with omitted root
  - ✅ Score reflects omitted notes (penalty < 0.2)

#### FR-1.2: Interval Priority System
- **Requirement**: Define which intervals are essential vs. optional per chord type
- **Rules**:
  ```
  Triads:
    Essential: root OR 3rd (at least one)
    Optional: 5th
  
  7th Chords:
    Essential: 3rd OR 7th (quality-defining)
    Optional: root, 5th
  
  Extended Chords (9/11/13):
    Essential: 7th + extension (9, 11, or 13)
    Optional: root, 5th, intermediate extensions
  ```

- **Acceptance Criteria**:
  - ✅ Chord definitions include `required`, `important`, `optional` fields
  - ✅ Scoring algorithm weights intervals accordingly
  - ✅ Cannot detect chord without essential intervals

#### FR-1.3: Handle Extra Notes (Non-Chord Tones)
- **Requirement**: Tolerate extra notes without rejecting chord match
- **Examples**:
  - C major + D (add9): [C, D, E, G] → "Cadd9" or "Cmaj"
  - C major + F (passing tone): [C, E, F, G] → "Cmaj" (F = melody/passing)
  
- **Acceptance Criteria**:
  - ✅ Extra notes reduce score but don't eliminate match
  - ✅ Penalty capped at max 0.2 (4+ extra notes)
  - ✅ Extra note analysis distinguishes extensions vs. non-chord tones

---

### FR-2: Time-Window Chord Aggregation

**ID**: FR-2  
**Priority**: **HIGH** (Phase 1)  
**Description**: Collect notes over a time window to handle rolled/arpeggiated chords

#### FR-2.1: Configurable Time Window
- **Requirement**: Allow time-window configuration for note collection
- **Parameters**:
  - `time_window_ms`: 50-150ms (default: 80ms)
  - `note_decay_time`: How long notes remain in buffer (default: 100ms)
  
- **Acceptance Criteria**:
  - ✅ Notes played within window are aggregated
  - ✅ Window configurable via settings/UI
  - ✅ Real-time performance maintained (<5ms latency)

#### FR-2.2: Weighted Time Decay
- **Requirement**: Newer notes weighted more heavily than older notes
- **Algorithm**:
  ```python
  weight = e^(-t / decay_constant)
  where t = time since note onset
  ```

- **Acceptance Criteria**:
  - ✅ Recent notes (0-50ms) have full weight (1.0)
  - ✅ Older notes (50-100ms) have reduced weight (0.5-0.8)
  - ✅ Very old notes (>150ms) excluded or minimal weight (<0.3)

---

### FR-3: Voice Separation

**ID**: FR-3  
**Priority**: **HIGH** (Phase 2)  
**Description**: Separate bass, chord tones, and melody notes by register

#### FR-3.1: Register-Based Separation
- **Requirement**: Define MIDI note ranges for bass, chord, melody
- **Default Ranges**:
  ```
  Bass:    MIDI 21-60  (A0-C4)
  Chord:   MIDI 36-84  (C2-C6)
  Melody:  MIDI 60-108 (C4-C8)
  ```

- **Acceptance Criteria**:
  - ✅ Lowest note in bass range treated as bass note
  - ✅ Notes in chord range used for chord detection
  - ✅ Notes in melody range excluded from chord (optional toggle)
  - ✅ Ranges configurable per instrument (piano/guitar/bass)

#### FR-3.2: Bass Note Detection & Slash Chords
- **Requirement**: Detect when bass note ≠ chord root (slash chords)
- **Examples**:
  - C/E: Bass = E, Chord = C major → "C major, 1st inversion" or "C/E"
  - Dm7/G: Bass = G, Chord = Dm7 → "Dm7/G"
  
- **Acceptance Criteria**:
  - ✅ Bass note always reported separately
  - ✅ Slash chord notation when bass ≠ root
  - ✅ Inversion detection for standard inversions
  - ✅ Score bonus for matching inversions

#### FR-3.3: Melody Note Filtering (Optional)
- **Requirement**: Optionally exclude highest notes from chord detection
- **Algorithm**:
  - If notes span >2 octaves AND highest note is >P8 above next note → exclude
  
- **Acceptance Criteria**:
  - ✅ Toggle in settings: "Exclude Melody Notes"
  - ✅ Improve accuracy for piano/guitar comping with melody
  - ✅ Visual indicator in UI showing excluded notes

---

### FR-4: Candidate Ranking System

**ID**: FR-4  
**Priority**: **HIGH** (Phase 2)  
**Description**: Generate and rank multiple chord candidates instead of single result

#### FR-4.1: Generate Top-N Candidates
- **Requirement**: For each note set, generate up to 5 candidate chords
- **Process**:
  1. Try all 12 roots as potential chord roots
  2. Try all chord types (maj, min, 7, 9, 11, 13, alt, etc.)
  3. Score each candidate
  4. Rank by score + context
  5. Return top 3-5

- **Acceptance Criteria**:
  - ✅ All candidates have score ≥ 0.4 (threshold)
  - ✅ Candidates sorted by total score (matching + context)
  - ✅ Include confidence level (0-100%)
  - ✅ Provide reason string (e.g., "Missing 5th, strong 3rd match")

#### FR-4.2: Scoring Algorithm Enhancement
- **Requirement**: Comprehensive scoring considering multiple factors
- **Score Components**:
  ```python
  total_score = (
      interval_match_score * 0.4 +      # How well intervals match
      voicing_score * 0.2 +              # Spacing/voicing quality
      context_score * 0.2 +              # Progression context
      frequency_score * 0.1 +            # Common chord bonus
      bass_match_score * 0.1             # Bass note alignment
  )
  ```

- **Acceptance Criteria**:
  - ✅ Interval matching: weighted by importance (3rd/7th > 5th)
  - ✅ Voicing scoring: prefers typical jazz voicings (drop-2, shell)
  - ✅ Context scoring: smooth voice leading preferred
  - ✅ Frequency scoring: common chords slightly boosted
  - ✅ Bass matching: bonus if bass = root or inversion tone

#### FR-4.3: Ambiguity Indicators
- **Requirement**: Flag when multiple interpretations are equally valid
- **Triggers**:
  - Top 2 candidates within 0.1 score difference
  - Enharmonic equivalents (e.g., C7b9 ≈ Dbmaj7#11)
  
- **Acceptance Criteria**:
  - ✅ UI shows "ambiguous" indicator
  - ✅ Display both/all equally-valid candidates
  - ✅ Allow user to pick preferred interpretation

---

### FR-5: Context-Aware Chord Recognition

**ID**: FR-5  
**Priority**: **MEDIUM** (Phase 3)  
**Description**: Use harmonic context (previous chords, key) to improve accuracy

#### FR-5.1: Chord History Tracking
- **Requirement**: Maintain buffer of last 5-10 chords
- **Data Stored**:
  - Chord root, quality, time
  - Key signature (if detected)
  - Harmonic function (I, IV, V, ii, etc.)

- **Acceptance Criteria**:
  - ✅ Chord history stored in memory (thread-safe)
  - ✅ Oldest chords expire after 10 seconds
  - ✅ Accessible to scoring algorithm

#### FR-5.2: Progression Pattern Recognition
- **Requirement**: Detect common chord progressions and boost expected chords
- **Patterns to Recognize**:
  - **ii-V-I**: Dm7 → G7 → Cmaj7
  - **I-vi-ii-V**: C → Am → Dm → G
  - **Circle of 5ths**: C → F → Bb → Eb...
  - **Secondary dominants**: C → A7 → Dm
  - **Tritone substitutions**: Db7 instead of G7 → Cmaj7

- **Acceptance Criteria**:
  - ✅ If previous = Dm7, boost G7/G9/G13/G7alt candidates by +0.2
  - ✅ If previous = G7, boost C/Cmaj7 candidates by +0.2
  - ✅ Penalize unlikely jumps (e.g., C → F# unless secondary dom)
  - ✅ Configurable: "Strict mode" (no context) vs. "Jazz mode" (full context)

#### FR-5.3: Key Detection Integration
- **Requirement**: Optionally detect key and prefer diatonic chords
- **Algorithm** (lightweight):
  - Track pitch class distribution over last 8-16 chords
  - Score against major/minor key profiles
  - Boost chords that fit key signature

- **Acceptance Criteria**:
  - ✅ Key detection optional (toggle in settings)
  - ✅ UI displays detected key (e.g., "Key: C major")
  - ✅ Diatonic chords get +0.1 boost, chromatic chords no penalty
  - ✅ Key can be manually overridden by user

---

### FR-6: Enhanced Chord Definitions

**ID**: FR-6  
**Priority**: **HIGH** (Phase 1-2)  
**Description**: Expand and enhance chord definition database

#### FR-6.1: Jazz/Altered Chord Support
- **Requirement**: Add comprehensive jazz chord types
- **New Chord Types to Add**:
  ```
  Altered Dominants:
  - 7alt (generic altered)
  - 7b5b9, 7b5#9, 7#5b9, 7#5#9
  - 7#9#11, 7b9#11, 7b9b13
  
  Extended Dominants:
  - 9, 9#11, 9b13
  - 11 (true 11th, not sus4)
  - 13, 13#11, 13b9
  
  Minor Extensions:
  - m9, m11, m13
  - m6/9, m7b5, mMaj7, mMaj9
  
  Special:
  - dim7 (fully diminished)
  - sus2, sus4, 7sus4
  - add9, add11, 6/9
  - b5, #5 (augmented)
  ```

- **Acceptance Criteria**:
  - ✅ All chord types defined in JSON
  - ✅ Each has `required`, `optional`, `alterations` fields
  - ✅ Unit tests verify each chord type detects correctly

#### FR-6.2: Chord Definition Schema v2.0
- **Requirement**: Enhance JSON schema with richer metadata
- **New Schema**:
  ```json
  {
    "chord_type": {
      "name": "Dominant 7th Flat 9",
      "symbol": "7b9",
      "required_intervals": [3, 10],      // Must have 3rd and b7
      "core_intervals": [0, 4, 7, 10],    // Full chord
      "optional_intervals": [7],          // 5th can be omitted
      "alterations": [1],                 // b9
      "interval_weights": {
        "0": 0.7, "3": 1.0, "7": 0.5, "10": 1.0, "1": 0.9
      },
      "typical_voicings": [
        [0, 4, 10, 1],   // Root position
        [4, 10, 1, 12]   // No root, with octave
      ],
      "complexity": "advanced",
      "genre_tags": ["jazz", "blues", "bebop"],
      "function": "dominant",
      "resolution_tendency": ["maj", "min"]
    }
  }
  ```

- **Acceptance Criteria**:
  - ✅ Backward compatible with existing definitions
  - ✅ Enhanced fields optional (defaults provided)
  - ✅ Loader validates schema and provides warnings

#### FR-6.3: User-Defined Chord Definitions
- **Requirement**: Allow users to add/edit chord definitions via UI
- **Features**:
  - Add new chord type
  - Edit existing chord intervals/weights
  - Import/export custom definition sets
  - Share custom definitions with community

- **Acceptance Criteria**:
  - ✅ UI for chord definition editor (Phase 3)
  - ✅ Validate user input (no duplicate intervals, valid ranges)
  - ✅ Custom definitions saved to `user_chord_definitions.json`
  - ✅ User defs override defaults with same chord_type key

---

### FR-7: Improved UI/UX

**ID**: FR-7  
**Priority**: **MEDIUM** (Phase 2-3)  
**Description**: Enhance user interface to show detection details and allow corrections

#### FR-7.1: Candidate Chord Display
- **Requirement**: Show top 3 chord candidates with scores
- **UI Mockup**:
  ```
  Detected Chord:
  ┌─────────────────────────────────────┐
  │ 1. Cmaj7        [92%] ★ SELECTED    │
  │    Root: C, Bass: E                 │
  │    Notes: C-E-G-B                   │
  │                                      │
  │ 2. C6/9         [85%]               │
  │    Root: C, Bass: E                 │
  │    Notes: C-E-G-A-D (missing 6)     │
  │                                      │
  │ 3. Am7/C        [78%]               │
  │    Root: A, Bass: C                 │
  └─────────────────────────────────────┘
  ```

- **Acceptance Criteria**:
  - ✅ Display top 3 candidates sorted by confidence
  - ✅ Highlight selected/primary chord
  - ✅ Show confidence % (0-100%)
  - ✅ Click to select alternate candidate
  - ✅ Show which notes matched/missing/extra

#### FR-7.2: Detection Explanation Panel
- **Requirement**: Explain why a chord was detected/scored
- **Information to Display**:
  - Matched intervals: ✓ R, ✓ 3, ✓ 7, ✗ 5 (omitted)
  - Extra notes: +9 (add9)
  - Bass note: E (1st inversion)
  - Context: "Follows Dm7 in ii-V progression"
  - Score breakdown: Match 0.85 + Context 0.10 = 0.95

- **Acceptance Criteria**:
  - ✅ Expandable panel in UI (default collapsed)
  - ✅ Updates in real-time
  - ✅ Uses color coding (green=match, yellow=optional, red=extra)

#### FR-7.3: Manual Chord Correction
- **Requirement**: Allow user to override detected chord
- **Features**:
  - Dropdown to select from candidate list
  - Text input for custom chord name
  - "Teach" button to save correction as training data

- **Acceptance Criteria**:
  - ✅ Override persists until notes change
  - ✅ Corrections saved to `corrections.json`
  - ✅ Option to "Improve detection" using saved corrections (Phase 3)
  - ✅ Visual indicator when chord is manually overridden

#### FR-7.4: Voice Visualization
- **Requirement**: Show notes colored by role (bass/chord/melody)
- **Piano Keyboard Display**:
  - Bass notes: Red
  - Chord tones: Blue
  - Melody/extra notes: Yellow
  - Omitted expected notes: Gray outline

- **Acceptance Criteria**:
  - ✅ Real-time color update on virtual keyboard
  - ✅ Legend explaining colors
  - ✅ Toggle to show/hide expected but missing notes

---

### FR-8: Testing & Quality Assurance

**ID**: FR-8  
**Priority**: **HIGH** (All Phases)  
**Description**: Comprehensive testing framework for chord detection accuracy

#### FR-8.1: Unit Test Suite
- **Requirement**: Automated tests for all chord types
- **Coverage**:
  - Each chord type (100+ chords)
  - Each chord type with omitted 5th
  - Each chord type with added 9th
  - Each inversion
  - Common voicings (drop-2, drop-3, shell voicings)

- **Acceptance Criteria**:
  - ✅ >200 unit tests
  - ✅ 90%+ detection accuracy on standard voicings
  - ✅ 75%+ detection accuracy on altered voicings
  - ✅ Tests run in CI/CD pipeline

#### FR-8.2: Integration Test Suite (MIDI Files)
- **Requirement**: Test against real jazz MIDI files
- **Test Corpus**:
  - 20+ jazz standards (Autumn Leaves, Blue Bossa, etc.)
  - Manually annotated with expected chords
  - Various playing styles (piano, guitar, combo)

- **Acceptance Criteria**:
  - ✅ Test framework loads MIDI, runs detector, compares to annotations
  - ✅ Generate accuracy report (% correct, confusion matrix)
  - ✅ Identify specific failure patterns
  - ✅ Regression testing (accuracy doesn't decrease)

#### FR-8.3: Performance Benchmarks
- **Requirement**: Ensure real-time performance
- **Metrics**:
  - Detection latency: <10ms (target: <5ms)
  - CPU usage: <10% single core
  - Memory usage: <50MB
  - Supports up to 10 simultaneous notes

- **Acceptance Criteria**:
  - ✅ Automated benchmark suite
  - ✅ Performance regression tests
  - ✅ Profiling reports identify bottlenecks

---

## 2. Non-Functional Requirements

### NFR-1: Performance
- Real-time chord detection with <10ms latency
- Minimal CPU/memory usage for background processing
- Smooth UI updates (60 FPS)

### NFR-2: Reliability
- Handle malformed MIDI input gracefully
- No crashes on unexpected note combinations
- Graceful degradation if advanced features fail

### NFR-3: Usability
- Intuitive UI for musicians (not just developers)
- Helpful error messages and tooltips
- Keyboard shortcuts for common actions

### NFR-4: Maintainability
- Clean, documented code (docstrings, type hints)
- Modular architecture (easy to swap components)
- Comprehensive logging for debugging

### NFR-5: Extensibility
- Plugin architecture for new chord detection algorithms
- Easy to add new chord types via JSON
- API for external integrations (DAWs, notation software)

---

## 3. Technical Requirements

### TR-1: Dependencies
- **Existing**: mido, zmq, PyQt6
- **New (Phase 1-2)**:
  - music21 (optional, chord naming fallback)
  - numpy (efficient interval calculations)
- **New (Phase 3, optional)**:
  - scikit-learn (pattern matching, clustering)

### TR-2: Python Version
- Minimum: Python 3.9
- Target: Python 3.10-3.11

### TR-3: Platform Support
- Windows (primary)
- macOS (secondary)
- Linux (best-effort)

### TR-4: Configuration
- Settings stored in `config.yaml` or JSON
- CLI arguments override config file
- UI settings panel for common options

---

## 4. User Stories

### US-1: Jazz Pianist
> "As a jazz pianist, I want the detector to recognize my voiced chords (no 5th, no root) so that I can see accurate chord symbols during practice."

**Acceptance**: Detects 80%+ of common jazz piano voicings (drop-2, rootless)

### US-2: Guitar Learner
> "As a guitar student, I want to see multiple possible chord names for the voicing I played, so I can understand chord theory better."

**Acceptance**: Shows 2-3 valid interpretations with explanations

### US-3: Music Theory Teacher
> "As a teacher, I want to see which notes are essential vs. optional in detected chords, so I can explain chord construction to students."

**Acceptance**: UI shows color-coded essential/optional/extra notes

### US-4: Composer
> "As a composer, I want the detector to understand chord progressions (ii-V-I) so it doesn't mis-identify chords out of context."

**Acceptance**: Progression-aware mode boosts accuracy by 10-15%

### US-5: Live Performer
> "As a performer, I need instant chord detection (<10ms) with no lag, even with complex voicings."

**Acceptance**: <10ms latency, <10% CPU usage on modern hardware

---

## 5. Success Metrics

### Accuracy Metrics
- **Simple chords (triads, 7ths)**: ≥95% accuracy
- **Extended chords (9/11/13)**: ≥80% accuracy
- **Altered chords**: ≥70% accuracy
- **Ambiguous cases**: Top 3 candidates include correct answer ≥90%

### Performance Metrics
- Latency: ≤10ms (95th percentile)
- CPU: ≤10% single core
- Memory: ≤100MB

### User Satisfaction (if measurable)
- User corrections: <10% of detected chords need manual override
- Net Promoter Score (NPS): ≥50 (if collecting feedback)

---

## 6. Out of Scope (Future Work)

❌ **NOT included in Phase 1-3**:
- Machine learning / neural network models
- Audio input (only MIDI)
- Automatic transcription from audio
- Multi-track MIDI (drums, bass, chords simultaneously)
- Real-time key modulation detection (basic key detection only)
- Quartal/quintal harmony, polychords, tone clusters
- Microtonal music, non-12-TET systems

---

## 7. Prioritization Summary

| Phase | Requirements | Timeline | Effort |
|-------|-------------|----------|--------|
| **Phase 1** | FR-1 (Fuzzy Matching), FR-2 (Time Window), FR-6 (Enhanced Definitions) | 1 month | High |
| **Phase 2** | FR-3 (Voice Separation), FR-4 (Ranking), FR-7.1-7.2 (UI) | 1.5 months | High |
| **Phase 3** | FR-5 (Context), FR-7.3-7.4 (Manual Correction), FR-6.3 (User Defs) | 1.5 months | Medium |

**Total estimated time**: 4 months for Phases 1-3

---

**Document Version**: 1.0  
**Last Updated**: December 5, 2025  
**Next Document**: `03-TECHNICAL-DESIGN.md`
