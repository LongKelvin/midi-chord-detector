#!/usr/bin/env python3
"""
Quick test script to verify the chord recognition system works
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.music_theory import ChordTheory

def test_chord_recognition():
    """Test basic chord recognition functionality"""
    print("Testing MIDI Chord Recognition System")
    print("=" * 50)
    
    # Initialize chord theory
    print("Initializing ChordTheory...")
    try:
        chord_theory = ChordTheory()
        print(f"✓ ChordTheory initialized successfully")
        print(f"  - Advanced analyzer available: {chord_theory.use_advanced_analyzer}")
        print(f"  - Genre: {chord_theory.genre}")
    except Exception as e:
        print(f"✗ Failed to initialize ChordTheory: {e}")
        return False
    
    # Test chord definitions
    print(f"\nChord definitions loaded: {len(chord_theory.CHORD_DEFINITIONS)} chords")
    
    # Test basic chord recognition
    test_chords = [
        # (notes, expected_chord_type, description)
        ({60, 64, 67}, "maj", "C Major Triad"),
        ({60, 63, 67}, "min", "C Minor Triad"),
        ({60, 64, 67, 70}, "7", "C Dominant 7th"),
        ({60, 64, 67, 71}, "maj7", "C Major 7th"),
        ({60, 63, 67, 70}, "m7", "C Minor 7th"),
        ({60, 63, 67, 70, 74}, "m9", "C Minor 9th"),  # This was failing before
        ({60, 64, 70, 74}, "9", "C Dominant 9th (no 5th)"),  # Jazz voicing without 5th
    ]
    
    print("\nTesting chord recognition:")
    print("-" * 30)
    
    success_count = 0
    for notes, expected_type, description in test_chords:
        try:
            result = chord_theory.recognize_chord(notes, min_notes_for_chord=2)
            
            if result:
                recognized_type = result.get('chord_type', 'unknown')
                chord_name = result.get('full_chord_name', 'N.C.')
                score = result.get('score', 0)
                confidence = result.get('confidence', 'N/A')
                is_advanced = result.get('advanced_analysis', False)
                
                analyzer_type = "Advanced" if is_advanced else "Basic"
                
                if recognized_type == expected_type:
                    print(f"✓ {description}: {chord_name} (score: {score:.3f}, confidence: {confidence}, {analyzer_type})")
                    success_count += 1
                else:
                    print(f"⚠ {description}: Expected {expected_type}, got {recognized_type} ({chord_name})")
                    print(f"   Notes: {sorted(list(notes))}, Score: {score:.3f}")
                    
                    # Show additional debug info for failed chords
                    if is_advanced:
                        analysis_quality = result.get('analysis_quality', {})
                        missing = analysis_quality.get('missing_expected_intervals', [])
                        extra = analysis_quality.get('extra_intervals', [])
                        if missing:
                            print(f"   Missing intervals: {missing}")
                        if extra:
                            print(f"   Extra intervals: {extra}")
            else:
                print(f"✗ {description}: No chord recognized")
                
        except Exception as e:
            print(f"✗ {description}: Error during recognition: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nResults: {success_count}/{len(test_chords)} chords recognized correctly")
    
    # Test voice separation if advanced analyzer is available
    if chord_theory.use_advanced_analyzer:
        print("\nTesting advanced voice separation:")
        print("-" * 30)
        
        # Test chord with melody note
        notes_with_melody = [48, 60, 64, 67, 84]  # C bass, C major chord, high C melody
        result = chord_theory.recognize_chord(set(notes_with_melody), min_notes_for_chord=2)
        
        if result and result.get('advanced_analysis'):
            voice_sep = result.get('voice_separation', {})
            print(f"Notes with melody: {notes_with_melody}")
            print(f"Recognized chord: {result.get('full_chord_name', 'N.C.')}")
            print(f"Bass notes: {voice_sep.get('bass_notes', [])}")
            print(f"Chord notes: {voice_sep.get('chord_notes', [])}")
            print(f"Melody notes: {voice_sep.get('melody_notes', [])}")
    
    return success_count == len(test_chords)

if __name__ == "__main__":
    success = test_chord_recognition()
    sys.exit(0 if success else 1)
