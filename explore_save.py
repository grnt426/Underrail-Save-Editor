#!/usr/bin/env python3
"""
Underrail Save File Explorer

A diagnostic tool for analyzing the binary structure of Underrail save files.
Useful for reverse-engineering new data patterns or debugging save file issues.

Usage:
    python explore_save.py                           # Analyze default test save
    python explore_save.py path/to/global.dat        # Analyze specific save
    python explore_save.py --stats                   # Show base stats only
    python explore_save.py --skills                  # Show skills only
    python explore_save.py --feats                   # Show feats only
    python explore_save.py --hexdump 205900 300      # Hexdump region
    python explore_save.py --search "pattern"        # Search for string pattern
"""

import argparse
import struct
import sys
from pathlib import Path

from skill_editor import (
    unpack_data,
    is_packed,
    get_skill_names_from_data,
    get_skill_names,
)

# Pattern constants
ESI_PATTERN = b'ESI\x02\x00\x00\x00\x02\x00\x00\x00\x09'  # Base attributes
ESKC_PATTERN = b'eSKC\x02\x00\x00\x00\x02\x00\x00\x00\x09'  # Skills

STAT_NAMES = ['Strength', 'Dexterity', 'Agility', 'Constitution', 'Perception', 'Will', 'Intelligence']


def load_save(path: Path) -> bytes:
    """Load and unpack a save file."""
    with open(path, 'rb') as f:
        data = f.read()
    
    if is_packed(data):
        print(f"Loaded packed save: {path} ({len(data)} bytes packed)")
        data = unpack_data(data)
        print(f"Unpacked to {len(data)} bytes")
    else:
        print(f"Loaded unpacked save: {path} ({len(data)} bytes)")
    
    return data


def hexdump(data: bytes, start: int, length: int):
    """Print a formatted hexdump of a data region."""
    for i in range(0, length, 16):
        if start + i >= len(data):
            break
        offset = start + i
        end = min(start + i + 16, len(data))
        chunk = data[start + i:end]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        print(f'{offset:06x}: {hex_part:<48} {ascii_part}')


def find_base_stats(data: bytes) -> list:
    """Find all base attribute entries using the ESI pattern."""
    idx = 0
    results = []
    while True:
        idx = data.find(ESI_PATTERN, idx)
        if idx == -1:
            break
        
        value_offset = idx + len(ESI_PATTERN) + 4  # Skip pattern + type ID
        
        if value_offset + 8 <= len(data):
            base = struct.unpack('<i', data[value_offset:value_offset+4])[0]
            effective = struct.unpack('<i', data[value_offset+4:value_offset+8])[0]
            
            # Filter for reasonable attribute values
            if 0 <= base <= 30 and 0 <= effective <= 50:
                results.append({
                    'pattern_offset': idx,
                    'value_offset': value_offset,
                    'base': base,
                    'effective': effective
                })
        idx += 1
    return results


def find_feats(data: bytes, skills_region_end: int = None) -> list:
    """
    Find feat strings in the save data.
    Feats are stored as lowercase strings with a length prefix.
    They typically appear shortly after the skills section.
    """
    # Known feat names (lowercase, no spaces)
    known_feats = [
        'nimble', 'heavypunch', 'lightningpunches', 'deflection', 'parry',
        'expertise', 'opportunist', 'conditioning', 'surestep', 'hunter',
        'quickpockets', 'paranoia', 'aimed', 'bullseye', 'steadyaim',
        'gunslinger', 'pointman', 'suppression', 'burstfire', 'commando',
        'fullautoburst', 'kneecap', 'yell', 'execute', 'cheapshots',
        'sprint', 'evasivemaneuvers', 'escape', 'freerunning', 'hit',
        'dodge', 'fancy', 'uncanny', 'finesse', 'executioner', 'recklessness',
        'critical', 'premeditation', 'psychostatic', 'psychoempiric',
    ]
    
    results = []
    for feat in known_feats:
        idx = data.find(feat.encode('ascii'))
        if idx >= 0:
            # Verify it's a feat (has length prefix before it)
            if idx > 0:
                length_byte = data[idx - 1]
                if length_byte == len(feat):
                    results.append({
                        'name': feat,
                        'offset': idx,
                        'length_prefix': length_byte
                    })
    
    return sorted(results, key=lambda x: x['offset'])


def find_strings(data: bytes, start: int, end: int, min_length: int = 4) -> list:
    """Find all lowercase ASCII strings in a region."""
    region = data[start:end]
    results = []
    i = 0
    
    while i < len(region):
        if ord('a') <= region[i] <= ord('z'):
            j = i
            while j < len(region) and ord('a') <= region[j] <= ord('z'):
                j += 1
            if j - i >= min_length:
                string = region[i:j].decode('ascii')
                results.append((start + i, string))
            i = j
        else:
            i += 1
    
    return results


def search_pattern(data: bytes, pattern: str, context_size: int = 20) -> list:
    """Search for a string pattern in the data."""
    pattern_bytes = pattern.encode('ascii')
    results = []
    idx = 0
    
    while True:
        idx = data.find(pattern_bytes, idx)
        if idx == -1:
            break
        
        start = max(0, idx - context_size)
        end = min(len(data), idx + len(pattern) + context_size)
        context = data[start:end]
        
        results.append({
            'offset': idx,
            'context': context
        })
        idx += 1
    
    return results


