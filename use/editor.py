#!/usr/bin/env python3
"""
Underrail Save File Editor

Edits skill point allocations and base stats in Underrail save files.
Uses UFE (Underrail File Exporter) for JSON-based editing.
"""

import sys
from pathlib import Path

from .ufe_parser import SaveEditor, UFEError
from .core import (
    find_save_file,
    get_skill_names,
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
    
    # Resolve save file path from args
    path_arg = args[0] if args and len(args) > 0 else None
    input_file = find_save_file(path_arg)
    
    if input_file is None:
        print("ERROR: No save file found!")
        if path_arg:
            print(f"Path: {path_arg}")
        print("Expected 'global.dat' in the specified location.")
        sys.exit(1)
    
    print(f"Found save file: '{input_file}'")
    print()
    
    # Initialize the UFE-based editor
    print("Loading save file with UFE...")
    try:
        editor = SaveEditor(input_file)
        save_data = editor.get_save_data()
        print("Save file loaded successfully.")
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except UFEError as e:
        print(f"ERROR: Failed to parse save file: {e}")
        sys.exit(1)
    
    print()
    
    # Get character info
    char_name = save_data.get_character_name()
    char_level = save_data.get_character_level()
    
    if char_name:
        print(f"Character: {char_name}")
    if char_level and 1 <= char_level <= 30:
        print(f"Level: {char_level}")
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
    
    # Get current skills
    print("Loading skill data...")
    skills = save_data.get_skills()
    
    if not skills:
        print("ERROR: Could not find skill data in save file!")
        editor.cleanup()
        sys.exit(1)
    
    print(f"Found {len(skills)} skills")
    
    # Detect DLC based on skill count
    skill_names = get_skill_names(len(skills))
    has_dlc = len(skills) >= 24
    if has_dlc:
        print("  (Expedition DLC detected - Temporal Manipulation skill present)")
    print()
    
    # Display current skills
    print("=" * 60)
    print("Current Skill Values")
    print("=" * 60)
    print(f"{'#':<3} {'Skill Name':<22} {'Base':>6} {'Effective':>10}")
    print("-" * 60)
    
    for i, skill in enumerate(skills):
        name = skill_names[i] if i < len(skill_names) else f"Unknown_{i}"
        print(f"{i+1:<3} {name:<22} {skill['base']:>6} {skill['effective']:>10}")
    
    print()
    
    # Track changes for summary
    skill_changes = []
    stat_changes = []
    
    # Get and display base attributes
    print("=" * 60)
    print("Current Base Attributes")
    print("=" * 60)
    
    attributes = save_data.get_base_attributes()
    
    if attributes:
        print(f"{'#':<3} {'Attribute':<15} {'Base':>6} {'Effective':>10}")
        print("-" * 40)
        for i, attr in enumerate(attributes):
            name = attr.get('name', STAT_NAMES[i] if i < len(STAT_NAMES) else f"Unknown_{i}")
            print(f"{i+1:<3} {name:<15} {attr['base']:>6} {attr['effective']:>10}")
        print()
        
        # Edit base stats
        print("=" * 60)
        print("Edit Base Attributes")
        print("=" * 60)
        print("For each attribute, enter a new base value or press Enter to keep current.")
        print("Valid range: 1 to 99")
        print()
        
        for i, attr in enumerate(attributes):
            name = attr.get('name', STAT_NAMES[i] if i < len(STAT_NAMES) else f"Unknown_{i}")
            current_base = attr['base']
            current_eff = attr['effective']
            
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
                    if editor.set_attribute_value(i, new_base, new_eff):
                        stat_changes.append({
                            'name': name,
                            'old_base': current_base,
                            'new_base': new_base,
                            'old_eff': current_eff,
                            'new_eff': new_eff
                        })
                        print(f"  Changed: {current_base} -> {new_base} (effective: {current_eff} -> {new_eff})")
                    else:
                        print("  ERROR: Failed to update attribute.")
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
    
    for i, skill in enumerate(skills):
        name = skill_names[i] if i < len(skill_names) else f"Unknown_{i}"
        current_base = skill['base']
        current_mod = skill['effective']
        
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
                if editor.set_skill_value(i, new_base, new_mod):
                    skill_changes.append({
                        'name': name,
                        'old_base': current_base,
                        'new_base': new_base,
                        'old_mod': current_mod,
                        'new_mod': new_mod
                    })
                    print(f"  Changed: {current_base} -> {new_base} (effective: {current_mod} -> {new_mod})")
                else:
                    print("  ERROR: Failed to update skill.")
                break
                
            except ValueError:
                print("  Please enter a valid number.")
    
    print()
    
    if not editor.has_changes():
        print("No changes made.")
        editor.cleanup()
        sys.exit(0)
    
    # Calculate total allocated skill points
    total_allocated = 0
    updated_save_data = editor.get_save_data()
    for skill in updated_save_data.get_skills():
        total_allocated += skill['base']
    
    print("=" * 60)
    print("Summary of Changes")
    print("=" * 60)
    
    if stat_changes:
        print("\nBase Attributes:")
        for change in stat_changes:
            print(f"  {change['name']}: {change['old_base']} -> {change['new_base']}")
    
    if skill_changes:
        print("\nSkills:")
        for change in skill_changes:
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
            editor.cleanup()
            sys.exit(0)
    
    # Apply changes
    print()
    print("Saving changes...")
    
    # Backup check
    backup_path = input_file.with_suffix(input_file.suffix + ".OLD")
    if backup_path.exists():
        print(f"  Note: '{backup_path.name}' already exists (previous backup)")
        overwrite = input("  Replace existing backup with current save? (y/n): ").strip().lower()
        if overwrite == 'y':
            backup_path.unlink()
    
    try:
        # Save JSON and patch
        print(f"  Writing changes to JSON...")
        editor.save(backup=not backup_path.exists())
        
        print(f"  Patching save file with UFE...")
        editor.apply(validate=True, cleanup_json=True)
        
        print()
        print("Save complete!")
        if backup_path.exists():
            print(f"  - Original backed up to: {backup_path.name}")
        print(f"  - Modified save: {input_file.name}")
        print()
        print("To restore the backup, rename 'global.dat.OLD' back to 'global.dat'")
        print()
        print("Note: The game will recalculate effective values when loading.")
        
    except UFEError as e:
        print(f"\nERROR: Failed to apply changes: {e}")
        print("Your original save file should be unchanged.")
        editor.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        editor.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
