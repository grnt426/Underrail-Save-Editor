#!/usr/bin/env python3
"""
Underrail Save File Skill Editor
Edits skill point allocations in Underrail save files.
"""

import struct
import gzip
import os
import sys
from pathlib import Path

# GUID header for packed files (24 bytes: 16-byte GUID + 8-byte version)
PACKED_HEADER = bytes([
    0xF9, 0x53, 0x8B, 0x83, 0x1F, 0x36, 0x32, 0x43,
    0xBA, 0xAE, 0x0D, 0x17, 0x86, 0x5D, 0x08, 0x54
])

# Note: Skill offsets are detected dynamically by searching for the eSKC pattern.
# The pattern structure is documented in get_skill_names_from_data().


def is_packed(data: bytes) -> bool:
    """Check if the file is in packed (compressed) format."""
    return data[:16] == PACKED_HEADER


def unpack_data(packed_data: bytes) -> bytes:
    """Unpack a compressed global.dat file."""
    # Skip 24-byte header (16-byte GUID + 8-byte version)
    compressed = packed_data[24:]
    return gzip.decompress(compressed)


def pack_data(unpacked_data: bytes) -> bytes:
    """Pack data back into global.dat format."""
    # Original header from a typical file
    header = bytes([
        0xF9, 0x53, 0x8B, 0x83, 0x1F, 0x36, 0x32, 0x43,
        0xBA, 0xAE, 0x0D, 0x17, 0x86, 0x5D, 0x08, 0x54,
        0xC2, 0x32, 0x0B, 0x72, 0x66, 0x00, 0x00, 0x00
    ])
    compressed = gzip.compress(unpacked_data)
    return header + compressed


def find_skill_offsets(data: bytes) -> list:
    """
    Find skill value offsets by searching for the eSKC pattern.
    
    Note: This function is an alias for get_skill_names_from_data() 
    for backwards compatibility.
    """
    return get_skill_names_from_data(data)


def find_subterfuge_skills(data: bytes) -> list:
    """Find skill offsets by searching for the eSKC pattern.
    
    Note: This function is kept for backwards compatibility but 
    get_skill_names_from_data() is the preferred method.
    """
    # Use the flexible pattern (same as get_skill_names_from_data)
    pattern = b'eSKC\x02\x00\x00\x00\x02\x00\x00\x00\x09'
    
    idx = 0
    found_skills = []
    
    while True:
        idx = data.find(pattern, idx)
        if idx == -1:
            break
        
        # Values are at: pattern_start + len(pattern) + 4 (skip variable type ID)
        value_offset = idx + len(pattern) + 4
        
        if value_offset + 8 <= len(data):
            base_val = struct.unpack('<i', data[value_offset:value_offset+4])[0]
            mod_val = struct.unpack('<i', data[value_offset+4:value_offset+8])[0]
            
            if 0 <= base_val <= 200 and 0 <= mod_val <= 500:
                found_skills.append({
                    'offset': value_offset,
                    'base': base_val,
                    'mod': mod_val
                })
        
        idx += 1
    
    return found_skills


def read_skill_values(data: bytes, offsets: list) -> list:
    """Read skill values from the data at given offsets."""
    skills = []
    for entry in offsets:
        offset = entry['offset']
        base = struct.unpack('<i', data[offset:offset+4])[0]
        mod = struct.unpack('<i', data[offset+4:offset+8])[0]
        skills.append({
            'offset': offset,
            'base': base,
            'mod': mod
        })
    return skills


def write_skill_value(data: bytearray, offset: int, base_value: int, mod_value: int = None):
    """Write a skill value to the data."""
    struct.pack_into('<i', data, offset, base_value)
    if mod_value is not None:
        struct.pack_into('<i', data, offset + 4, mod_value)


