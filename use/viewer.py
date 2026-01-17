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
    load_save_data,
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
    get_inventory_summary,
    get_equipment_summary,
    STAT_NAMES,
    SKILL_CATEGORIES,
)


def display_character_data(save_path: Path):
    """Load and display all character data from a save file."""
    
    # Load save data via UFE parser
    save_data = load_save_data(save_path)
    
    # Get character info
    char_name = find_character_name(save_data)
    version = find_game_version(save_data)
    skills = get_skill_entries(save_data)
    dlc = detect_dlc(save_data, len(skills) if skills else 0)
    
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
    char_level = find_character_level(save_data, total_skill_points)
    if char_level is not None:
        print(f"Level: {char_level}")
    
    # XP system detection
    xp_system, xp_certain = detect_xp_system(save_data)
    
    xp = find_xp_current(save_data)
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
    currency = find_currency(save_data)
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
    stats = get_stat_entries(save_data)
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
    feats = find_feats(save_data, skills)
    if feats:
        print("FEATS")
        print("-" * 40)
        for feat in feats:
            print(f"  {feat['name']}")
        print()
    
    # Equipment
    equipment = get_equipment_summary(save_data)
    if equipment['total_equipped'] > 0:
        print("EQUIPPED")
        print("-" * 40)
        
        # Character gear (armor, weapons, belt)
        if equipment['character_gear']:
            print("\n  Character Gear:")
            for item in equipment['character_gear']:
                print(f"    {item['name']:<30} [{item['category']}]")
                
                # Weapon stats
                weapon = item.get('weapon')
                if weapon:
                    dmg_min = weapon.get('damage_min')
                    dmg_max = weapon.get('damage_max')
                    ap = weapon.get('ap_cost')
                    crit = weapon.get('crit_chance')
                    crit_dmg = weapon.get('crit_damage')
                    
                    weapon_stats = []
                    if dmg_min is not None and dmg_max is not None:
                        weapon_stats.append(f"Damage: {dmg_min}-{dmg_max}")
                    if ap is not None:
                        weapon_stats.append(f"AP: {ap}")
                    if crit is not None:
                        weapon_stats.append(f"Crit: {crit*100:.0f}%")
                    if crit_dmg is not None and crit_dmg != 1.0:
                        bonus = (crit_dmg - 1) * 100
                        sign = "+" if bonus >= 0 else ""
                        weapon_stats.append(f"Crit Dmg: {sign}{bonus:.0f}%")
                    if weapon_stats:
                        print(f"      {', '.join(weapon_stats)}")
                
                # Armor stats
                armor = item.get('armor')
                if armor:
                    armor_stats = []
                    for dr in armor.get('damage_resistances', []):
                        val = dr.get('value', 0)
                        res = dr.get('resistance', 0)
                        if val > 0 or res > 0:
                            armor_stats.append(f"DR: {val} ({res*100:.0f}%)")
                    evasion = armor.get('evasion_penalty', 0)
                    if evasion > 0:
                        armor_stats.append(f"Evasion: -{evasion*100:.0f}%")
                    if armor_stats:
                        print(f"      {', '.join(armor_stats)}")
                
                # Durability and energy
                dur = item.get('current_durability')
                bat = item.get('current_battery')
                max_bat = item.get('max_battery')
                
                runtime_stats = []
                if dur is not None and dur > 0:
                    runtime_stats.append(f"Durability: {dur:.0f}")
                if bat is not None and bat > 0:
                    if max_bat:
                        runtime_stats.append(f"Energy: {bat:.0f}/{max_bat}")
                    else:
                        runtime_stats.append(f"Energy: {bat:.0f}")
                if runtime_stats:
                    print(f"      {', '.join(runtime_stats)}")
                
                # Basic stats (value, weight)
                basic_stats = []
                if item.get('value') is not None:
                    basic_stats.append(f"Value: {item['value']:,.0f}")
                if item.get('weight') is not None:
                    basic_stats.append(f"Weight: {item['weight']:.1f}")
                if basic_stats:
                    print(f"      {', '.join(basic_stats)}")
        
        # Utility slots (belt slots for grenades, tools, etc.)
        if equipment['utility_slots']:
            print("\n  Utility Slots:")
            for item in equipment['utility_slots']:
                count = item.get('count', 1)
                if count > 1:
                    print(f"    {item['name']:<30} x{count}")
                else:
                    print(f"    {item['name']:<30}")
        
        # Hotbar items
        if equipment['hotbar']:
            print("\n  Hotbar:")
            for item in equipment['hotbar']:
                print(f"    {item['name']:<30} [{item['category']}]")
        
        print()
        print("-" * 40)
        print(f"  Total equipped: {equipment['total_equipped']}")
        print()
    
    # Inventory
    inventory = get_inventory_summary(save_data)
    if inventory['items']:
        print("INVENTORY")
        print("-" * 40)
        
        # Display by category, excluding currency (already shown above)
        category_order = ['Weapons', 'Armor', 'Consumables', 'Devices', 'Grenades', 
                         'Traps', 'Components', 'Expendables', 'Ammo', 'Quest Items']
        
        for category in category_order:
            if category in inventory['by_category']:
                cat_items = inventory['by_category'][category]
                print(f"\n  {category}:")
                for item in cat_items:
                    # Format count display
                    if item['stack_counts']:
                        # Multiple stacks - show breakdown
                        stack_str = '+'.join(str(c) for c in item['stack_counts'])
                        count_str = f"x{item['count']} ({stack_str})"
                    else:
                        count_str = f"x{item['count']}"
                    
                    print(f"    {item['name']:<30} {count_str}")
        
        # Show any remaining categories
        for category, cat_items in sorted(inventory['by_category'].items()):
            if category not in category_order and category != 'Currency':
                print(f"\n  {category}:")
                for item in cat_items:
                    if item['stack_counts']:
                        stack_str = '+'.join(str(c) for c in item['stack_counts'])
                        count_str = f"x{item['count']} ({stack_str})"
                    else:
                        count_str = f"x{item['count']}"
                    print(f"    {item['name']:<30} {count_str}")
        
        print()
        print("-" * 40)
        print(f"  Total unique items: {inventory['total_items']}")
        print(f"  Total stacks: {inventory['total_stacks']}")
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
