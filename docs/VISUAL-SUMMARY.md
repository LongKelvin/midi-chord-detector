# MIDI Chord Detector Enhancement: Visual Summary

## 🎯 The Big Picture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CURRENT PROBLEM                                      │
│                                                                               │
│  ❌ Exact pattern matching only                                             │
│  ❌ Fails on jazz voicings (omitted notes)                                  │
│  ❌ Can't handle rolled/arpeggiated chords                                  │
│  ❌ No voice separation (bass/chord/melody)                                 │
│  ❌ Single answer, no alternatives                                          │
│  ❌ No context awareness                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
                           🔧 3-PHASE SOLUTION
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENHANCED SYSTEM                                      │
│                                                                               │
│  ✅ Fuzzy matching with interval weights                                    │
│  ✅ Handles omitted notes (no 5th, no root)                                │
│  ✅ Time window aggregation (50-150ms)                                     │
│  ✅ Voice separation (bass/chord/melody)                                   │
│  ✅ Multiple ranked candidates (top 3-5)                                   │
│  ✅ Context-aware (progression patterns)                                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Accuracy Improvement Trajectory

```
Accuracy
   %
  100┤
     │
   95┤                                        ┌────── Simple Chords (Triads, 7ths)
     │                           ┌───────────┤
   90┤                    ┌──────┤           │
     │                    │      │           │
   85┤             ┌──────┤      │           │
     │             │      │      │           │
   80┤      ┌──────┤      │      └───────────┐ Extended (9/11/13)
     │      │      │      │                  │
   75┤      │      │      └──────────────────┤
     │      │      │                         │
   70┤      │      └─────────────────────────┐ Altered (7b9, 7alt)
     │      │                                │
   65┤      │                                │
     │      │                                │
   60┤──────┤                                │
     │      │                                │
   55┤      │                                │
     └──────┴────────────────────────────────┴──────────────────────────
          Current  Phase 1    Phase 2    Phase 3
                  (Month 1)  (Month 3)  (Month 5)
```

---

## 🏗️ Architecture Evolution

### BEFORE: Simple Pattern Matching
```
┌──────────────┐
│ MIDI Input   │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────┐
│ Active Notes (Set[int])      │
│ {60, 64, 67}                 │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────────────────────┐
│ Exact Pattern Match          │
│ [0,4,7] = Major?             │
│ YES → Return "Cmaj"          │
│ NO  → Return "N.C."          │
└──────┬───────────────────────┘
       │
       ▼
┌──────────────┐
│ Single Chord │
└──────────────┘
```

### AFTER: Intelligent Recognition
```
┌──────────────┐
│ MIDI Input   │
└──────┬───────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Time Window Buffer (80ms)              │
│ Notes with decay weights               │
│ {60: 1.0, 64: 0.9, 67: 0.8}           │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Voice Separator                        │
│ Bass: [60]                             │
│ Chord: [64, 67, 71]                    │
│ Melody: [84]                           │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Candidate Generator                    │
│ Try all 12 roots × all chord types    │
│                                        │
│ ┌────────────────────────────────┐    │
│ │ Fuzzy Matcher                  │    │
│ │ - Interval weights             │    │
│ │ - Omitted note tolerance       │    │
│ └────────────────────────────────┘    │
│                                        │
│ ┌────────────────────────────────┐    │
│ │ Context Analyzer               │    │
│ │ - Chord history                │    │
│ │ - Progression patterns         │    │
│ │ - Key detection                │    │
│ └────────────────────────────────┘    │
│                                        │
│ ┌────────────────────────────────┐    │
│ │ Scorer                         │    │
│ │ - Interval: 0.85               │    │
│ │ - Voicing: 0.90                │    │
│ │ - Context: 0.70                │    │
│ │ - Frequency: 0.80              │    │
│ │ - Bass: 0.95                   │    │
│ │ Total: 0.84                    │    │
│ └────────────────────────────────┘    │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│ Ranked Candidates                      │
│ 1. Cmaj7/E    [92%] ★                 │
│ 2. C6/9       [85%]                   │
│ 3. Am7/C      [78%]                   │
└──────┬─────────────────────────────────┘
       │
       ▼
┌────────────────┐
│ UI + ZMQ       │
└────────────────┘
```

