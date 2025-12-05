# MIDI Chord Detector: Problem Analysis & Current State

## Executive Summary

This document analyzes the current state of the MIDI chord detector project and identifies why it works well for simple chords but struggles with jazz/complex chords.

**Current State**: `feature/advanced-chord-detection` branch  
**Date**: December 5, 2025  
**Analysis Type**: Architecture Review & Enhancement Planning

---

## 1. Current Architecture Overview

### 1.1 Core Components

```
┌──────────────────────────────────────────────────────────┐
│                  MIDI Input Layer                         │
│  (MIDIChordRecognizer - chord_recognition_engine.py)     │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│              Music Theory Engine                          │
│           (ChordTheory - music_theory.py)                │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Basic Recognition (Pattern Matching)              │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Advanced Recognition (optional)                   │  │
│  │  (AdvancedChordAnalyzer)                          │  │
│  └────────────────────────────────────────────────────┘  │
└────────────────┬─────────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│              Output Layer                                 │
│  - ZMQ Publisher (real-time streaming)                   │
│  - UI Callback (PyQt6 display)                          │
└──────────────────────────────────────────────────────────┘
```

### 1.2 Current Recognition Flow

```python
# Simplified current algorithm
1. Collect MIDI note-on events → Set[int] of MIDI notes
2. Apply sustain pedal logic
3. Convert MIDI notes → pitch classes (0-11)
4. Match against chord_definitions.json:
   - Exact/fuzzy pattern matching
   - Score calculation (core + optional intervals)
5. Select best match (highest score > threshold)
6. Return: {root, bass, chord_type, inversion, score}
```

---

## 2. What Works Well (Simple Chords)

### 2.1 Success Cases

✅ **Triads** (Major, Minor, Diminished, Augmented)
- Clear interval patterns: [0,4,7], [0,3,7], [0,3,6], [0,4,8]
- Small note count (3 notes)
- Well-defined inversions

✅ **Basic 7th Chords** (maj7, min7, dom7)
- Standard patterns: [0,4,7,11], [0,3,7,10], [0,4,7,10]
- Common in pop/rock/blues
- Limited ambiguity

✅ **Power Chords & Sus Chords**
- Simple intervals: [0,7], [0,5,7], [0,2,7]
- Rock/metal contexts

### 2.2 Why These Work

1. **Low Complexity**: 3-4 notes maximum
2. **Exact Matching Possible**: Notes are almost always complete
3. **Clear Definitions**: Little room for interpretation
4. **Simultaneous Attack**: Pop/rock playing tends to strike chords together
5. **Standard Voicings**: Close position, octave-doubled

---

## 3. What Fails (Jazz/Complex Chords)

### 3.1 Failure Scenarios

❌ **Extended Chords** (9th, 11th, 13th)
```
Problem: C13 = [C, E, G, Bb, D, F, A] (7 notes!)
Reality: Pianist plays [D, G, Bb, E, A] (no root, no 5th)
Result: Detector sees Gm9 or Em7b5 or unknown
```

