# Getting Started: Implementation Guide

## 🎯 You Are Here

You've reviewed the comprehensive analysis and are ready to start implementing. This guide will walk you through the first steps.

---

## 📚 What You Have

### Documentation (Complete ✅)
1. **01-PROBLEM-ANALYSIS.md** - Why current system fails
2. **02-REQUIREMENTS.md** - What to build
3. **03-TECHNICAL-DESIGN.md** - How to build it
4. **04-TASK-BREAKDOWN.md** - Step-by-step tasks (67 tasks)
5. **05-ROADMAP.md** - Timeline and big picture
6. **VISUAL-SUMMARY.md** - Quick visual reference
7. **README.md** - Documentation index

### Current Codebase (Partially Complete ⚡)
- ✅ Basic MIDI input handling
- ✅ Simple chord recognition
- ✅ PyQt6 UI
- ✅ ZMQ publishing
- 🟡 `AdvancedChordAnalyzer` (partially implemented)
- ❌ Time window buffer (not implemented)
- ❌ Voice separation (not implemented)
- ❌ Context tracking (not implemented)

---

## 🚀 Start Here: Phase 1, Sprint 1.1

### Week 1: Time Window Buffer

#### Day 1-2: Task MIDI-101 (6 hours)
**Create TimeWindowBuffer Class**

1. **Create new file**: `core/time_window_buffer.py`

2. **Implement the class**:
```python
import math
import threading
import time
from typing import Dict, List, Tuple

class TimeWindowBuffer:
    """
    Aggregates MIDI notes over a time window with exponential decay weighting.
    Handles rolled/arpeggiated chords.
    """
    
    def __init__(self, window_ms: float = 80, decay_ms: float = 100):
        """
        Args:
            window_ms: Time window in milliseconds to keep notes
            decay_ms: Decay constant for exponential weighting
        """
        self.window_ms = window_ms
        self.decay_ms = decay_ms
        self.note_events: List[Tuple[int, float, int]] = []
        self.lock = threading.Lock()
    
    def add_note(self, midi_note: int, timestamp: float, velocity: int):
        """Add a note event to the buffer"""
        with self.lock:
            self.note_events.append((midi_note, timestamp, velocity))
            self._cleanup_old_notes(timestamp)
    
    def remove_note(self, midi_note: int, timestamp: float):
        """Remove a note from the buffer"""
        with self.lock:
            self.note_events = [
                (n, t, v) for n, t, v in self.note_events 
                if n != midi_note
            ]
    
    def _cleanup_old_notes(self, current_time: float):
        """Remove notes older than window"""
        cutoff = current_time - (self.window_ms / 1000.0)
        self.note_events = [
            (n, t, v) for n, t, v in self.note_events 
            if t >= cutoff
        ]
    
    def get_weighted_notes(self, current_time: float) -> Dict[int, float]:
        """
        Get notes with time-decay weights
        
        Returns:
            Dict mapping MIDI note number to weight (0.0-1.0)
        """
        with self.lock:
            weighted = {}
            for midi_note, timestamp, velocity in self.note_events:
                age_ms = (current_time - timestamp) * 1000
                
                # Exponential decay
                time_weight = math.exp(-age_ms / self.decay_ms)
                
                # Velocity factor
                velocity_factor = velocity / 127.0
                
                final_weight = time_weight * velocity_factor
                
                # Keep highest weight if note appears multiple times
                weighted[midi_note] = max(
                    weighted.get(midi_note, 0), 
                    final_weight
                )
            
            return weighted
    
    def clear(self):
        """Clear all notes from buffer"""
        with self.lock:
            self.note_events.clear()
```

3. **Create unit tests**: `tests/test_time_window_buffer.py`

