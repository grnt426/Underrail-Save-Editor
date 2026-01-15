#!/usr/bin/env python3
"""
Underrail Save File Viewer

Displays character data from an Underrail save file without modifying anything.
Shows character name, base stats, skills, feats, XP, and currency.
"""

import argparse
import sys
from pathlib import Path

from .core import (
    load_save,
    resolve_save_path,
    find_character_name,
    find_game_version,
    find_character_level,
    find_xp_current,
    detect_xp_system,
    calculate_xp_needed,
    find_currency,
    get_stat_entries,
    get_skill_entries,
    get_skill_names,
    find_feats,
    detect_dlc,
    STAT_NAMES,
    SKILL_CATEGORIES,
)


def display_character_data(save_path: Path):
    """Load and display all character data from a save file."""
    
    # Load save
    data = load_save(save_path)
    
    # Get character info
    char_name = find_character_name(data)
    version = find_game_version(data)
    skills = get_skill_entries(data)
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
    
    # Calculate total skill points for level detection
    total_skill_points = sum(s['base'] for s in skills) if skills else None
    
    # Character level and XP
    char_level = find_character_level(save_path, total_skill_points)
    if char_level is not None:
        print(f"Level: {char_level}")
    
    # XP system detection
    xp_system, xp_certain = detect_xp_system(data)
    
    xp = find_xp_current(data)
    if xp is not None:
        if char_level is not None:
            xp_needed = calculate_xp_needed(char_level, xp_system)
            if xp_certain:
                system_label = f" ({xp_system.title()} XP)"
            else:
                system_label = f" ({xp_system.title()} XP?)"
            print(f"Experience: {xp:,} / ~{xp_needed:,}{system_label}")
        else:
            if xp_certain:
                system_label = f" ({xp_system.title()} XP)"
            else:
                system_label = f" ({xp_system.title()} XP?)"
            print(f"Experience: {xp:,}{system_label}")
    print()
    
    # Currency
    currency = find_currency(data)
    has_currency = any(v is not None for v in currency.values())
    if has_currency:
        print("CURRENCY")
        print("-" * 40)
        if currency.get('stygian_coins') is not None:
            print(f"  Stygian Coins:    {currency['stygian_coins']:,}")
        if currency.get('sgs_credits') is not None:
            print(f"  SGS Credits:      {currency['sgs_credits']:,}")
        print()
    
    # Base Stats
    stats = get_stat_entries(data)
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
        
        # Build skill lookup
        skill_lookup = {}
        for i, skill in enumerate(skills):
            name = skill_names[i] if i < len(skill_names) else f"Unknown_{i}"
            skill_lookup[name] = skill
        
        for category, skill_list in SKILL_CATEGORIES.items():
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


def main(args=None):
    """Main entry point for the viewer."""
    parser = argparse.ArgumentParser(description='View Underrail save file character data')
    parser.add_argument(
        'save_file',
        nargs='?',
        default=None,
        help='Path to global.dat save file or save folder (defaults to current directory)'
    )
    parsed_args = parser.parse_args(args)
    
    try:
        save_path = resolve_save_path(parsed_args.save_file)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    display_character_data(save_path)


if __name__ == "__main__":
    main()
