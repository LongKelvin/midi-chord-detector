#!/usr/bin/env python3
"""
Enhanced debug for root weighting in Cmaj6 vs Am7/C
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.advanced_chord_analyzer import AdvancedChordAnalyzer

def debug_root_weighting():
    """Debug the root weighting system"""
    analyzer = AdvancedChordAnalyzer()
    
    # Test notes: C(60), E(64), G(67), A(69) = Cmaj6 or Am7/C
    test_notes = [60, 64, 67, 69]
    bass_note_pc = min(test_notes) % 12  # Should be 0 (C)
    
    print("Root Weighting Analysis")
    print("=" * 30)
    print(f"Test notes: {test_notes} (C-E-G-A)")
    print(f"Bass note PC: {bass_note_pc} ({analyzer._pc_to_name(bass_note_pc)})")
    
    # Check all root candidates that would be generated
    root_candidates = []
    
    # First priority: bass note as root (C = 0)
    root_candidates.append((bass_note_pc, 1.0))
    
    # Second priority: other notes as potential roots
    for note in test_notes:
        pc = note % 12
        if pc != bass_note_pc:
            weight = 0.7 if note <= (min(test_notes) + 12) else 0.5
            root_candidates.append((pc, weight))
    
    print(f"\nRoot candidates:")
    for root_pc, weight in root_candidates:
        note_name = analyzer._pc_to_name(root_pc)
        print(f"  {note_name} (PC {root_pc}): weight {weight}")
    
    # Test scoring for both C6 and Am7
    played_pcs = set(note % 12 for note in test_notes)
    print(f"\nPlayed pitch classes: {played_pcs}")
    
    # Test C as root (should give C6)
    c_relative_pcs = set((pc - 0) % 12 for pc in played_pcs)
    print(f"\nC as root - relative PCs: {c_relative_pcs}")
    
    if '6' in analyzer.enhanced_chord_defs:
        c6_def = analyzer.enhanced_chord_defs['6']
        print(f"C6 definition core: {set(c6_def['core'])}")
        c6_matched = c_relative_pcs & set(c6_def['core'])
        c6_missing = set(c6_def['core']) - c_relative_pcs
        print(f"C6 matched core: {c6_matched}")
        print(f"C6 missing core: {c6_missing}")
        
        # Estimate C6 score
        c6_score = len(c6_matched) / len(c6_def['core']) * 0.6  # Core score
        root_bonus_c = (1.0 - 0.3) * 0.35  # Updated bass note bonus
        c6_total = c6_score + root_bonus_c
        print(f"C6 estimated score: {c6_total:.3f} (core: {c6_score:.3f}, root bonus: {root_bonus_c:.3f})")
    
    # Test A as root (should give Am7)
    a_relative_pcs = set((pc - 9) % 12 for pc in played_pcs)
    print(f"\nA as root - relative PCs: {a_relative_pcs}")
    
    if 'm7' in analyzer.enhanced_chord_defs:
        am7_def = analyzer.enhanced_chord_defs['m7']
        print(f"Am7 definition core: {set(am7_def['core'])}")
        print(f"Am7 definition important: {set(am7_def.get('important', []))}")
        am7_matched_core = a_relative_pcs & set(am7_def['core'])
        am7_matched_important = a_relative_pcs & set(am7_def.get('important', []))
        am7_missing_core = set(am7_def['core']) - a_relative_pcs
        print(f"Am7 matched core: {am7_matched_core}")
        print(f"Am7 matched important: {am7_matched_important}")
        print(f"Am7 missing core: {am7_missing_core}")
        
        # Estimate Am7 score
        am7_core_score = len(am7_matched_core) / len(am7_def['core']) * 0.6
        am7_important_score = len(am7_matched_important) / len(am7_def.get('important', [1])) * 0.25 if am7_def.get('important') else 0
        root_bonus_a = (0.7 - 0.3) * 0.35  # Updated other note bonus
        am7_total = am7_core_score + am7_important_score + root_bonus_a
        print(f"Am7 estimated score: {am7_total:.3f} (core: {am7_core_score:.3f}, important: {am7_important_score:.3f}, root bonus: {root_bonus_a:.3f})")

if __name__ == "__main__":
    debug_root_weighting()