```python
import pytest
import time
from core.time_window_buffer import TimeWindowBuffer

def test_add_note():
    """Test adding notes to buffer"""
    buffer = TimeWindowBuffer(window_ms=100)
    buffer.add_note(60, 0.0, 100)
    
    weighted = buffer.get_weighted_notes(0.0)
    assert 60 in weighted
    assert weighted[60] > 0.9  # Should be close to 1.0

def test_time_decay():
    """Test exponential decay over time"""
    buffer = TimeWindowBuffer(window_ms=100, decay_ms=50)
    buffer.add_note(60, 0.0, 100)
    
    # Check weight decays over time
    weight_0ms = buffer.get_weighted_notes(0.0)[60]
    weight_50ms = buffer.get_weighted_notes(0.05)[60]
    weight_100ms = buffer.get_weighted_notes(0.1)[60]
    
    assert weight_0ms > weight_50ms > weight_100ms

def test_cleanup_old_notes():
    """Test old notes are removed"""
    buffer = TimeWindowBuffer(window_ms=100)
    buffer.add_note(60, 0.0, 100)
    
    # After window expires, note should be gone
    weighted = buffer.get_weighted_notes(0.15)  # 150ms later
    assert 60 not in weighted

def test_velocity_weighting():
    """Test velocity affects weight"""
    buffer = TimeWindowBuffer()
    buffer.add_note(60, 0.0, 127)  # Loud
    buffer.add_note(64, 0.0, 64)   # Medium
    
    weighted = buffer.get_weighted_notes(0.0)
    assert weighted[60] > weighted[64]

def test_remove_note():
    """Test removing notes"""
    buffer = TimeWindowBuffer()
    buffer.add_note(60, 0.0, 100)
    buffer.remove_note(60, 0.0)
    
    weighted = buffer.get_weighted_notes(0.0)
    assert 60 not in weighted

def test_multiple_same_pitch():
    """Test same pitch keeps max weight"""
    buffer = TimeWindowBuffer()
    buffer.add_note(60, 0.0, 80)
    buffer.add_note(60, 0.01, 100)  # Same note, louder
    
    weighted = buffer.get_weighted_notes(0.01)
    # Should keep the louder one's weight
    assert weighted[60] > 0.75
```

4. **Run tests**:
```powershell
pytest tests/test_time_window_buffer.py -v
```

---

#### Day 3: Task MIDI-102 (4 hours)
**Integrate TimeWindowBuffer into MIDIChordRecognizer**

1. **Open** `core/chord_recognition_engine.py`

2. **Import TimeWindowBuffer**:
```python
from core.time_window_buffer import TimeWindowBuffer
```

3. **Modify `__init__`**:
```python
def __init__(
    self,
    # ... existing params
    time_window_ms: float = 80,
    time_decay_ms: float = 100,
    # ... rest of params
):
    # ... existing code
    
    # NEW: Replace active_notes Set with TimeWindowBuffer
    self.time_buffer = TimeWindowBuffer(
        window_ms=time_window_ms,
        decay_ms=time_decay_ms
    )
    # Keep active_notes for backward compatibility (convert from buffer)
    self.active_notes: Set[int] = set()
```

4. **Modify `_process_midi_message`**:
```python
def _process_midi_message(self, msg: mido.Message) -> bool:
    changed = False
    current_time = time.time()
    
    if msg.type == "note_on" and msg.velocity > 0:
        # Add to time buffer
        self.time_buffer.add_note(msg.note, current_time, msg.velocity)
        
        # Update active_notes for compatibility
        if msg.note not in self.active_notes:
            self.active_notes.add(msg.note)
            changed = True
        
        # ... rest of existing code
    
    elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
        if not self.sustain_pedal_on:
            # Remove from time buffer
            self.time_buffer.remove_note(msg.note, current_time)
            
            # Update active_notes
            if msg.note in self.active_notes:
                self.active_notes.discard(msg.note)
                changed = True
        
        # ... rest of existing code
    
    return changed
```

5. **Modify `_update_chord_and_publish`**:
```python
def _update_chord_and_publish(self):
    current_time = time.time()
    
    # Get weighted notes from time buffer
    weighted_notes = self.time_buffer.get_weighted_notes(current_time)
    
    # Update active_notes for compatibility
    self.active_notes = set(weighted_notes.keys())
    
    # Pass weighted notes to chord recognition
    chord_info = self.chord_theory.recognize_chord(
        weighted_notes,  # Now Dict[int, float] instead of Set[int]
        self.min_notes
    )
    
    # ... rest of existing code
```

6. **Update `ChordTheory.recognize_chord` signature** in `core/music_theory.py`:
```python
def recognize_chord(
    self, 
    played_notes: Union[Set[int], Dict[int, float]],  # Accept both
    min_notes_for_chord: int
) -> Optional[Dict[str, Any]]:
    """
    Recognize chord from MIDI notes (with optional weights)
    
    Args:
        played_notes: Set of MIDI notes OR Dict of {midi_note: weight}
        min_notes_for_chord: Minimum notes required
    """
    # Convert to Set if Dict (for backward compatibility)
    if isinstance(played_notes, dict):
        played_midi_notes = set(played_notes.keys())
        note_weights = played_notes
    else:
        played_midi_notes = played_notes
        note_weights = {n: 1.0 for n in played_notes}
    
    # ... rest of existing code uses played_midi_notes
```

