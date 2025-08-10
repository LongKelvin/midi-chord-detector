#!/usr/bin/env python3
"""
Debug C9 chord recognition issue
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.music_theory import ChordTheory

def debug_c9_chord():
    """Debug the C9 chord recognition specifically"""
    print("Debugging C9 Chord Recognition")
    print("=" * 50)
    
    # Initialize chord recognition
    chord_theory = ChordTheory(genre='jazz')
    
    # Test the problematic chord: C9 without 5th
    # Notes: C (60), E (64), Bb (70), D (74) = C, E, Bb, D
    test_notes = {60, 64, 70, 74}
    
    print(f"Test notes: {sorted(test_notes)}")
    print(f"Note names: C(60), E(64), Bb(70), D(74)")
    print(f"Expected: C9 (C dominant 9th without 5th)")
    print()
    
    # Test with advanced analyzer
    result = chord_theory.recognize_chord(test_notes, min_notes_for_chord=2)
    
    print(f"Recognized: {result}")
    print()
    
    # Let's also check what the intervals are
    print("Interval analysis:")
    root_c = 60  # C
    intervals = []
    for note in sorted(test_notes):
        interval = (note - root_c) % 12
        intervals.append(interval)
    print(f"Intervals from C: {intervals}")
    print(f"Expected C9 intervals: [0, 4, 10, 2] (root, 3rd, 7th, 9th)")
    
    # Check if we have the right intervals
    expected_c9 = {0, 4, 10, 2}  # C9 intervals
    actual_intervals = set(intervals)
    print(f"Actual interval set: {actual_intervals}")
    print(f"Expected C9 interval set: {expected_c9}")
    print(f"Match: {actual_intervals == expected_c9}")
    
if __name__ == "__main__":
    debug_c9_chord()
