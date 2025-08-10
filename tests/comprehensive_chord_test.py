#!/usr/bin/env python3
"""
Comprehensive Chord Recognition Test Suite
Tests all chord types across multiple roots to ensure consistent recognition
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.music_theory import ChordTheory
from typing import Dict, List, Set, Tuple

class ComprehensiveChordTester:
    """Test chord recognition across all roots and chord types"""
    
    def __init__(self):
        self.chord_theory = ChordTheory(genre='jazz')
        
        # Define chord types with their intervals (semitones from root)
        self.chord_definitions = {
            # Major family
            'maj': [0, 4, 7],                    # C-E-G
            'maj7': [0, 4, 7, 11],              # C-E-G-B
            'maj9': [0, 4, 7, 11, 14],          # C-E-G-B-D (14 = 2 + 12)
            'maj6': [0, 4, 7, 9],               # C-E-G-A
            'add9': [0, 4, 7, 14],              # C-E-G-D (no 7th)
            
            # Minor family  
            'min': [0, 3, 7],                   # C-Eb-G
            'm7': [0, 3, 7, 10],                # C-Eb-G-Bb
            'm9': [0, 3, 7, 10, 14],            # C-Eb-G-Bb-D
            'm11': [0, 3, 7, 10, 14, 17],       # C-Eb-G-Bb-D-F (17 = 5 + 12)
            'm6': [0, 3, 7, 9],                 # C-Eb-G-A
            
            # Suspended
            'sus4': [0, 5, 7],                  # C-F-G
            'sus2': [0, 2, 7],                  # C-D-G
            
            # Augmented
            'aug': [0, 4, 8],                   # C-E-G#
            
            # Dominant
            '7': [0, 4, 7, 10],                 # C-E-G-Bb
            '9': [0, 4, 7, 10, 14],             # C-E-G-Bb-D
            '13': [0, 4, 7, 10, 14, 21],        # C-E-G-Bb-D-A (21 = 9 + 12)
        }
        
        # Test roots (all 12 pitch classes)
        self.test_roots = list(range(12))
        self.root_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        # Base MIDI octave for tests
        self.base_octave = 60  # Middle C
    
    def midi_notes_for_chord(self, root_pc: int, chord_type: str, octave: int = 60) -> Set[int]:
        """Generate MIDI note numbers for a chord"""
        if chord_type not in self.chord_definitions:
            raise ValueError(f"Unknown chord type: {chord_type}")
        
        intervals = self.chord_definitions[chord_type]
        midi_notes = set()
        
        for interval in intervals:
            # Calculate MIDI note number
            midi_note = octave + root_pc + interval
            # Keep within reasonable range (avoid going too high)
            if midi_note > 127:
                midi_note -= 12
            midi_notes.add(midi_note)
        
        return midi_notes
    
    def test_single_chord(self, root_pc: int, chord_type: str) -> Dict:
        """Test recognition of a single chord"""
        root_name = self.root_names[root_pc]
        expected_chord_name = f"{root_name}{chord_type}"
        
        try:
            # Generate MIDI notes for the chord
            midi_notes = self.midi_notes_for_chord(root_pc, chord_type, self.base_octave)
            
            # Recognize the chord
            result = self.chord_theory.recognize_chord(midi_notes, min_notes_for_chord=2)
            
            if result and 'full_chord_name' in result:
                recognized_name = result['full_chord_name']
                score = result.get('score', 0)
                confidence = result.get('confidence', 0)
                
                # Check if recognition matches expectation
                success = self._is_recognition_correct(expected_chord_name, recognized_name, chord_type)
                
                return {
                    'success': success,
                    'expected': expected_chord_name,
                    'recognized': recognized_name,
                    'score': round(score, 3),
                    'confidence': round(confidence, 3),
                    'notes': sorted(list(midi_notes)),
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'expected': expected_chord_name,
                    'recognized': 'Unknown',
                    'score': 0,
                    'confidence': 0,
                    'notes': sorted(list(midi_notes)),
                    'error': 'No recognition result'
                }
        
        except Exception as e:
            return {
                'success': False,
                'expected': expected_chord_name,
                'recognized': 'Error',
                'score': 0,
                'confidence': 0,
                'notes': [],
                'error': str(e)
            }
    
    def _is_recognition_correct(self, expected: str, recognized: str, chord_type: str) -> bool:
        """Check if the recognition is correct, allowing for equivalent chord names"""
        
        # Direct match
        if expected.lower() == recognized.lower():
            return True
        
        # Handle equivalent chord names
        equivalents = {
            'maj': ['', 'maj', 'M'],  # C major can be "C", "Cmaj", or "CM"
            'min': ['m', 'min', '-'],  # C minor can be "Cm", "Cmin", or "C-"
            'aug': ['+', 'aug', '#5'],  # C augmented variations
            '7': ['7', 'dom7'],  # Dominant 7th variations
        }
        
        # Extract root from both names
        expected_root = expected[0:2] if len(expected) > 1 and expected[1] in ['#', 'b'] else expected[0]
        recognized_root = recognized[0:2] if len(recognized) > 1 and recognized[1] in ['#', 'b'] else recognized[0]
        
        # Roots must match
        if expected_root != recognized_root:
            return False
        
        # Check chord type equivalents
        expected_suffix = expected[len(expected_root):]
        recognized_suffix = recognized[len(recognized_root):]
        
        if chord_type in equivalents:
            return (expected_suffix in equivalents[chord_type] and 
                   recognized_suffix in equivalents[chord_type])
        
        # For other chord types, allow minor variations
        return expected_suffix.lower() == recognized_suffix.lower()
    
    def test_chord_type_across_roots(self, chord_type: str) -> Dict:
        """Test a specific chord type across all roots"""
        print(f"\nTesting {chord_type} chords across all roots:")
        print("-" * 60)
        
        results = {}
        success_count = 0
        
        for root_pc in self.test_roots:
            root_name = self.root_names[root_pc]
            result = self.test_single_chord(root_pc, chord_type)
            results[root_name] = result
            
            # Print result
            status = "✓" if result['success'] else "✗"
            if result['error']:
                print(f"{status} {root_name}{chord_type}: ERROR - {result['error']}")
            else:
                print(f"{status} {root_name}{chord_type}: Expected '{result['expected']}', Got '{result['recognized']}' "
                      f"(score: {result['score']}, conf: {result['confidence']})")
            
            if result['success']:
                success_count += 1
        
        success_rate = (success_count / len(self.test_roots)) * 100
        print(f"\nSuccess rate for {chord_type}: {success_count}/{len(self.test_roots)} ({success_rate:.1f}%)")
        
        return {
            'chord_type': chord_type,
            'results': results,
            'success_count': success_count,
            'total_tests': len(self.test_roots),
            'success_rate': success_rate
        }
    
    def run_comprehensive_test(self) -> Dict:
        """Run the complete test suite"""
        print("Comprehensive Chord Recognition Test Suite")
        print("=" * 60)
        print(f"Testing {len(self.chord_definitions)} chord types across {len(self.test_roots)} roots")
        print(f"Total tests: {len(self.chord_definitions) * len(self.test_roots)}")
        
        # Initialize chord theory
        print(f"\nChord Theory initialized: Advanced analyzer available: {hasattr(self.chord_theory, 'advanced_analyzer') and self.chord_theory.advanced_analyzer is not None}")
        
        all_results = {}
        overall_success = 0
        overall_total = 0
        
        # Test each chord type
        for chord_type in self.chord_definitions.keys():
            chord_result = self.test_chord_type_across_roots(chord_type)
            all_results[chord_type] = chord_result
            
            overall_success += chord_result['success_count']
            overall_total += chord_result['total_tests']
        
        # Calculate overall statistics
        overall_success_rate = (overall_success / overall_total) * 100 if overall_total > 0 else 0
        
        print(f"\n" + "=" * 60)
        print("OVERALL RESULTS:")
        print(f"Total successful recognitions: {overall_success}/{overall_total} ({overall_success_rate:.1f}%)")
        
        # Show chord type summary
        print(f"\nChord type success rates:")
        for chord_type, result in all_results.items():
            print(f"  {chord_type:>6}: {result['success_count']:>2}/{result['total_tests']} ({result['success_rate']:>5.1f}%)")
        
        # Identify problematic chord types
        problematic_chords = [ct for ct, result in all_results.items() if result['success_rate'] < 80]
        if problematic_chords:
            print(f"\nProblematic chord types (< 80% success): {', '.join(problematic_chords)}")
        
        return {
            'overall_success': overall_success,
            'overall_total': overall_total,
            'overall_success_rate': overall_success_rate,
            'chord_results': all_results,
            'problematic_chords': problematic_chords
        }
    
    def test_specific_chords(self, chord_list: List[Tuple[str, str]]) -> None:
        """Test specific chord combinations"""
        print(f"\nTesting specific chords:")
        print("-" * 40)
        
        for root_name, chord_type in chord_list:
            root_pc = self.root_names.index(root_name)
            result = self.test_single_chord(root_pc, chord_type)
            
            status = "✓" if result['success'] else "✗"
            if result['error']:
                print(f"{status} {root_name}{chord_type}: ERROR - {result['error']}")
            else:
                print(f"{status} {root_name}{chord_type}: Expected '{result['expected']}', Got '{result['recognized']}' "
                      f"(score: {result['score']})")

def main():
    """Run the comprehensive test suite"""
    tester = ComprehensiveChordTester()
    
    # Option 1: Test all chord types across all roots
    results = tester.run_comprehensive_test()
    
    # Option 2: Test specific problematic chords
    if results['problematic_chords']:
        print(f"\n" + "=" * 60)
        print("Testing problematic chords with C root for debugging:")
        specific_tests = [('C', chord_type) for chord_type in results['problematic_chords']]
        tester.test_specific_chords(specific_tests)

if __name__ == "__main__":
    main()
