#!/usr/bin/env python3
"""
Debug the Cmaj6 vs Am7/C issue
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.advanced_chord_analyzer import AdvancedChordAnalyzer

def debug_cmaj6():
    """Debug Cmaj6 recognition in detail"""
    analyzer = AdvancedChordAnalyzer()
    
    # Test notes: C(60), E(64), G(67), A(69) = Cmaj6 or Am7/C
    test_notes = [60, 64, 67, 69]
    
    print("Debugging Cmaj6 vs Am7/C")
    print("=" * 40)
    print(f"Test notes: {test_notes} (C-E-G-A)")
    
    # Get the fuzzy analysis result
    result = analyzer.analyze_chord_fuzzy(test_notes)
    
    if result:
        print(f"\nWinner: {result.chord_name}")
        print(f"Score: {result.score:.3f}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Root PC: {result.root_pc} ({analyzer._pc_to_name(result.root_pc)})")
        print(f"Missing: {result.missing_expected}")
        print(f"Extra: {result.extra_notes}")
    
    # Let's check what definitions exist
    print(f"\nChecking chord definitions...")
    
    if '6' in analyzer.enhanced_chord_defs:
        maj6_def = analyzer.enhanced_chord_defs['6']
        print(f"maj6 definition: {maj6_def}")
    else:
        print("No '6' chord definition found!")
    
    if 'm7' in analyzer.enhanced_chord_defs:
        m7_def = analyzer.enhanced_chord_defs['m7']
        print(f"m7 definition: {m7_def}")
    
    # Check both C6 and Am7 manually
    print(f"\nManual analysis:")
    
    # C as root (Cmaj6)
    c_pcs = {0, 4, 7, 9}  # C-E-G-A from C
    print(f"C root intervals: {c_pcs}")
    
    # A as root (Am7)  
    a_pcs = {(pc - 9) % 12 for pc in {0, 4, 7, 9}}  # Relative to A
    print(f"A root intervals: {a_pcs}")  # Should be {3, 7, 10, 0}

if __name__ == "__main__":
    debug_cmaj6()