def analyze_stats(data: bytes):
    """Analyze and display base attributes."""
    print("\n" + "=" * 60)
    print("BASE ATTRIBUTES (ESI Pattern)")
    print("=" * 60)
    
    stats = find_base_stats(data)
    
    if not stats:
        print("No base stats found!")
        return
    
    print(f"Found {len(stats)} attribute entries\n")
    print(f"{'Attribute':<15} {'Base':>6} {'Effective':>10} {'Offset':>10}")
    print("-" * 45)
    
    for i, stat in enumerate(stats):
        name = STAT_NAMES[i] if i < len(STAT_NAMES) else f"Unknown_{i}"
        print(f"{name:<15} {stat['base']:>6} {stat['effective']:>10} {stat['value_offset']:>10}")


def analyze_skills(data: bytes):
    """Analyze and display skills."""
    print("\n" + "=" * 60)
    print("SKILLS (eSKC Pattern)")
    print("=" * 60)
    
    skills = get_skill_names_from_data(data)
    
    if not skills:
        print("No skills found!")
        return
    
    skill_names = get_skill_names(len(skills))
    has_dlc = len(skills) >= 24
    
    print(f"Found {len(skills)} skill entries")
    if has_dlc:
        print("(Expedition DLC detected)")
    
    total_base = sum(s['base'] for s in skills)
    
    print(f"\n{'#':<3} {'Skill':<22} {'Base':>6} {'Effective':>10} {'Offset':>10}")
    print("-" * 55)
    
    for i, skill in enumerate(skills):
        name = skill_names[i] if i < len(skill_names) else f"Unknown_{i}"
        print(f"{i+1:<3} {name:<22} {skill['base']:>6} {skill['mod']:>10} {skill['offset']:>10}")
    
    print("-" * 55)
    print(f"{'TOTAL':<26} {total_base:>6}")


def analyze_feats(data: bytes):
    """Analyze and display feats."""
    print("\n" + "=" * 60)
    print("FEATS")
    print("=" * 60)
    
    # Get skills to estimate feat region
    skills = get_skill_names_from_data(data)
    if skills:
        skills_end = skills[-1]['offset'] + 8
        print(f"Skills end at offset: {skills_end}")
        print(f"Searching for feats in region {skills_end} - {skills_end + 5000}...\n")
    
    feats = find_feats(data)
    
    if not feats:
        print("No known feats found!")
        print("\nTry using --search to find specific feat names")
        return
    
    print(f"Found {len(feats)} feats:\n")
    print(f"{'Feat Name':<25} {'Offset':>10}")
    print("-" * 37)
    
    for feat in feats:
        print(f"{feat['name']:<25} {feat['offset']:>10}")


def full_analysis(data: bytes):
    """Run full analysis of the save file."""
    print("\n" + "=" * 60)
    print("FULL SAVE ANALYSIS")
    print("=" * 60)
    print(f"Data size: {len(data)} bytes")
    
    analyze_stats(data)
    analyze_skills(data)
    analyze_feats(data)
    
    # Summary
    stats = find_base_stats(data)
    skills = get_skill_names_from_data(data)
    feats = find_feats(data)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Base attributes: {len(stats)}")
    print(f"Skills: {len(skills)}")
    print(f"Known feats found: {len(feats)}")
    
    if skills:
        total_skill_points = sum(s['base'] for s in skills)
        print(f"Total skill points allocated: {total_skill_points}")


def main():
    parser = argparse.ArgumentParser(
        description='Explore Underrail save file structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        'save_file',
        nargs='?',
        default='tests/fixtures/see_me_now/level_10/global.dat',
        help='Path to global.dat save file (default: test fixture)'
    )
    
    parser.add_argument('--stats', action='store_true', help='Show base attributes only')
    parser.add_argument('--skills', action='store_true', help='Show skills only')
    parser.add_argument('--feats', action='store_true', help='Show feats only')
    
    parser.add_argument(
        '--hexdump',
        nargs=2,
        type=int,
        metavar=('OFFSET', 'LENGTH'),
        help='Hexdump a region of the file'
    )
    
    parser.add_argument(
        '--search',
        metavar='PATTERN',
        help='Search for a string pattern in the file'
    )
    
    parser.add_argument(
        '--strings',
        nargs=2,
        type=int,
        metavar=('START', 'END'),
        help='Find all lowercase strings in a region'
    )
    
    args = parser.parse_args()
    
    # Load save file
    save_path = Path(args.save_file)
    if not save_path.exists():
        print(f"Error: File not found: {save_path}")
        sys.exit(1)
    
    data = load_save(save_path)
    
    # Execute requested analysis
    if args.hexdump:
        offset, length = args.hexdump
        print(f"\nHexdump at offset {offset}, length {length}:")
        hexdump(data, offset, length)
    
    elif args.search:
        print(f"\nSearching for '{args.search}'...")
        results = search_pattern(data, args.search)
        if results:
            print(f"Found {len(results)} occurrences:")
            for r in results[:10]:  # Limit output
                print(f"  Offset {r['offset']}: {r['context']}")
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more")
        else:
            print("Pattern not found")
    
    elif args.strings:
        start, end = args.strings
        print(f"\nStrings in region {start}-{end}:")
        strings = find_strings(data, start, end)
        for offset, s in strings:
            if len(s) >= 5:
                print(f"  {offset}: '{s}'")
    
    elif args.stats:
        analyze_stats(data)
    
    elif args.skills:
        analyze_skills(data)
    
    elif args.feats:
        analyze_feats(data)
    
    else:
        # Full analysis by default
        full_analysis(data)


if __name__ == "__main__":
    main()
