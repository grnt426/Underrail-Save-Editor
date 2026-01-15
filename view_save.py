#!/usr/bin/env python3
"""
Underrail Save File Viewer

Displays character data from an Underrail save file without modifying anything.
Shows character name, base stats, skills, and feats.

Usage:
    python view_save.py path/to/global.dat
    python view_save.py                        # Uses test fixture if no path given
"""

import argparse
import struct
import sys
from pathlib import Path

from skill_editor import (
    is_packed,
    unpack_data,
    get_skill_names_from_data,
    get_skill_names,
)

# Pattern constants
ESI_PATTERN = b'ESI\x02\x00\x00\x00\x02\x00\x00\x00\x09'
VERSION_MARKER = b'System.Version\x04\x00\x00\x00\x06_Major\x06_Minor\x06_Build\x09_Revision'

STAT_NAMES = ['Strength', 'Dexterity', 'Agility', 'Constitution', 'Perception', 'Will', 'Intelligence']

# Display name mapping for feats (internal abbreviation -> display name)
# Many feats use abbreviated internal names (e.g., 'o' for Opportunist, 'pe' for Psi Empathy)
FEAT_DISPLAY_NAMES = {
    # Single/two letter abbreviations
    'o': 'Opportunist',
    'pe': 'Psi Empathy',
    # Multi-word feats (stored without spaces)
    'heavypunch': 'Heavy Punch',
    'lightningpunches': 'Lightning Punches',
    'surestep': 'Sure Step',
    'quickpockets': 'Quick Pockets',
    'steadyaim': 'Steady Aim',
    'burstfire': 'Burst Fire',
    'fullautoburst': 'Full Auto Burst',
    'cheapshots': 'Cheap Shots',
    'evasivemaneuvers': 'Evasive Maneuvers',
    'freerunning': 'Free Running',
    'mentalsubversion': 'Mental Subversion',
}


def load_save(path: Path) -> bytes:
    """Load and unpack a save file."""
    with open(path, 'rb') as f:
        data = f.read()
    
    if is_packed(data):
        data = unpack_data(data)
    
    return data


def find_character_name(data: bytes) -> str:
    """Find character name in save data."""
    # Pattern: \x06 + byte + XX\x00\x00 + length_byte + name_string + ... + eG
    # The bytes after \x06 vary between saves, so we use a flexible pattern
    for i in range(len(data) - 50):
        # Look for: \x06 + any byte + any byte + \x00\x00 + length (3-30)
        if (data[i] == 0x06 and 
            data[i+3:i+5] == b'\x00\x00'):
            
            length_offset = i + 5
            length = data[length_offset]
            
            if 3 <= length <= 30:
                name_start = length_offset + 1
                name_end = name_start + length
                
                if name_end + 20 <= len(data):
                    potential_name = data[name_start:name_end]
                    # Check if all printable ASCII (including spaces)
                    if all(32 <= b <= 126 for b in potential_name):
                        # Verify with sentinel: "eG" appears shortly after name
                        if b'eG' in data[name_end:name_end+20]:
                            return potential_name.decode('ascii')
    return None


def find_game_version(data: bytes) -> tuple:
    """Find game version (System.Version structure)."""
    idx = data.find(VERSION_MARKER)
    
    if idx >= 0:
        # Skip marker, field nulls, then type bytes
        values_offset = idx + len(VERSION_MARKER) + 4 + 4
        if values_offset + 16 <= len(data):
            major = struct.unpack('<i', data[values_offset:values_offset+4])[0]
            minor = struct.unpack('<i', data[values_offset+4:values_offset+8])[0]
            build = struct.unpack('<i', data[values_offset+8:values_offset+12])[0]
            revision = struct.unpack('<i', data[values_offset+12:values_offset+16])[0]
            
            if 0 <= major <= 10 and 0 <= minor <= 100 and 0 <= build <= 1000 and 0 <= revision <= 10000:
                return (major, minor, build, revision)
    return None


def detect_dlc(data: bytes, skill_count: int) -> dict:
    """Detect installed DLC based on save file content."""
    dlc = {
        'expedition': skill_count >= 24,  # Expedition adds Temporal Manipulation skill
        # Heavy Duty DLC: No reliable detection method found yet.
        # It adds items/content but no unique string markers identified.
    }
    
    # Additional Expedition detection: look for expedition-specific content
    if b'xpbl_' in data or b'expedition_' in data:
        dlc['expedition'] = True
    
    return dlc


def find_base_stats(data: bytes) -> list:
    """Find all base attribute entries."""
    idx = 0
    results = []
    while True:
        idx = data.find(ESI_PATTERN, idx)
        if idx == -1:
            break
        
        value_offset = idx + len(ESI_PATTERN) + 4
        
        if value_offset + 8 <= len(data):
            base = struct.unpack('<i', data[value_offset:value_offset+4])[0]
            effective = struct.unpack('<i', data[value_offset+4:value_offset+8])[0]
            
            if 0 <= base <= 30 and 0 <= effective <= 50:
                results.append({'base': base, 'effective': effective})
        idx += 1
    return results


