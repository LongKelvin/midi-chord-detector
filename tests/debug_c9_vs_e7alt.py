#!/usr/bin/env python3
"""
Enhanced debug for C9 vs E7alt chord recognition
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.advanced_chord_analyzer import AdvancedChordAnalyzer

def debug_c9_vs_e7alt():
    """Debug C9 vs E7alt scoring in detail"""
    print("C9 vs E7alt Detailed Analysis")
    print("=" * 50)
    
    # Initialize advanced analyzer
    analyzer = AdvancedChordAnalyzer()
    
    # Test notes: C (60), E (64), Bb (70), D (74)
    test_notes = [60, 64, 70, 74]
    
    print(f"Test notes: {test_notes}")
    print(f"Note names: C(60), E(64), Bb(70), D(74)")
    print()
    
    # Analyze with the fuzzy analyzer
    result = analyzer.analyze_chord_fuzzy(test_notes)
    
    if result:
        print(f"Winner: {result.chord_name}")
        print(f"Score: {result.score}")
        print(f"Confidence: {result.confidence}")
        print(f"Complexity: {result.complexity}")
        print(f"Missing expected: {result.missing_expected}")
        print(f"Extra notes: {result.extra_notes}")
        print()
    
    # Let's manually check both C9 and E7alt definitions
    print("Manual chord definition analysis:")
    print("-" * 40)
    
    # Get the definitions
    defs = analyzer.enhanced_chord_defs
    
    # Test C as root for 9 chord
    c_root_pc = 0  # C
    test_pcs = {note % 12 for note in test_notes}  # {0, 2, 4, 10}
    c_relative_pcs = {(pc - c_root_pc) % 12 for pc in test_pcs}  # {0, 2, 4, 10}
    
    print(f"C9 chord analysis:")
    print(f"  Pitch classes: {test_pcs}")
    print(f"  Relative to C: {c_relative_pcs}")
    
    if '9' in defs:
        c9_def = defs['9']
        print(f"  C9 definition: {c9_def}")
        print(f"  Core intervals: {set(c9_def['core'])}")
        print(f"  Match core: {c_relative_pcs & set(c9_def['core'])}")
        print(f"  Missing core: {set(c9_def['core']) - c_relative_pcs}")
    
    print()
    
    # Test E as root for 7alt chord
    e_root_pc = 4  # E
    e_relative_pcs = {(pc - e_root_pc) % 12 for pc in test_pcs}  # From E: C=8, E=0, Bb=6, D=10
    
    print(f"E7alt chord analysis:")
    print(f"  Relative to E: {e_relative_pcs}")
    
    if '7alt' in defs:
        e7alt_def = defs['7alt']
        print(f"  E7alt definition: {e7alt_def}")
        print(f"  Core intervals: {set(e7alt_def['core'])}")
        print(f"  Important intervals: {set(e7alt_def['important'])}")
        print(f"  Match core: {e_relative_pcs & set(e7alt_def['core'])}")
        print(f"  Match important: {e_relative_pcs & set(e7alt_def['important'])}")
        print(f"  Missing core: {set(e7alt_def['core']) - e_relative_pcs}")

if __name__ == "__main__":
    debug_c9_vs_e7alt()