---

## 🗓️ Timeline Visualization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        20-WEEK TIMELINE                                  │
└─────────────────────────────────────────────────────────────────────────┘

Month 1          Month 2          Month 3          Month 4          Month 5
├────────────────┼────────────────┼────────────────┼────────────────┼────┤
│   PHASE 1      │       PHASE 2                   │    PHASE 3            │
│ Fuzzy Match    │ Voice Separation & Ranking      │ Context Awareness     │
├────────────────┼────────────────┼────────────────┼────────────────┼────┤
│                │                │                │                │    │
│ Week 1-4       │ Week 5-8       │ Week 9-12      │ Week 13-16     │W17-20
│                │                │                │                │    │
│ ┌────────────┐ │ ┌────────────┐ │ ┌────────────┐ │ ┌────────────┐ │┌──┐│
│ │Time Window │ │ │   Voice    │ │ │ Candidate  │ │ │  Context   │ ││Fi││
│ │   Buffer   │ │ │ Separation │ │ │Generation  │ │ │  Tracking  │ ││na││
│ └────────────┘ │ └────────────┘ │ └────────────┘ │ └────────────┘ ││l ││
│ ┌────────────┐ │ ┌────────────┐ │ ┌────────────┐ │ ┌────────────┐ ││  ││
│ │   Fuzzy    │ │ │ Multi-     │ │ │   UI       │ │ │Progression │ ││Te││
│ │  Matching  │ │ │ Candidate  │ │ │Enhancements│ │ │  Patterns  │ ││st││
│ └────────────┘ │ └────────────┘ │ └────────────┘ │ └────────────┘ ││in││
│ ┌────────────┐ │ ┌────────────┐ │ ┌────────────┐ │ ┌────────────┐ ││g ││
│ │  Enhanced  │ │ │   Slash    │ │ │   Voice    │ │ │   Manual   │ ││& ││
│ │ Chord Defs │ │ │   Chords   │ │ │  Colored   │ │ │Corrections │ ││  ││
│ └────────────┘ │ └────────────┘ │ └────────────┘ │ └────────────┘ ││Re││
│                │                │                │                │││le││
│                │                │                │                │││as││
│                │                │                │                │││e ││
└────────────────┴────────────────┴────────────────┴────────────────┴┴──┴┘

Milestone:     M1: Fuzzy      M2: Voice      M3: Ranking    M4: Context  M5:
               Complete       Complete       Complete       Complete     v2.0
```

---

## 🎯 Feature Comparison Matrix

```
Feature                      │ Current │ Phase 1 │ Phase 2 │ Phase 3
─────────────────────────────┼─────────┼─────────┼─────────┼─────────
Exact Pattern Match          │    ✅   │    ✅   │    ✅   │    ✅
Fuzzy Pattern Match          │    ❌   │    ✅   │    ✅   │    ✅
Time Window (Rolled Chords)  │    ❌   │    ✅   │    ✅   │    ✅
Omitted Notes (no 5th)       │    ❌   │    ✅   │    ✅   │    ✅
Omitted Root (rootless)      │    ❌   │    🟡   │    ✅   │    ✅
Extended Chords (9/11/13)    │    🟡   │    ✅   │    ✅   │    ✅
Altered Chords (7b9, 7alt)   │    ❌   │    🟡   │    ✅   │    ✅
Voice Separation             │    ❌   │    ❌   │    ✅   │    ✅
Slash Chords (C/E)           │    🟡   │    🟡   │    ✅   │    ✅
Multiple Candidates          │    ❌   │    ❌   │    ✅   │    ✅
Explanation Panel            │    ❌   │    ❌   │    ✅   │    ✅
Context Awareness            │    ❌   │    ❌   │    ❌   │    ✅
Progression Detection        │    ❌   │    ❌   │    ❌   │    ✅
Key Detection                │    ❌   │    ❌   │    ❌   │    ✅
Manual Correction            │    ❌   │    ❌   │    ❌   │    ✅
User Chord Definitions       │    ❌   │    ❌   │    ❌   │    ✅

