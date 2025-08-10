#!/usr/bin/env python3
"""
Quick test for the problematic chord types
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.music_theory import ChordTheory

def test_problematic_chords():
    """Test the specific chord types that were failing"""
    chord_theory = ChordTheory(genre='jazz')
    
    # Define test cases with MIDI notes
    test_cases = [
        # (notes, expected, description)
        ({60, 64, 67, 69}, "6", "C Major 6th"),         # C-E-G-A
        ({60, 64, 67, 74}, "add9", "C Add 9"),          # C-E-G-D
        ({60, 63, 67, 69}, "m6", "C Minor 6th"),        # C-Eb-G-A
        ({60, 65, 67}, "sus4", "C Sus4"),               # C-F-G
        ({60, 62, 67}, "sus2", "C Sus2"),               # C-D-G
        ({60, 64, 67, 70, 74, 81}, "13", "C 13th"),     # C-E-G-Bb-D-A
    ]
    
    print("Testing Previously Problematic Chords")
    print("=" * 50)
    
    success_count = 0
    for notes, expected_type, description in test_cases:
        result = chord_theory.recognize_chord(notes, min_notes_for_chord=2)
        
        if result and 'chord_type' in result:
            recognized_type = result['chord_type']
            success = (recognized_type == expected_type)
            
            status = "✓" if success else "✗"
            score = result.get('score', 0)
            confidence = result.get('confidence', 0)
            
            print(f"{status} {description}: Expected 'C{expected_type}', Got '{result['full_chord_name']}' "
                  f"(score: {score:.3f}, conf: {confidence:.3f})")
            
            if success:
                success_count += 1
        else:
            print(f"✗ {description}: No result")
    
    print(f"\nFixed chord types: {success_count}/{len(test_cases)} ({100*success_count/len(test_cases):.1f}%)")

if __name__ == "__main__":
    test_problematic_chords()
