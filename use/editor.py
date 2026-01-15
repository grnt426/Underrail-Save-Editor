#!/usr/bin/env python3
"""
Underrail Save File Editor

Edits skill point allocations and base stats in Underrail save files.
"""

import struct
import sys
from pathlib import Path

from .core import (
    is_packed,
    unpack_data,
    pack_data,
    find_save_file,
    find_character_level,
    get_stat_entries,
    get_skill_entries,
    get_skill_names,
    write_skill_value,
    write_stat_value,
    calculate_max_skill_per_level,
    calculate_total_skill_points,
    STAT_NAMES,
)


def main(args=None):
    """Main entry point for the editor."""
    print("=" * 60)
    print("Underrail Save File Editor")
    print("=" * 60)
    print()
    
    # Track whether to ignore warnings
    ignore_warnings = False
    first_warning = True
    
    # Resolve save file path from args (handles directories, files, mixed slashes)
    path_arg = args[0] if args and len(args) > 0 else None
    input_file, is_packed_file, data = find_save_file(path_arg)
    
    if input_file is None or data is None:
        print("ERROR: No save file found!")
        if path_arg:
            print(f"Path: {path_arg}")
        print("Expected 'global.dat' or 'global/global' in the specified location.")
        sys.exit(1)
    
    if is_packed_file:
        print(f"Found packed file: '{input_file}'")
    else:
        print(f"Found unpacked file: '{input_file}'")
    
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
    char_level = find_character_level(input_file)
    
    if char_level is not None and 1 <= char_level <= 30:
        print(f"Auto-detected level: {char_level}")
    else:
        # Ask user for level
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
    
    max_skill_per_level = calculate_max_skill_per_level(char_level)
    total_skill_points = calculate_total_skill_points(char_level)
    
    print(f"\nAt level {char_level}:")
    print(f"  - Maximum points per skill: {max_skill_per_level}")
    print(f"  - Total available skill points: {total_skill_points}")
    print()
    
    # Find all skills
    print("Scanning for skill data...")
    skill_entries = get_skill_entries(data)
    
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
    
    # Convert to bytearray for editing
    data = bytearray(data)
    changes_made = []
    stat_changes_made = []
    
    # Find and display base stats
    print("=" * 60)
    print("Current Base Attributes")
    print("=" * 60)
    
    stat_entries = get_stat_entries(data)
    
    if stat_entries:
        print(f"{'#':<3} {'Attribute':<15} {'Base':>6} {'Effective':>10}")
        print("-" * 40)
        for i, entry in enumerate(stat_entries):
            name = STAT_NAMES[i] if i < len(STAT_NAMES) else f"Unknown_{i}"
            print(f"{i+1:<3} {name:<15} {entry['base']:>6} {entry['effective']:>10}")
        print()
        
        # Edit base stats
        print("=" * 60)
        print("Edit Base Attributes")
        print("=" * 60)
        print("For each attribute, enter a new base value or press Enter to keep current.")
        print("Valid range: 1 to 99")
        print()
        
        for i, entry in enumerate(stat_entries):
            name = STAT_NAMES[i] if i < len(STAT_NAMES) else f"Unknown_{i}"
            current_base = entry['base']
            current_eff = entry['effective']
            
            while True:
                prompt = f"{name} (current: {current_base}, effective: {current_eff}): "
                new_value = input(prompt).strip()
                
                if new_value == "":
                    break
                
                try:
                    new_base = int(new_value)
                    
                    if new_base < 1:
                        print("  Value must be at least 1.")
                        continue
                    
                    if new_base > 99:
                        print("  Value cannot exceed 99.")
                        continue
                    
                    # Calculate new effective value (preserve bonus)
                    bonus = current_eff - current_base
                    new_eff = new_base + bonus
                    if new_eff < 1:
                        new_eff = new_base
                    
                    # Apply the change
                    write_stat_value(data, entry['offset'], new_base, new_eff)
                    stat_changes_made.append({
                        'name': name,
                        'old_base': current_base,
                        'new_base': new_base,
                        'old_eff': current_eff,
                        'new_eff': new_eff
                    })
                    
                    print(f"  Changed: {current_base} -> {new_base} (effective: {current_eff} -> {new_eff})")
                    break
                    
                except ValueError:
                    print("  Please enter a valid number.")
        
        print()
    else:
        print("Could not find base attribute data in save file.")
        print()
    
    # Interactive skill editing
    print("=" * 60)
    print("Edit Skills")
    print("=" * 60)
    print("For each skill, enter a new base value or press Enter to keep current.")
    print(f"Valid range: 0 to {max_skill_per_level}")
    print()
    
    for i, entry in enumerate(skill_entries):
        name = skill_names[i] if i < len(skill_names) else f"Unknown_{i}"
        current_base = entry['base']
        current_mod = entry['mod']
        
        while True:
            prompt = f"{name} (current: {current_base}, effective: {current_mod}): "
            new_value = input(prompt).strip()
            
            if new_value == "":
                break
            
            try:
                new_base = int(new_value)
                
                if new_base < 0:
                    print("  Value cannot be negative.")
                    continue
                
                if new_base > max_skill_per_level and not ignore_warnings:
                    print(f"  WARNING: Value exceeds max for level {char_level} ({max_skill_per_level})")
                    if first_warning:
                        confirm = input("  Set anyway? (Yes/No/Ignore): ").strip().lower()
                        first_warning = False
                    else:
                        confirm = input("  Set anyway? (y/n/i): ").strip().lower()
                    
                    if confirm == 'i' or confirm == 'ignore':
                        ignore_warnings = True
                    elif confirm != 'y' and confirm != 'yes':
                        continue
                
                # Calculate new effective value
                bonus = current_mod - current_base
                new_mod = new_base + bonus
                if new_mod < 0:
                    new_mod = new_base
                
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
    
    if not changes_made and not stat_changes_made:
        print("No changes made.")
        sys.exit(0)
    
    # Calculate total allocated skill points
    total_allocated = 0
    for i, entry in enumerate(skill_entries):
        base = struct.unpack('<i', data[entry['offset']:entry['offset']+4])[0]
        total_allocated += base
    
    print("=" * 60)
    print("Summary of Changes")
    print("=" * 60)
    
    if stat_changes_made:
        print("\nBase Attributes:")
        for change in stat_changes_made:
            print(f"  {change['name']}: {change['old_base']} -> {change['new_base']}")
    
    if changes_made:
        print("\nSkills:")
        for change in changes_made:
            print(f"  {change['name']}: {change['old_base']} -> {change['new_base']}")
    
    print()
    print(f"Total skill points allocated: {total_allocated}")
    print(f"Maximum available at level {char_level}: {total_skill_points}")
    
    if total_allocated > total_skill_points and not ignore_warnings:
        print()
        print("WARNING: Total allocated points exceed maximum available!")
        print(f"         You are {total_allocated - total_skill_points} points over the limit.")
        if first_warning:
            confirm = input("Save anyway? (Yes/No/Ignore): ").strip().lower()
        else:
            confirm = input("Save anyway? (y/n/i): ").strip().lower()
        
        if confirm == 'i' or confirm == 'ignore':
            pass
        elif confirm != 'y' and confirm != 'yes':
            print("Changes discarded.")
            sys.exit(0)
    
    # Determine the packed file location
    if "global" in str(input_file.parent):
        global_dat = input_file.parent.parent / "global.dat"
        unpacked_file = input_file
    else:
        global_dat = save_dir / "global.dat"
        unpacked_file = save_dir / "global" / "global"
    
    # Backup original
    backup_file = global_dat.parent / "global.dat.OLD"
    
    print()
    print("Saving changes...")
    
    backup_created = False
    
    if backup_file.exists():
        print(f"  Note: '{backup_file.name}' already exists (previous backup)")
        overwrite = input("  Replace existing backup with current save? (y/n): ").strip().lower()
        if overwrite == 'y':
            backup_file.unlink()
    
    if global_dat.exists() and not backup_file.exists():
        print(f"  Backing up: '{global_dat.name}' -> '{backup_file.name}'")
        global_dat.rename(backup_file)
        backup_created = True
    
    # Save the unpacked version
    print(f"  Writing unpacked data to '{unpacked_file}'...")
    unpacked_file.parent.mkdir(parents=True, exist_ok=True)
    with open(unpacked_file, 'wb') as f:
        f.write(bytes(data))
    
    # Pack and save
    print(f"  Packing and saving to '{global_dat}'...")
    packed_data = pack_data(bytes(data))
    with open(global_dat, 'wb') as f:
        f.write(packed_data)
    
    print()
    print("Save complete!")
    if backup_created:
        print(f"  - Original backed up to: {backup_file.name}")
    elif backup_file.exists():
        print(f"  - Previous backup preserved: {backup_file.name}")
    print(f"  - New save written to: {global_dat.name}")
    print()
    if backup_file.exists():
        print("To restore the backup, rename 'global.dat.OLD' back to 'global.dat'")
        print()
    print("Note: The game will recalculate effective values when loading.")


if __name__ == "__main__":
    main()