Legend: ✅ Full Support  🟡 Partial Support  ❌ No Support
```

---

## 💡 Core Algorithms at a Glance

### 1. Time Window Aggregation
```python
# Collect notes over 80ms window with decay
weight = e^(-time_since_onset / decay_constant) * (velocity / 127)

Result: {60: 1.0, 64: 0.9, 67: 0.8}  # MIDI note → weight
```

### 2. Voice Separation
```python
# Separate by register
bass   = lowest note in range [21-60]
chord  = notes in range [36-84], exclude bass
melody = highest note if gap >12 semitones

Result: {bass: [48], chord: [60,64,67], melody: [84]}
```

### 3. Fuzzy Matching
```python
# Score with interval importance weights
score = (matched_core_weight / total_core_weight) 
        + optional_bonus 
        - missing_penalty 
        - extra_penalty

Result: 0.87  # Score 0.0-1.0
```

### 4. Candidate Ranking
```python
# Try all roots & types, score each
total_score = (interval * 0.40) 
            + (voicing * 0.20) 
            + (context * 0.20) 
            + (frequency * 0.10) 
            + (bass_match * 0.10)

Result: [Cmaj7/E (0.92), C6/9 (0.85), Am7/C (0.78)]
```

### 5. Context Analysis
```python
# Track history, detect progressions
if previous == Dm7 and current_candidates_include(G7):
    boost(G7, +0.2)  # ii-V pattern

if previous == G7 and current_candidates_include(Cmaj):
    boost(Cmaj, +0.2)  # V-I pattern

Result: Context-adjusted scores
```

---

## 📈 Expected Impact

```
                    BEFORE              AFTER
                    ───────             ──────
Accuracy
  Simple:            90%        →        95%     (+5%)
  Extended:          40%        →        85%     (+45%)
  Altered:           20%        →        75%     (+55%)
  Jazz Voicings:     15%        →        80%     (+65%)

User Experience
  Single Answer      ✅         →        ❌
  Multiple Options   ❌         →        ✅      (Top 3-5)
  Explanations       ❌         →        ✅      (Why detected)
  Context Aware      ❌         →        ✅      (ii-V-I)
  Manual Override    ❌         →        ✅      (User correction)

Performance
  Latency:           ~3ms       →        <10ms   (Still real-time)
  CPU:               ~5%        →        <10%    (Single core)
  Memory:            ~30MB      →        <100MB
```

---

## 🎹 Example Transformations

### Example 1: C13 Voicing (Jazz Piano)
```
Input MIDI Notes: [40(E), 46(Bb), 62(D), 65(F), 69(A)]
Pitch Classes: [4, 10, 2, 5, 9]

┌─────────────────────────────────────────────────────────────┐
│ CURRENT SYSTEM                                               │
│ ❌ No match found (root C not present)                      │
│ → Returns "N.C." (No Chord)                                 │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ ENHANCED SYSTEM (Phase 3)                                    │
│ ✅ Detected as C13 (omit root, omit 5th)                   │
│                                                              │
│ Candidates:                                                  │
│ 1. ★ C13       [89%]  Root: C, Bass: E                     │
│    Intervals: m3(E), b7(Bb), 9(D), 11(F), 13(A)            │
│    Missing: root(C), 5th(G)                                 │
│    Reason: Strong match; typical jazz voicing               │
│                                                              │
│ 2.   Em7b5     [72%]  Root: E, Bass: E                     │
│    Reason: Good match; less common in context               │
│                                                              │
│ 3.   Bb13      [68%]  Root: Bb, Bass: E                    │
│    Reason: Possible; unusual bass note                      │
└─────────────────────────────────────────────────────────────┘
```

### Example 2: ii-V-I Progression
```
Sequence: Dm7 → ? → Cmaj7

Current chord notes: [55(G), 59(B), 62(D), 65(F)]
Pitch Classes: [7, 11, 2, 5]