7. **Test integration**:
```powershell
# Run existing tests (should still pass)
pytest tests/test_chord_recognition.py -v

# Manual test: play rolled chord, verify detected
python midi_chord_app.py
```

---

#### Day 4: Task MIDI-103 (2 hours)
**Add Configuration Options**

1. **Update** `chord_recognition_engine.py` `__init__` to accept config:
```python
def __init__(
    self,
    # ... existing params
    time_window_ms: float = 80,
    time_decay_ms: float = 100,
    # ...
):
    # Store config
    self.time_window_ms = time_window_ms
    self.time_decay_ms = time_decay_ms
```

2. **Create** `config.yaml` (if not exists):
```yaml
detection:
  time_window:
    enabled: true
    window_ms: 80
    decay_ms: 100
```

3. **Load config** in `midi_chord_app.py`:
```python
import yaml

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Pass to recognizer
recognizer = MIDIChordRecognizer(
    time_window_ms=config['detection']['time_window']['window_ms'],
    time_decay_ms=config['detection']['time_window']['decay_ms'],
    # ... other params
)
```

4. **Update README.md** with configuration example

---

## 📊 Progress Tracking

### Week 1 Checklist
- [ ] Day 1-2: TimeWindowBuffer class implemented
- [ ] Day 1-2: Unit tests pass (8+ tests)
- [ ] Day 3: Integration complete
- [ ] Day 3: Existing tests still pass
- [ ] Day 4: Configuration added
- [ ] Day 4: README updated
- [ ] Manual test: Rolled chords detected

### Success Criteria
- ✅ Can detect C-E-G played 40ms apart (rolled)
- ✅ Unit tests >90% coverage for TimeWindowBuffer
- ✅ No performance regression (<10ms latency)
- ✅ Existing functionality still works

---

## 🔄 Next Steps After Week 1

### Week 2: Fuzzy Matching
- Task MIDI-105: Create FuzzyChordMatcher
- Task MIDI-106: Integrate into ChordTheory
- Task MIDI-107: Update chord definitions
- Task MIDI-108: Unit tests

### Week 3: Enhanced Chord Definitions
- Task MIDI-109: Add 20+ jazz chord types
- Task MIDI-110: Chord definition validator
- Task MIDI-111: Documentation
- Task MIDI-112: Tests for each chord type

### Week 4: Integration & Testing
- Task MIDI-113: MIDI file integration tests
- Task MIDI-114: Performance benchmarks
- Task MIDI-115: Documentation updates
- Task MIDI-116: Bug fixes

---

## 🆘 Troubleshooting

### Issue: Tests fail after integration
**Solution**: Check that existing code handles both `Set[int]` and `Dict[int, float]`

### Issue: Performance degrades
**Solution**: Profile with cProfile, optimize `_cleanup_old_notes()`

### Issue: Notes not detected in time window
**Solution**: Verify timestamps are correct, check window_ms value

---

## 📞 Getting Help

- **Documentation**: Review `03-TECHNICAL-DESIGN.md` Section 2.1
- **Example Code**: See technical design for full implementation
- **Questions**: Open GitHub Issue with `[question]` tag
- **Bugs**: Open GitHub Issue with `[bug]` tag, include MIDI example

---

## ✅ Before You Start

- [ ] Read all documentation (6-8 hours)
- [ ] Understand the problem (why exact matching fails)
- [ ] Set up dev environment (Python 3.9+, dependencies)
- [ ] Run existing tests (verify baseline)
- [ ] Create feature branch: `git checkout -b feature/phase-1-time-window`
- [ ] Create task tracking board (GitHub Projects)

---

## 🎯 Your Mission

**Goal**: By end of Week 1, the chord detector should handle rolled chords (notes within 80ms) as a single chord.

**Test Case**: 
```python
# Play C major arpeggio: C (0ms), E (+40ms), G (+80ms)
# Expected: Detect "C major" chord
# Before: Only detects last note(s)
# After: Aggregates all 3 notes → "C major"
```

---

**Ready? Let's begin! 🚀**

Start with: `core/time_window_buffer.py`

Good luck! 🎵