❌ **Altered Chords** (7b9, 7#9, 7#5, 7alt)
```
Problem: G7alt = [G, B, Db, Eb, F] (b9, #9, b5/#11, b13 tensions)
Reality: Multiple valid names, context-dependent
Result: Misidentified as diminished or half-diminished
```

❌ **Voicing Spread** (Wide intervals, omitted tones)
```
Problem: Bass plays C, right hand plays E-Bb-D (C9 no 5th no 3rd spread)
Reality: Notes span 2+ octaves, non-adjacent
Result: Detector treats as separate events or incomplete pattern
```

❌ **Rolled/Arpeggiated Chords**
```
Problem: Jazz comp: C → E → G → Bb (30ms apart)
Reality: Notes not simultaneous
Result: Only last note(s) captured in time window
```

❌ **Slash Chords & Polychords**
```
Problem: Dm7/G = [G, D, F, A, C] (G bass, Dm7 chord)
Reality: Could be G9sus, G11, Dm7/G, Csus/G
Result: Ambiguous, no clear "best" answer
```

### 3.2 Root Causes

#### Technical Limitations

1. **Exact Pattern Matching**
   - Current: Must match `core_intervals` + `optional_intervals`
   - Reality: Jazz voicings omit/substitute notes freely
   - Impact: No match found → defaults to "N.C." (No Chord)

2. **Single Time-Slice Detection**
   - Current: `chord_buffer_time = 0.015s` (15ms window)
   - Reality: Jazz voicings roll over 50-100ms
   - Impact: Captures partial chord only

3. **No Voice Separation**
   - Current: All notes treated equally
   - Reality: Bass note ≠ chord tones ≠ melody
   - Impact: Melody notes contaminate chord detection

4. **Stateless Recognition**
   - Current: Each moment analyzed independently
   - Reality: Chord meaning depends on context (ii-V-I, secondary dominants)
   - Impact: Misses harmonic function

5. **Binary Scoring**
   - Current: Either matches or doesn't (threshold = 0.6)
   - Reality: Multiple valid interpretations exist
   - Impact: Arbitrary selection, no candidate ranking

#### Musical Complexity

6. **Enharmonic Equivalence**
   - C7b9 = C-E-G-Bb-Db
   - Same pitch classes could be Dbmaj7#11
   
7. **Contextual Naming**
   - [G,B,D,F] in key of C = G7 (dominant)
   - Same notes in modal jazz = GMixolydian color
   
8. **Chord Substitutions**
   - Tritone sub: Db7 ⟷ G7
   - Same function, different roots
   
9. **Upper Structure Triads**
   - C7alt = B triad over C bass
   - Detector sees two separate chords

---

## 4. Existing Attempts at Solutions

### 4.1 `advanced_chord_analyzer.py` (Partial Implementation)

**What's Already Built:**
```python
class AdvancedChordAnalyzer:
    - VoiceContext (bass/chord/melody registers)
    - ChordCandidate (scored candidates)
    - Pattern weights (ML-inspired)
    - Jazz substitutions
    - Fuzzy matching logic
```

**Current Status:**
- ✅ Integrated into `ChordTheory` class
- ✅ Optional (fallback to basic recognition)
- ⚠️ **Not fully utilized** (voice separation incomplete)
- ⚠️ **Limited testing** on real jazz MIDI

**Limitations:**
- Voice separation not properly implemented
- Pattern matching still too rigid
- Context awareness minimal
- No time-window aggregation

### 4.2 `chord_definitions.json` Enhancement

**Current Structure:**
```json
{
  "chord_type": {
    "name": "Chord Name",
    "core_intervals": [0, 4, 7],
    "optional_intervals": [2, 9]
  }
}
```

**What's Good:**
- ✅ Core vs. optional distinction
- ✅ Supports extensions

**What's Missing:**
- ❌ No "required subset" (e.g., 7th chords need 3rd OR 7th)
- ❌ No voicing templates (drop-2, drop-3)
- ❌ No priority/weight per interval
- ❌ No jazz-specific definitions (7alt, 13#11, etc.)

---

## 5. Comparison with Existing Solutions

### 5.1 `jchord` Library

**Strengths:**
- ✅ Handles chord naming & progression
- ✅ Converts MIDI ↔ chord symbols
- ✅ Supports basic extensions

**Weaknesses:**
- ❌ Limited to standard chord vocabulary
- ❌ No real-time MIDI input
- ❌ Struggles with ambiguous voicings
- ❌ No voice separation

**Verdict**: Good for batch processing, not real-time jazz detection

### 5.2 `music21` Library

**Strengths:**
- ✅ **Comprehensive music theory** (MIT Music Lab)
- ✅ Chord identification: `chord.Chord(["C4","E4","G4"]).commonName`
- ✅ Inversion detection
- ✅ Roman numeral analysis
- ✅ Quality/interval analysis

**Weaknesses:**
- ❌ Heavy dependency (slow startup)
- ❌ Designed for score analysis, not real-time
- ❌ Still struggles with jazz extensions
- ❌ No MIDI input handling

**Verdict**: Excellent backend for chord naming logic, could augment our detector

### 5.3 Audio-Based Chord Recognition (ChordFormer, etc.)

**Research Findings:**
- Large-vocabulary chord recognition is **unsolved problem**
- State-of-the-art ML models: ~70% accuracy on jazz chords
- Better results on simple chords (~85-90%)

**Key Insight**: Even with ML, jazz chord recognition is hard!

---

## 6. Key Findings & Conclusions

### 6.1 Core Problem Statement

> **The current detector uses exact pattern matching on pitch-class sets, which works for simple chords but fails when:**
> 1. Notes are omitted (incomplete voicings)
> 2. Notes are added (tensions, non-chord tones)
> 3. Notes are spread across time/register (voicing/arpeggiation)
> 4. Multiple valid interpretations exist (ambiguity)
> 5. Context determines meaning (progressions)

### 6.2 Why This Is a Known Hard Problem

1. **Symbolic ambiguity**: Same notes = multiple valid chord names
2. **Voicing flexibility**: Jazz omits/reorders notes freely
3. **Temporal complexity**: Chords exist over time, not at instants
4. **Context dependency**: Meaning comes from progression, not isolated notes
5. **Domain knowledge required**: Jazz harmony is a complex language

### 6.3 What Success Looks Like

**Realistic Goals:**

✅ **Tier 1 (Achievable in 1-2 months)**
- Detect extended chords (9th, 11th, 13th) with omitted 5ths
- Handle basic altered dominants (7b9, 7#9, 7#5)
- Support slash chords (e.g., Dm7/G)
- Improve time-window tolerance (50-100ms)
- Rank multiple candidate chords

✅ **Tier 2 (Achievable in 3-4 months)**
- Voice separation (bass/chord/melody)
- Context-aware scoring (ii-V-I patterns)
- Jazz substitution awareness (tritone subs)
- User feedback/correction UI
- Test suite with real jazz MIDI files

✅ **Tier 3 (Advanced, 6+ months)**
- ML-based pattern recognition
- Automatic voicing learning
- Harmonic rhythm detection
- Key detection integration

**Unrealistic:**
- ❌ 100% accuracy on all jazz chords (even humans disagree!)
- ❌ Real-time detection of polychords/quartal harmony without context
- ❌ Automatic "correct" naming (subjectivity exists)

---

## 7. Recommended Approach

### 7.1 Philosophy

**Accept Ambiguity, Embrace Ranking**
- Don't force a single "correct" answer
- Provide **ranked candidates** with confidence scores
- Let user choose or override

**Fuzzy Matching, Not Exact**
- Allow partial matches (missing 5th, omitted root)
- Score based on "fit", not binary yes/no

**Context Over Isolation**
- Use progression history to disambiguate
- Prefer smooth voice leading

**User-Centric**
- Show why detector picked a chord
- Allow manual correction
- Learn from corrections

### 7.2 Next Steps (Immediate Actions)

1. **Complete existing `AdvancedChordAnalyzer`** (70% done)
2. **Extend time window** to 50-100ms
3. **Implement voice separation** (bass register detection)
4. **Add candidate ranking** (show top 3)
5. **Build test suite** with jazz MIDI files
6. **Integrate `music21`** for chord naming fallback

---

## 8. References & Resources

### Research Papers
- **ChordFormer** (2023): "Large-Vocabulary Chord Recognition" - arXiv
- **Automatic Chord Recognition** (Cho et al.): Surveys state-of-art methods
- **Jazz Harmony Analysis** (Rohrmeier): Context-dependent chord interpretation

### Libraries
- **music21**: https://web.mit.edu/music21/
- **jchord**: https://jonathangjertsen.github.io/jchord/
- **mido**: https://mido.readthedocs.io/
- **PrettyMIDI**: For time quantization

### Music Theory
- **Mark Levine**: "The Jazz Theory Book" (voicing conventions)
- **Berklee**: Chord scales, upper structures, alterations
- **Real Book**: Standard jazz progressions for testing

---

## Appendix: Concrete Examples

### Example 1: C13 Voicing

**Written Chord**: C13
**Full Definition**: C-E-G-Bb-D-F-A (7 notes)

**Reality (Jazz Piano Voicing)**:
```
Left hand:  E (10th), Bb (b7)
Right hand: D (9th), F (11th), A (13th)
MIDI notes: [40(E), 46(Bb), 62(D), 65(F), 69(A)]
Pitch classes: [4, 10, 2, 5, 9]
```

**Current Detector**: ❌ No match (root C not present!)
**Expected Output**: C13 (omit root, omit 5th)

---

### Example 2: G7alt → Cmaj7 (ii-V-I progression)

**Context**: Dm7 → G7alt → Cmaj7

**G7alt voicing**:
```
MIDI: [43(G), 54(F#/Gb), 59(B), 61(Db), 63(Eb)]
Pitch classes: [7, 6, 11, 1, 3]
```

**Current Detector**: ❌ Matches as "Gdim" or "Unknown"
**Expected**: G7alt (context: dominant resolving to C)

---

**Document Version**: 1.0  
**Last Updated**: December 5, 2025  
**Next Document**: `02-REQUIREMENTS.md`