def find_feats(data: bytes, skills: list = None) -> list:
    """
    Find player feats in the save data.
    
    Player feats are stored in a specific region near the skills data,
    with a pattern: \x0a\x0a\x06 XX XX \x00\x00 + length_byte + feat_name
    
    Detection is now looser - any valid lowercase ASCII string matching the
    pattern is considered a potential feat, without requiring hardcoded lists.
    """
    results = []
    seen_offsets = set()  # Avoid duplicates
    
    # Determine search region based on skills location
    if skills:
        # Feats are typically within a few thousand bytes after last skill
        last_skill_offset = skills[-1]['offset']
        search_start = last_skill_offset
        search_end = min(len(data), last_skill_offset + 5000)
    else:
        # Fallback: search middle portion of file
        search_start = len(data) // 4
        search_end = len(data) * 3 // 4
    
    # Player feat pattern header: \x0a\x0a\x06 + 2 bytes ID + \x00\x00
    feat_header = b'\x0a\x0a\x06'
    
    idx = search_start
    while idx < search_end:
        idx = data.find(feat_header, idx, search_end)
        if idx == -1:
            break
        
        # Header is 7 bytes: \x0a\x0a\x06 + XX XX + \x00\x00
        length_offset = idx + 7
        if length_offset >= len(data):
            idx += 1
            continue
        
        length = data[length_offset]
        # Accept feats from 1 to 30 characters (some are abbreviated like 'o', 'pe')
        if 1 <= length <= 30:
            name_start = length_offset + 1
            name_end = name_start + length
            
            if name_end <= len(data) and name_start not in seen_offsets:
                try:
                    feat_name = data[name_start:name_end].decode('ascii')
                    # Accept any all-lowercase string (feats are stored lowercase)
                    # Also allow single letters (abbreviations like 'o')
                    if feat_name.islower() and feat_name.isalpha():
                        seen_offsets.add(name_start)
                        # Look up display name, or capitalize the internal name
                        display_name = FEAT_DISPLAY_NAMES.get(feat_name, feat_name.capitalize())
                        results.append({
                            'name': display_name,
                            'internal': feat_name,
                            'offset': name_start
                        })
                except (UnicodeDecodeError, ValueError):
                    pass
        
        idx += 1
    
    return results


def main():
    parser = argparse.ArgumentParser(description='View Underrail save file character data')
    parser.add_argument(
        'save_file',
        nargs='?',
        default='tests/fixtures/see_me_now/level_10/global.dat',
        help='Path to global.dat save file'
    )
    args = parser.parse_args()
    
    save_path = Path(args.save_file)
    if not save_path.exists():
        print(f"Error: File not found: {save_path}")
        sys.exit(1)
    
    # Load save
    data = load_save(save_path)
    
    # Get character name and version first
    char_name = find_character_name(data)
    version = find_game_version(data)
    skills = get_skill_names_from_data(data)
    dlc = detect_dlc(data, len(skills) if skills else 0)
    
    # Header
    print()
    print("=" * 60)
    print("UNDERRAIL CHARACTER DATA")
    print("=" * 60)
    print(f"Save file: {save_path}")
    if char_name:
        print(f"Character: {char_name}")
    if version:
        print(f"Game version: {version[0]}.{version[1]}.{version[2]}.{version[3]}")
    
    # DLC info
    dlc_list = []
    if dlc.get('expedition'):
        dlc_list.append("Expedition")
    if dlc_list:
        print(f"DLC detected: {', '.join(dlc_list)}")
    print()
    
    # Base Stats
    stats = find_base_stats(data)
    if stats:
        print("BASE ATTRIBUTES")
        print("-" * 40)
        for i, stat in enumerate(stats):
            name = STAT_NAMES[i] if i < len(STAT_NAMES) else f"Unknown_{i}"
            if stat['base'] != stat['effective']:
                print(f"  {name:<15} {stat['base']:>3}  ({stat['effective']})")
            else:
                print(f"  {name:<15} {stat['base']:>3}")
        print()
    
    # Skills
    if skills:
        skill_names = get_skill_names(len(skills))
        
        print("SKILLS")
        print("-" * 40)
        
        # Group by category
        categories = {
            'Offense': ['Guns', 'Heavy Guns', 'Throwing', 'Crossbows', 'Melee'],
            'Defense': ['Dodge', 'Evasion'],
            'Subterfuge': ['Stealth', 'Hacking', 'Lockpicking', 'Pickpocketing', 'Traps'],
            'Technology': ['Mechanics', 'Electronics', 'Chemistry', 'Biology', 'Tailoring'],
            'Psi': ['Thought Control', 'Psychokinesis', 'Metathermics', 'Temporal Manipulation'],
            'Social': ['Persuasion', 'Intimidation', 'Mercantile'],
        }
        
        # Build skill lookup
        skill_lookup = {}
        for i, skill in enumerate(skills):
            name = skill_names[i] if i < len(skill_names) else f"Unknown_{i}"
            skill_lookup[name] = skill
        
        for category, skill_list in categories.items():
            category_skills = [(name, skill_lookup.get(name)) for name in skill_list if name in skill_lookup]
            if category_skills:
                print(f"\n  {category}:")
                for name, skill in category_skills:
                    if skill['base'] != skill['mod']:
                        print(f"    {name:<22} {skill['base']:>3}  ({skill['mod']})")
                    else:
                        print(f"    {name:<22} {skill['base']:>3}")
        
        # Summary
        total_base = sum(s['base'] for s in skills)
        print()
        print("-" * 40)
        print(f"  Total skill points: {total_base}")
        print()
    
    # Feats
    feats = find_feats(data, skills)
    if feats:
        print("FEATS")
        print("-" * 40)
        for feat in feats:
            print(f"  {feat['name']}")
        print()
    
    print("=" * 60)


if __name__ == "__main__":
    main()