def get_skill_names_from_data(data: bytes) -> list:
    """
    Analyze the save file and return skill information.
    Returns list of dicts with 'offset', 'base', 'mod' keys.
    
    Dynamically searches for skill entries using the eSKC marker pattern.
    The pattern structure is:
        eSKC (4 bytes)
        + \x02\x00\x00\x00 (4 bytes)
        + \x02\x00\x00\x00 (4 bytes)  
        + \x09 (1 byte)
        + variable type ID (4 bytes) - THIS VARIES BETWEEN SAVES
        + base_value (4 bytes int32)
        + effective_value (4 bytes int32)
    """
    # Flexible pattern that stops before the variable type ID bytes
    # This matches: eSKC + two int32(2) markers + 0x09 byte
    skill_pattern = b'eSKC\x02\x00\x00\x00\x02\x00\x00\x00\x09'
    
    idx = 0
    all_skill_offsets = []
    
    while True:
        idx = data.find(skill_pattern, idx)
        if idx == -1:
            break
        
        # Values are at: pattern_start + len(pattern) + 4 (skip variable type ID)
        value_offset = idx + len(skill_pattern) + 4
        
        if value_offset + 8 <= len(data):
            base = struct.unpack('<i', data[value_offset:value_offset+4])[0]
            mod = struct.unpack('<i', data[value_offset+4:value_offset+8])[0]
            
            # Filter for reasonable skill values (base 0-300, effective 0-600)
            if 0 <= base <= 300 and 0 <= mod <= 600:
                all_skill_offsets.append({
                    'offset': value_offset,
                    'base': base,
                    'mod': mod
                })
        
        idx += 1
    
    return all_skill_offsets


# Skill name mapping - order matches game UI
# Base game has 23 skills, Expedition DLC adds Temporal Manipulation (24 skills)

SKILL_NAMES_BASE = [
    # Offense
    "Guns",                  # 1
    "Heavy Guns",            # 2
    "Throwing",              # 3
    "Crossbows",             # 4
    "Melee",                 # 5
    # Defense
    "Dodge",                 # 6
    "Evasion",               # 7
    # Subterfuge
    "Stealth",               # 8
    "Hacking",               # 9
    "Lockpicking",           # 10
    "Pickpocketing",         # 11
    "Traps",                 # 12
    # Technology
    "Mechanics",             # 13
    "Electronics",           # 14
    "Chemistry",             # 15
    "Biology",               # 16
    "Tailoring",             # 17
    # Psi
    "Thought Control",       # 18
    "Psychokinesis",         # 19
    "Metathermics",          # 20
    # Social
    "Persuasion",            # 21
    "Intimidation",          # 22
    "Mercantile",            # 23
]

SKILL_NAMES_DLC = [
    # Offense
    "Guns",                  # 1
    "Heavy Guns",            # 2
    "Throwing",              # 3
    "Crossbows",             # 4
    "Melee",                 # 5
    # Defense
    "Dodge",                 # 6
    "Evasion",               # 7
    # Subterfuge
    "Stealth",               # 8
    "Hacking",               # 9
    "Lockpicking",           # 10
    "Pickpocketing",         # 11
    "Traps",                 # 12
    # Technology
    "Mechanics",             # 13
    "Electronics",           # 14
    "Chemistry",             # 15
    "Biology",               # 16
    "Tailoring",             # 17
    # Psi
    "Thought Control",       # 18
    "Psychokinesis",         # 19
    "Metathermics",          # 20
    "Temporal Manipulation", # 21 (Expedition DLC)
    # Social
    "Persuasion",            # 22
    "Intimidation",          # 23
    "Mercantile",            # 24
]

def get_skill_names(num_skills: int) -> list:
    """Return appropriate skill name list based on detected skill count."""
    if num_skills >= 24:
        return SKILL_NAMES_DLC
    else:
        return SKILL_NAMES_BASE

# Note: Skill offsets are dynamically detected at runtime.
# They change based on save file content and cannot be hardcoded.


