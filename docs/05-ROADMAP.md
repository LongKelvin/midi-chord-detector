# MIDI Chord Detector: Project Roadmap & Summary

## Executive Summary

This document provides a high-level roadmap for enhancing the MIDI Chord Detector to support jazz and complex chord detection. The project is divided into 3 phases over 4-5 months.

**Current State**: Basic chord detection works for simple chords (triads, basic 7ths)  
**Goal**: Robust jazz chord detection with context awareness and user-friendly UI  
**Timeline**: 16-20 weeks (4-5 months)  
**Estimated Effort**: 320-380 hours

---

## Problem Statement

The current MIDI chord detector uses **exact pattern matching** which works well for simple chords but fails for:

1. **Jazz voicings** with omitted notes (no 5th, no root)
2. **Extended chords** (9th, 11th, 13th) with complex intervals
3. **Altered dominants** (7b9, 7#9, 7alt) 
4. **Rolled/arpeggiated chords** where notes aren't simultaneous
5. **Slash chords** where bass ≠ root
6. **Context-dependent** chord meanings (ii-V-I progressions)

**Root Cause**: Rigid pattern matching + single time-slice detection + no voice separation + no context awareness

---

## Solution Approach

### Core Strategy: From Exact to Fuzzy, From Isolated to Contextual

```
Current:                          Enhanced:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Exact pattern matching       →    Fuzzy matching with weights
Single time instant          →    Time window aggregation
All notes equal              →    Voice separation (bass/chord/melody)
Single best match            →    Ranked candidates
No context                   →    Progression-aware scoring
Binary yes/no                →    Confidence scores (0-100%)
```

---

## 3-Phase Development Plan

### 📊 Phase 1: Fuzzy Matching & Time Window (Month 1)
**Goal**: Handle omitted notes and rolled chords

**Key Features**:
- ✅ Time window buffer (50-150ms) for note aggregation
- ✅ Fuzzy chord matching with interval importance weights
- ✅ Support for omitted 5ths, roots in jazz voicings
- ✅ Enhanced chord definitions (20+ jazz chord types)

**Deliverables**:
- `TimeWindowBuffer` class
- `FuzzyChordMatcher` class
- Extended `chord_definitions.json`
- 200+ unit tests

**Success Metrics**:
- Detect chords with omitted 5th (90%+ accuracy)
- Handle rolled chords within 100ms
- >85% accuracy on pop progressions

---

### 📊 Phase 2: Voice Separation & Candidate Ranking (Months 2-3)
**Goal**: Handle slash chords and provide multiple interpretations

**Key Features**:
- ✅ Voice separation by register (bass/chord/melody)
- ✅ Slash chord detection (e.g., Dm7/G)
- ✅ Multi-candidate generation (top 3-5 options)
- ✅ Comprehensive scoring (interval + voicing + context + frequency + bass)
- ✅ Enhanced UI showing candidates and explanations

**Deliverables**:
- `VoiceSeparator` class
- `CandidateGenerator` class
- `ChordCandidate` dataclass
- Multi-candidate UI display
- Voice-colored piano keyboard

**Success Metrics**:
- Detect slash chords (90%+ accuracy)
- Top-3 candidates include correct answer (90%+)
- >75% accuracy on extended chords (9th, 11th, 13th)

---

### 📊 Phase 3: Context Awareness (Months 3-4)
**Goal**: Use harmonic context to improve accuracy

**Key Features**:
- ✅ Chord history tracking (last 10 chords)
- ✅ Key detection (Krumhansl-Schmuckler algorithm)
- ✅ Progression pattern recognition (ii-V-I, V-I, etc.)
- ✅ Context-based scoring adjustments
- ✅ Manual chord correction UI
- ✅ User-defined chord definitions

**Deliverables**:
- `ChordContext` class
- Progression pattern matcher
- Key detection algorithm
- Chord correction UI
- User chord definition editor

**Success Metrics**:
- >70% accuracy on altered chords
- Context improves accuracy by 10-15%
- Key detection confidence >70% after 8 chords

---

## Visual Roadmap

```
Week 1-4: PHASE 1 - Fuzzy Matching & Time Window
┣━ Sprint 1.1: Time Window Buffer
┣━ Sprint 1.2: Fuzzy Matching
┣━ Sprint 1.3: Enhanced Chord Definitions
┗━ Sprint 1.4: Integration & Testing

Week 5-12: PHASE 2 - Voice Separation & Ranking
┣━ Sprint 2.1: Voice Separation (2 weeks)
┣━ Sprint 2.2: Candidate Generation (2 weeks)
┣━ Sprint 2.3: UI Enhancements (2 weeks)
┗━ Sprint 2.4: Testing & Refinement (2 weeks)

Week 13-20: PHASE 3 - Context Awareness
┣━ Sprint 3.1: Context Tracking (2 weeks)
┣━ Sprint 3.2: Progression Recognition (2 weeks)
┣━ Sprint 3.3: User Features (2 weeks)
┗━ Sprint 3.4: Final Testing & Release (2 weeks)
```

---

## Gantt Chart (Text Format)

```
Task                          | W1 W2 W3 W4 W5 W6 W7 W8 W9 W10 W11 W12 W13 W14 W15 W16 W17 W18 W19 W20
------------------------------|━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Time Window Buffer            |██ 
Fuzzy Matching                |   ██ 
Enhanced Chord Definitions    |      ██ 
Integration & Testing         |         ██ 
Voice Separation              |            ████ 
Candidate Generation          |                ████ 
UI Enhancements               |                    ████ 
Testing & Refinement          |                        ████ 
Context Tracking              |                            ████ 
Progression Recognition       |                                ████ 
User Features                 |                                    ████ 
Final Testing & Release       |                                        ████ 
```

---

## Key Milestones

| Milestone | Week | Description | Success Criteria |
|-----------|------|-------------|------------------|
| **M1: Fuzzy Matching Complete** | 4 | Omitted notes and time window working | >85% accuracy on simple chords with omissions |
| **M2: Voice Separation Complete** | 8 | Slash chords and multi-candidate | >90% slash chord detection |
| **M3: Candidate Ranking Complete** | 12 | Top-3 candidates with UI | Top-3 includes correct answer 90%+ |
| **M4: Context Awareness Complete** | 16 | Progression-aware detection | Context improves accuracy by 10-15% |
| **M5: Release v2.0** | 20 | All features complete, tested, documented | All acceptance criteria met |

---

## Technology Stack

### Core Technologies
- **Python 3.9-3.11**: Main language
- **mido**: MIDI input/output
- **PyQt6**: User interface
- **ZMQ**: Real-time message publishing
- **numpy**: Efficient calculations (Phase 2+)

### Optional Libraries
- **music21**: Chord naming fallback (Phase 3+)
- **scikit-learn**: Pattern recognition (Future)

### Development Tools
- **pytest**: Unit testing
- **cProfile**: Performance profiling
- **Git**: Version control
- **GitHub Actions**: CI/CD (optional)

---

## Architecture Changes

### Before (Current):
```
MIDI Input → Active Notes Set → Pattern Matching → Single Chord
```

### After (Phase 3):
```
MIDI Input
    ↓
Time Window Buffer (50-150ms aggregation)
    ↓
Voice Separator (bass/chord/melody)
    ↓
Candidate Generator
    ├─ Fuzzy Matcher (interval weighting)
    ├─ Context Analyzer (progression patterns)
    └─ Voicing Scorer (spacing, range)
    ↓
Ranked Candidates (top 3-5)
    ↓
Output (UI + ZMQ)
```

---

## Expected Outcomes

### Quantitative Improvements

| Metric | Before | After Phase 1 | After Phase 2 | After Phase 3 |
|--------|--------|---------------|---------------|---------------|
| **Simple chords** (triads, 7ths) | 90% | 95% | 95% | 95% |
| **Extended chords** (9/11/13) | 40% | 65% | 80% | 85% |
| **Altered chords** (7b9, 7alt) | 20% | 45% | 65% | 75% |
| **Slash chords** | 30% | 50% | 90% | 92% |
| **Jazz voicings** (rootless) | 15% | 50% | 75% | 80% |
| **Top-3 accuracy** | N/A | 80% | 90% | 93% |

### Qualitative Improvements

**Phase 1**:
- ✅ Detects chords with omitted 5ths
- ✅ Handles rolled chords (piano/guitar style)
- ✅ Supports 20+ new jazz chord types

**Phase 2**:
- ✅ Shows multiple possible chord names
- ✅ Explains why each chord was detected
- ✅ Properly handles bass notes (slash chords)
- ✅ Visual feedback (voice-colored keyboard)

**Phase 3**:
- ✅ Understands chord progressions (ii-V-I)
- ✅ Detects musical key
- ✅ Learns from user corrections
- ✅ Fully customizable chord definitions

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance degradation (latency >10ms) | Medium | High | Benchmark early, optimize hot paths |
| Candidate generation too slow | Medium | Medium | Cache definitions, limit search space |
| UI complexity | Low | Medium | Iterative design, user testing |
| Context logic too aggressive | Medium | Low | Make context-aware mode toggleable |

### Schedule Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scope creep | Medium | High | Stick to 3-phase plan, defer extras |
| Testing takes longer | Medium | Medium | Start testing early, parallel with dev |
| Integration issues | Low | High | Incremental integration, automated tests |

---

## Success Criteria

### Must-Have (Critical)
- ✅ Detect extended chords (9/11/13) with 75%+ accuracy
- ✅ Handle omitted notes (no 5th, no root)
- ✅ Detect slash chords (bass ≠ root)
- ✅ Show multiple candidate chords
- ✅ Real-time performance (<10ms latency)

### Should-Have (High Priority)
- ✅ Context-aware detection (progression patterns)
- ✅ Key detection
- ✅ Voice separation (bass/chord/melody)
- ✅ Manual correction UI

### Nice-to-Have (Medium Priority)
- ✅ User-defined chord definitions
- ✅ Explanation panel (why detected)
- ✅ Voice-colored keyboard
- ✅ Import/export custom definitions

---

## Resource Requirements

### Development Team
- **1-2 developers** (Python, music theory knowledge helpful)
- **1 tester** (optional, can be developer)
- **1 musician** for testing/feedback (optional)

### Hardware
- **MIDI keyboard/controller** for testing
- **Modern PC** (8GB+ RAM, multi-core CPU)

### Time Commitment
- **Full-time** (40 hrs/week): 8-10 weeks
- **Part-time** (20 hrs/week): 16-20 weeks
- **Hobby** (10 hrs/week): 32-40 weeks

---

## Post-Release Plans (Future)

### Phase 4: Machine Learning (Optional, 6+ months)
- Train classifier on labeled jazz MIDI data
- Features: pitch classes, voicing, context
- Integrate as additional candidate generator
- Requires large annotated dataset

### Phase 5: Advanced Features (Future)
- Multi-track MIDI support (bass + chords separately)
- Harmonic rhythm visualization
- Real-time key modulation detection
- Quartal/quintal harmony support
- DAW plugin integration (VST/AU)

---

## How to Use This Roadmap

### For Project Managers:
1. Review milestones and timeline
2. Assign tasks to developers (see `04-TASK-BREAKDOWN.md`)
3. Track progress weekly
4. Adjust schedule as needed

### For Developers:
1. Read `01-PROBLEM-ANALYSIS.md` to understand the problem
2. Read `02-REQUIREMENTS.md` for detailed requirements
3. Read `03-TECHNICAL-DESIGN.md` for implementation details
4. Follow `04-TASK-BREAKDOWN.md` for step-by-step tasks
5. Start with Phase 1, Sprint 1.1

### For Testers:
1. Set up test environment (MIDI keyboard + software)
2. Review acceptance criteria in `02-REQUIREMENTS.md`
3. Create test cases based on `04-TASK-BREAKDOWN.md`
4. Report bugs with MIDI file examples

### For Musicians/Users:
1. Test pre-release builds
2. Provide feedback on accuracy and UI
3. Report chords that are mis-detected
4. Suggest improvements

---

## Communication Plan

### Weekly Sync (1 hour)
- Progress update
- Blockers/issues
- Next week's plan

### Sprint Reviews (2 hours, every 2 weeks)
- Demo new features
- Review test results
- Adjust priorities

### Release Retrospective (2 hours, after each phase)
- What went well
- What could improve
- Lessons learned

---

## Documentation Status

| Document | Status | Purpose |
|----------|--------|---------|
| `01-PROBLEM-ANALYSIS.md` | ✅ Complete | Explains the problem and why current system fails |
| `02-REQUIREMENTS.md` | ✅ Complete | Detailed functional and non-functional requirements |
| `03-TECHNICAL-DESIGN.md` | ✅ Complete | Architecture, algorithms, implementation details |
| `04-TASK-BREAKDOWN.md` | ✅ Complete | Actionable tasks (67 tasks) for all 3 phases |
| `05-ROADMAP.md` (this doc) | ✅ Complete | High-level roadmap and summary |

---

## Getting Started

### Step 1: Review Documentation
```bash
cd docs/
# Read in order:
1. 01-PROBLEM-ANALYSIS.md
2. 02-REQUIREMENTS.md
3. 03-TECHNICAL-DESIGN.md
4. 04-TASK-BREAKDOWN.md
5. 05-ROADMAP.md (this file)
```

### Step 2: Set Up Development Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Run existing tests (should pass)
pytest tests/

# Start existing app (verify baseline)
python midi_chord_app.py
```

### Step 3: Start Phase 1, Sprint 1.1
```bash
# Create branch
git checkout -b feature/time-window-buffer

# Start with Task MIDI-101
# See 04-TASK-BREAKDOWN.md for details
```

### Step 4: Track Progress
- Use GitHub Issues or project management tool
- Mark tasks as Complete/In Progress/Blocked
- Update this roadmap as needed

---

## Contact & Support

**Project Lead**: [Your Name]  
**Repository**: https://github.com/LongKelvin/midi-chord-detector  
**Branch**: `feature/advanced-chord-detection`

**Questions?** Open a GitHub Issue or discussion

---

## Conclusion

This roadmap provides a clear, actionable path to enhance the MIDI Chord Detector from basic pattern matching to intelligent, context-aware jazz chord recognition. The 3-phase approach balances:

- **Quick wins** (Phase 1: fuzzy matching)
- **User value** (Phase 2: multi-candidate UI)
- **Intelligence** (Phase 3: context awareness)

By the end of Phase 3 (20 weeks), you'll have a robust chord detector that rivals commercial solutions for MIDI chord recognition.

**Let's build something great! 🎵🎹**

---

**Document Version**: 1.0  
**Last Updated**: December 5, 2025  
**Status**: Ready for Implementation