┌─────────────────────────────────────────────────────────────┐
│ CURRENT SYSTEM (No Context)                                  │
│ ❌ Ambiguous: could be G7, G9, Bdim7, etc.                  │
│ → Returns "G7" (arbitrary choice)                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ ENHANCED SYSTEM (Phase 3)                                    │
│ ✅ Context-aware detection                                  │
│                                                              │
│ Context: Previous chord was Dm7                              │
│ Pattern: Likely ii-V progression                             │
│                                                              │
│ Candidates (with context boost):                             │
│ 1. ★ G9        [94%]  (+0.2 context boost)                 │
│    Root: G, Bass: G                                         │
│    Reason: Strong ii-V pattern; resolves to Cmaj7           │
│                                                              │
│ 2.   G7        [88%]  (+0.2 context boost)                 │
│    Reason: Also fits ii-V pattern                           │
│                                                              │
│ 3.   Bdim7     [65%]  (no context boost)                   │
│    Reason: Less likely in ii-V-I progression                │
│                                                              │
│ Detected Key: C major (confidence: 85%)                      │
│ Progression: ii-V-I (Dm7 → G9 → Cmaj7 expected)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started: First 3 Tasks

### Task 1: Create TimeWindowBuffer Class (6 hours)
```python
# File: core/time_window_buffer.py
class TimeWindowBuffer:
    def __init__(self, window_ms=80, decay_ms=100):
        self.window_ms = window_ms
        self.decay_ms = decay_ms
        self.note_events = []  # (midi_note, timestamp, velocity)
    
    def add_note(self, midi_note, timestamp, velocity):
        self.note_events.append((midi_note, timestamp, velocity))
        self._cleanup_old_notes(timestamp)
    
    def get_weighted_notes(self, current_time):
        weighted = {}
        for note, ts, vel in self.note_events:
            age_ms = (current_time - ts) * 1000
            weight = math.exp(-age_ms / self.decay_ms) * (vel / 127)
            weighted[note] = max(weighted.get(note, 0), weight)
        return weighted
```

### Task 2: Create FuzzyChordMatcher Class (8 hours)
```python
# File: core/fuzzy_chord_matcher.py
class FuzzyChordMatcher:
    WEIGHTS = {
        0: 0.8, 3: 1.0, 4: 1.0, 7: 0.5, 10: 1.0, 11: 1.0, ...
    }
    
    @classmethod
    def calculate_score(cls, played_pcs, chord_def):
        required = chord_def.get('required_intervals', [])
        if required and not all(i in played_pcs for i in required):
            return 0.0, {'reason': 'Missing required'}
        
        # Calculate weighted score
        # ... (implementation from technical design)
        
        return final_score, details
```

### Task 3: Add Enhanced Chord Definitions (6 hours)
```json
// File: data/chord_definitions.json
{
  "7b9": {
    "name": "Dominant 7th Flat 9",
    "required_intervals": [4, 10],
    "core_intervals": [0, 4, 7, 10],
    "optional_intervals": [7],
    "alterations": [1]
  },
  "7alt": {
    "name": "Dominant 7th Altered",
    "required_intervals": [4, 10],
    "core_intervals": [0, 4, 10],
    "optional_intervals": [1, 3, 6, 8]
  }
  // ... +20 more chord types
}
```

---

## 📞 Support & Resources

- **Documentation**: `/docs/` (5 comprehensive documents)
- **Repository**: https://github.com/LongKelvin/midi-chord-detector
- **Branch**: `feature/advanced-chord-detection`
- **Issues**: GitHub Issues with tag `[enhancement]`

---

## ✅ Success Checklist

- [ ] Read all 5 documentation files
- [ ] Understand the problem (why exact matching fails)
- [ ] Review the 3-phase plan
- [ ] Set up development environment
- [ ] Create project tracking board
- [ ] Start Phase 1, Task MIDI-101

---

**Status**: 📘 Documentation Complete → 🚀 Ready for Implementation

**Let's transform this chord detector! 🎵**