def main():
    print("=" * 60)
    print("Underrail Save File Skill Editor")
    print("=" * 60)
    print()
    
    # Determine input file
    save_dir = Path(".")
    
    # Check for possible input files in order of preference:
    # 1. global/global (unpacked in subfolder)
    # 2. global.dat (packed)
    # 3. global (unpacked file, not folder)
    
    possible_files = [
        save_dir / "global" / "global",  # Unpacked in subfolder
        save_dir / "global.dat",          # Packed file
        save_dir / "global",              # Unpacked file (only if it's a file, not folder)
    ]
    
    input_file = None
    is_packed_file = False
    data = None
    
    for candidate in possible_files:
        if candidate.exists() and candidate.is_file():
            try:
                with open(candidate, 'rb') as f:
                    data = f.read()
                
                if is_packed(data):
                    print(f"Found packed file: '{candidate}'")
                    is_packed_file = True
                else:
                    print(f"Found unpacked file: '{candidate}'")
                    is_packed_file = False
                
                input_file = candidate
                break
            except PermissionError:
                continue
    
    if input_file is None or data is None:
        print("ERROR: No save file found!")
        print("Please place this script in a save folder containing:")
        print("  - 'global.dat' (packed), or")
        print("  - 'global/global' (unpacked in subfolder)")
        sys.exit(1)
    
    # Unpack if needed
    if is_packed_file:
        print("Unpacking save file...")
        try:
            data = unpack_data(data)
            print(f"Unpacked successfully ({len(data)} bytes)")
        except Exception as e:
            print(f"ERROR: Failed to unpack: {e}")
            sys.exit(1)
    else:
        print(f"File is already unpacked ({len(data)} bytes)")
    
    print()
    
    # Try to auto-detect character level from info.dat
    char_level = None
    info_file = save_dir / "info.dat"
    if not info_file.exists():
        # Check parent directory
        info_file = save_dir.parent / "info.dat"
    
    if info_file.exists():
        try:
            info_data = open(info_file, 'rb').read()
            # info.dat structure has SGI:CL (character level) key
            # The actual values are stored later in the file
            # After character name string, the level follows as int32
            
            # Find SGI:CN (character name) key position
            cn_key = info_data.find(b'SGI:CN')
            cl_key = info_data.find(b'SGI:CL')
            
            if cn_key >= 0 and cl_key >= 0:
                # Values start after the key definitions
                # Search for a readable string (character name) followed by level int32
                # Character names are typically ASCII strings 3-20 chars long
                for i in range(180, min(350, len(info_data) - 20)):
                    # Look for printable string followed by small int (level)
                    if all(32 <= info_data[j] <= 126 for j in range(i, i+3)):
                        # Found start of a string, find its end
                        str_end = i
                        while str_end < len(info_data) and 32 <= info_data[str_end] <= 126:
                            str_end += 1
                        str_len = str_end - i
                        
                        if 3 <= str_len <= 30:  # Reasonable name length
                            # Check if followed by level (1-30)
                            if str_end + 4 <= len(info_data):
                                potential_level = struct.unpack('<i', info_data[str_end:str_end+4])[0]
                                if 1 <= potential_level <= 30:
                                    char_name = info_data[i:str_end].decode('ascii')
                                    char_level = potential_level
                                    print(f"Character: {char_name}")
                                    print(f"Auto-detected level: {char_level}")
                                    break
        except Exception as e:
            print(f"Could not auto-detect level: {e}")
    
    # If auto-detection failed, ask user
    if char_level is None or not (1 <= char_level <= 30):
        print("Enter your character level (needed to calculate max skill values):")
        while True:
            try:
                level_input = input("Character level (1-30): ").strip()
                char_level = int(level_input)
                if 1 <= char_level <= 30:
                    break
                print("Level must be between 1 and 30.")
            except ValueError:
                print("Please enter a valid number.")
    
    max_skill_per_level = 10 + (5 * char_level)
    total_skill_points = 120 + (40 * char_level)
    
    print(f"\nAt level {char_level}:")
    print(f"  - Maximum points per skill: {max_skill_per_level}")
    print(f"  - Total available skill points: {total_skill_points}")
    print()
    
    # Find all skills
    print("Scanning for skill data...")
    skill_entries = get_skill_names_from_data(data)
    
    if not skill_entries:
        print("ERROR: Could not find skill data in save file!")
        sys.exit(1)
    
    print(f"Found {len(skill_entries)} skill entries")
    
    # Detect DLC based on skill count
    skill_names = get_skill_names(len(skill_entries))
    has_dlc = len(skill_entries) >= 24
    if has_dlc:
        print("  (Expedition DLC detected - Temporal Manipulation skill present)")
    print()
    
    # Display current skills
    print("=" * 60)
    print("Current Skill Values")
    print("=" * 60)
    print(f"{'#':<3} {'Skill Name':<22} {'Base':>6} {'Effective':>10}")
    print("-" * 60)
    
    for i, entry in enumerate(skill_entries):
        name = skill_names[i] if i < len(skill_names) else f"Unknown_{i}"
        print(f"{i+1:<3} {name:<22} {entry['base']:>6} {entry['mod']:>10}")
    
    print()
    
    # Interactive editing
    print("=" * 60)
    print("Edit Skills")
    print("=" * 60)
    print("For each skill, enter a new base value or press Enter to keep current.")
    print(f"Valid range: 0 to {max_skill_per_level}")
    print()
    
    # Convert to bytearray for editing
    data = bytearray(data)
    changes_made = []
    
    for i, entry in enumerate(skill_entries):
        name = skill_names[i] if i < len(skill_names) else f"Unknown_{i}"
        current_base = entry['base']
        current_mod = entry['mod']
        
        while True:
            prompt = f"{name} (current: {current_base}, effective: {current_mod}): "
            new_value = input(prompt).strip()
            
            if new_value == "":
                # Keep current value
                break
            
            try:
                new_base = int(new_value)
                
                if new_base < 0:
                    print("  Value cannot be negative.")
                    continue
                
                if new_base > max_skill_per_level:
                    print(f"  WARNING: Value exceeds max for level {char_level} ({max_skill_per_level})")
                    confirm = input("  Set anyway? (y/n): ").strip().lower()
                    if confirm != 'y':
                        continue
                
                # Calculate new effective value (assuming same bonus ratio)
                # Bonus = current_mod - current_base
                bonus = current_mod - current_base
                new_mod = new_base + bonus
                if new_mod < 0:
                    new_mod = new_base  # At minimum, effective = base
                
                # Apply the change
                write_skill_value(data, entry['offset'], new_base, new_mod)
                changes_made.append({
                    'name': name,
                    'old_base': current_base,
                    'new_base': new_base,
                    'old_mod': current_mod,
                    'new_mod': new_mod
                })
                
                print(f"  Changed: {current_base} -> {new_base} (effective: {current_mod} -> {new_mod})")
                break
                
            except ValueError:
                print("  Please enter a valid number.")
    
    print()
    
    if not changes_made:
        print("No changes made.")
        sys.exit(0)
    
    # Calculate total allocated points
    total_allocated = 0
    for i, entry in enumerate(skill_entries):
        base = struct.unpack('<i', data[entry['offset']:entry['offset']+4])[0]
        total_allocated += base
    
    print("=" * 60)
    print("Summary of Changes")
    print("=" * 60)
    
    for change in changes_made:
        print(f"  {change['name']}: {change['old_base']} -> {change['new_base']}")
    
    print()
    print(f"Total skill points allocated: {total_allocated}")
    print(f"Maximum available at level {char_level}: {total_skill_points}")
    
    if total_allocated > total_skill_points:
        print()
        print("WARNING: Total allocated points exceed maximum available!")
        print(f"         You are {total_allocated - total_skill_points} points over the limit.")
        confirm = input("Save anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Changes discarded.")
            sys.exit(0)
    
    # Determine the packed file location (global.dat in parent of global/ folder)
    if "global" in str(input_file.parent):
        # Input was from global/ subfolder
        global_dat = input_file.parent.parent / "global.dat"
        unpacked_file = input_file
    else:
        global_dat = save_dir / "global.dat"
        unpacked_file = save_dir / "global" / "global"
    
    # Backup original by renaming to .OLD
    backup_file = global_dat.parent / "global.dat.OLD"
    
    print()
    print("Saving changes...")
    
    # Check if backup already exists
    if backup_file.exists():
        print(f"  Note: '{backup_file.name}' already exists (previous backup)")
        overwrite = input("  Overwrite the existing backup? (y/n): ").strip().lower()
        if overwrite == 'y':
            backup_file.unlink()
        else:
            print("  Keeping existing backup.")
    
    # Rename original global.dat to global.dat.OLD
    if global_dat.exists() and not backup_file.exists():
        print(f"  Backing up original: '{global_dat.name}' -> '{backup_file.name}'")
        global_dat.rename(backup_file)
    
    # Save the unpacked version to global/global
    print(f"  Writing unpacked data to '{unpacked_file}'...")
    unpacked_file.parent.mkdir(parents=True, exist_ok=True)
    with open(unpacked_file, 'wb') as f:
        f.write(bytes(data))
    
    # Pack and save as global.dat
    print(f"  Packing and saving to '{global_dat}'...")
    packed_data = pack_data(bytes(data))
    with open(global_dat, 'wb') as f:
        f.write(packed_data)
    
    print()
    print("Save complete!")
    print(f"  - Original backed up to: {backup_file.name}")
    print(f"  - New save written to: {global_dat.name}")
    print()
    print("To restore the original save, rename 'global.dat.OLD' back to 'global.dat'")
    print()
    print("Note: The game will recalculate effective values when loading.")


if __name__ == "__main__":
    main()
