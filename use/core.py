#!/usr/bin/env python3
"""
Core save file processing functions for Underrail Save Editor.

This module handles:
- Loading save files via UFE (Underrail File Exporter)
- Parsing skills, attributes, feats, XP, and currency from save data
- Providing structured access to game data

All other modules (viewer, editor) import from here.
"""

from pathlib import Path
from typing import Optional
from .ufe_parser import parse_save, SaveData, UFEError


# =============================================================================
# Constants
# =============================================================================

# Base attribute names in save file order
STAT_NAMES = ['Strength', 'Dexterity', 'Agility', 'Constitution', 'Perception', 'Will', 'Intelligence']

# Skill names - base game (23 skills)
SKILL_NAMES_BASE = [
    # Offense
    "Guns", "Heavy Guns", "Throwing", "Crossbows", "Melee",
    # Defense
    "Dodge", "Evasion",
    # Subterfuge
    "Stealth", "Hacking", "Lockpicking", "Pickpocketing", "Traps",
    # Technology
    "Mechanics", "Electronics", "Chemistry", "Biology", "Tailoring",
    # Psi
    "Thought Control", "Psychokinesis", "Metathermics",
    # Social
    "Persuasion", "Intimidation", "Mercantile",
]

# Skill names - with Expedition DLC (24 skills, adds Temporal Manipulation)
SKILL_NAMES_DLC = [
    # Offense
    "Guns", "Heavy Guns", "Throwing", "Crossbows", "Melee",
    # Defense
    "Dodge", "Evasion",
    # Subterfuge
    "Stealth", "Hacking", "Lockpicking", "Pickpocketing", "Traps",
    # Technology
    "Mechanics", "Electronics", "Chemistry", "Biology", "Tailoring",
    # Psi
    "Thought Control", "Psychokinesis", "Metathermics", "Temporal Manipulation",
    # Social
    "Persuasion", "Intimidation", "Mercantile",
]

# Skill categories for display grouping
SKILL_CATEGORIES = {
    'Offense': ['Guns', 'Heavy Guns', 'Throwing', 'Crossbows', 'Melee'],
    'Defense': ['Dodge', 'Evasion'],
    'Subterfuge': ['Stealth', 'Hacking', 'Lockpicking', 'Pickpocketing', 'Traps'],
    'Technology': ['Mechanics', 'Electronics', 'Chemistry', 'Biology', 'Tailoring'],
    'Psi': ['Thought Control', 'Psychokinesis', 'Metathermics', 'Temporal Manipulation'],
    'Social': ['Persuasion', 'Intimidation', 'Mercantile'],
}

# Display name mapping for feats (internal abbreviation -> display name)
FEAT_DISPLAY_NAMES = {
    'o': 'Opportunist',
    'pe': 'Psi Empathy',
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
    'nimble': 'Nimble',
    'quicktinkering': 'Quick Tinkering',
    'trapexpert': 'Trap Expert',
    'interloper': 'Interloper',
    'sprint': 'Sprint',
    'specialattacks': 'Specialization: Unarmed Combat',
}

# Known item categories and their display names
ITEM_CATEGORIES = {
    'currency': 'Currency',
    'devices': 'Devices',
    'Devices': 'Devices',
    'weapons': 'Weapons',
    'Weapons': 'Weapons',
    'armor': 'Armor',
    'consumables': 'Consumables',
    'grenades': 'Grenades',
    'Grenades': 'Grenades',
    'traps': 'Traps',
    'components': 'Components',
    'Components': 'Components',
    'expendables': 'Expendables',
    'Ammo': 'Ammo',
    'messages': 'Messages',
    'plot': 'Quest Items',
}


# =============================================================================
# Path Resolution
# =============================================================================

def normalize_path(path_str: str) -> Path:
    """
    Normalize a path string to a Path object.
    
    Handles:
    - Forward slashes (Unix-style)
    - Backward slashes (Windows-style)
    - Mixed slashes
    - Relative and absolute paths
    """
    normalized = path_str.replace('/', '\\').replace('\\', '/')
    return Path(normalized).resolve()


def resolve_save_path(path_input: str | Path | None = None) -> Path:
    """
    Resolve a user-provided path to an actual save file.
    
    Accepts:
    - None or empty: uses current directory
    - A file path: returns it directly (after normalization)
    - A directory path: searches for global.dat or global/global inside
    
    Handles mixed slash styles and relative/absolute paths.
    
    Returns:
        Path to the resolved save file
        
    Raises:
        FileNotFoundError: if path doesn't exist or no save file found
    """
    if path_input is None or (isinstance(path_input, str) and not path_input.strip()):
        path = Path('.').resolve()
    elif isinstance(path_input, str):
        path = Path(path_input.replace('\\', '/')).resolve()
    else:
        path = Path(path_input).resolve()
    
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    
    if path.is_file():
        return path
    
    if path.is_dir():
        candidates = [
            path / "global.dat",
            path / "global" / "global",
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate
        
        raise FileNotFoundError(
            f"No save file found in directory: {path}\n"
            f"Expected 'global.dat' or 'global/global'"
        )
    
    raise FileNotFoundError(f"Path is neither file nor directory: {path}")


def find_save_file(save_dir: str | Path | None = None) -> tuple:
    """
    Find save file in directory, checking multiple locations.
    
    Returns (path, is_packed, data) or (None, None, None) if not found.
    Note: is_packed is always True now (UFE handles this internally).
    """
    try:
        path = resolve_save_path(save_dir)
        return (path, True, None)  # UFE handles unpacking
    except FileNotFoundError:
        return (None, None, None)


# =============================================================================
# Save Data Loading
# =============================================================================

# Cache for parsed save data
_save_cache: dict[Path, SaveData] = {}


def load_save_data(path_input: str | Path | None = None, use_cache: bool = True) -> SaveData:
    """
    Load and parse a save file, returning structured SaveData.
    
    Args:
        path_input: Path to save file, directory, or None for current directory
        use_cache: If True, return cached data if available
    
    Returns:
        SaveData object with parsed game data
    """
    path = resolve_save_path(path_input)
    
    if use_cache and path in _save_cache:
        return _save_cache[path]
    
    save_data = parse_save(path, keep_json=False)
    _save_cache[path] = save_data
    
    return save_data


def clear_cache():
    """Clear the save data cache."""
    _save_cache.clear()


# =============================================================================
# Skill Data
# =============================================================================

def get_skill_entries(data_or_path) -> list:
    """
    Get all skill entries from save data.
    
    Args:
        data_or_path: Either a SaveData object or a path to load
    
    Returns list of dicts with 'name', 'base', 'mod' keys.
    """
    if isinstance(data_or_path, SaveData):
        save_data = data_or_path
    else:
        save_data = load_save_data(data_or_path)
    
    raw_skills = save_data.get_skills()
    skill_names = get_skill_names(len(raw_skills))
    
    results = []
    for i, skill in enumerate(raw_skills):
        name = skill_names[i] if i < len(skill_names) else f"Skill {i}"
        results.append({
            'name': name,
            'base': skill['base'],
            'mod': skill['effective'],
            'offset': i  # Use index as offset for compatibility
        })
    
    return results


def get_skill_names(num_skills: int) -> list:
    """Return appropriate skill name list based on detected skill count."""
    if num_skills >= 24:
        return SKILL_NAMES_DLC
    return SKILL_NAMES_BASE


# =============================================================================
# Base Attributes (Stats)
# =============================================================================

def get_stat_entries(data_or_path) -> list:
    """
    Get all base attribute entries from save data.
    
    Returns list of dicts with 'name', 'base', 'effective' keys.
    """
    if isinstance(data_or_path, SaveData):
        save_data = data_or_path
    else:
        save_data = load_save_data(data_or_path)
    
    attributes = save_data.get_base_attributes()
    
    results = []
    for i, attr in enumerate(attributes):
        results.append({
            'name': attr['name'],
            'base': attr['base'],
            'effective': attr['effective'],
            'offset': i  # Use index as offset for compatibility
        })
    
    return results


# =============================================================================
# Character Info
# =============================================================================

def find_character_name(data_or_path) -> Optional[str]:
    """Get character name from save data."""
    if isinstance(data_or_path, SaveData):
        save_data = data_or_path
    else:
        save_data = load_save_data(data_or_path)
    
    return save_data.get_character_name()


def find_game_version(data_or_path) -> Optional[tuple]:
    """Get game version (System.Version structure)."""
    if isinstance(data_or_path, SaveData):
        save_data = data_or_path
    else:
        save_data = load_save_data(data_or_path)
    
    return save_data.get_game_version()


def find_character_level(save_path_or_data, total_skill_points: int = None) -> Optional[int]:
    """
    Get character level from save data.
    
    Args:
        save_path_or_data: Path or SaveData object
        total_skill_points: Unused, kept for compatibility
    """
    if isinstance(save_path_or_data, SaveData):
        return save_path_or_data.get_character_level()
    
    # If it's a path, try to load the save
    try:
        save_data = load_save_data(save_path_or_data)
        return save_data.get_character_level()
    except (FileNotFoundError, UFEError):
        return None


# =============================================================================
# Experience Points
# =============================================================================

def find_xp_current(data_or_path) -> Optional[int]:
    """
    Find current XP.
    
    Note: XP is now calculated based on oddities studied.
    The game uses oddity XP by default in modern versions.
    """
    # XP tracking is complex in the oddity system
    # For now, return None as the exact XP format needs more research
    return None


def detect_xp_system(data_or_path) -> tuple:
    """
    Detect XP system by looking for studied oddities.
    
    Returns (system_name, is_certain):
    - ('oddity', True) - Definitely Oddity XP
    - ('classic', False) - Likely Classic XP (uncertain)
    """
    if isinstance(data_or_path, SaveData):
        save_data = data_or_path
    else:
        save_data = load_save_data(data_or_path)
    
    # Check for studied oddities in the player's oddity collection
    player = save_data.get_player()
    if player:
        # PC1:O contains oddity study data
        # If any oddities are studied, it's the oddity XP system
        for record in save_data._records:
            obj = record.get('class') or record.get('class_id')
            if obj:
                members = obj.get('members', {})
                for key in members:
                    if 'Oddity.' in str(members.get(key, '')):
                        return ('oddity', True)
    
    return ('classic', False)


def calculate_xp_needed(level: int, xp_system: str = 'oddity') -> int:
    """
    Estimate XP needed to reach the next level.
    NOTE: This is an approximation; actual game values may vary.
    """
    if xp_system == 'classic':
        return level * 1000
    else:
        if level >= 14:
            return 30
        return 2 * (level + 1)


# =============================================================================
# Currency
# =============================================================================

def find_currency(data_or_path) -> dict:
    """Find currency counts (Stygian Coins and SGS Credits)."""
    if isinstance(data_or_path, SaveData):
        save_data = data_or_path
    else:
        save_data = load_save_data(data_or_path)
    
    results = {
        'stygian_coins': None,
        'sgs_credits': None
    }
    
    # Search inventory items for currency
    items = save_data.get_inventory_items()
    for item in items:
        path = item.get('path', '').lower()
        if 'stygiancoin' in path:
            results['stygian_coins'] = item.get('count', 0)
        elif 'sgscredits' in path:
            results['sgs_credits'] = item.get('count', 0)
    
    return results


# =============================================================================
# DLC Detection
# =============================================================================

def detect_dlc(data_or_path, skill_count: int = None) -> dict:
    """Detect installed DLC based on save file content."""
    if isinstance(data_or_path, SaveData):
        save_data = data_or_path
    else:
        save_data = load_save_data(data_or_path)
    
    if skill_count is None:
        skills = save_data.get_skills()
        skill_count = len(skills)
    
    return {
        'expedition': skill_count >= 24,
    }


# =============================================================================
# Feats
# =============================================================================

def find_feats(data_or_path, skills: list = None) -> list:
    """
    Find player feats in the save data.
    
    Returns list of dicts with 'name', 'internal' keys.
    """
    if isinstance(data_or_path, SaveData):
        save_data = data_or_path
    else:
        save_data = load_save_data(data_or_path)
    
    raw_feats = save_data.get_feats()
    
    results = []
    for feat in raw_feats:
        internal = feat.get('internal', '')
        display_name = FEAT_DISPLAY_NAMES.get(internal, internal.replace('_', ' ').title())
        results.append({
            'name': display_name,
            'internal': internal,
            'offset': 0  # Not used with UFE parser
        })
    
    return results


# =============================================================================
# Inventory
# =============================================================================

def _extract_item_display_name(path: str) -> str:
    """
    Convert item path to display name.
    
    Uses item name mappings extracted from game files (.item files in rules/items/).
    Falls back to pattern-based conversion for unmapped items.
    """
    import re
    from .item_names import get_display_name
    
    name = path.split('\\')[-1]
    name_lower = name.lower()
    
    # First, try to get the display name from game file mappings
    display_name = get_display_name(name_lower)
    if display_name:
        return display_name
    
    # Fallback: pattern-based conversion for unmapped items
    name = name.replace('_', ' ')
    name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
    name = re.sub(r'([a-zA-Z])(\d+)$', r'\1 \2', name)
    
    words = name.split()
    result_words = []
    
    acronyms = {'emp', 'he', 'tnt', 'smg', 'em', 'jhp', 'ap', 'hp', 'sgs', 'li', 'ai', 'mk'}
    
    for word in words:
        word_lower = word.lower()
        if word_lower in acronyms:
            result_words.append(word.upper())
        else:
            result_words.append(word.capitalize())
    
    return ' '.join(result_words)


def find_inventory_items(data_or_path) -> list:
    """
    Find all inventory items in save data.
    
    Returns list of dicts with:
        - 'path': internal item path (e.g., 'devices\\fishingrod')
        - 'name': display name (e.g., 'Fishing Rod')
        - 'category': item category (e.g., 'Devices')
        - 'count': quantity of this item
        - 'id': internal item ID
    """
    if isinstance(data_or_path, SaveData):
        save_data = data_or_path
    else:
        save_data = load_save_data(data_or_path)
    
    raw_items = save_data.get_inventory_items()
    
    items = []
    for item in raw_items:
        path = item.get('path', '')
        if not path or '\\' not in path:
            continue
        
        # Skip message items
        if path.startswith('messages\\'):
            continue
        
        parts = path.split('\\')
        category = ITEM_CATEGORIES.get(parts[0], parts[0].title())
        display_name = _extract_item_display_name(path)
        
        items.append({
            'path': path,
            'name': display_name,
            'category': category,
            'count': item.get('count', 1),
            'id': item.get('id'),
            'index': item.get('id', 0),
            'offset': 0,  # Not used with UFE parser
            'durability': item.get('durability', 0),
            'battery': item.get('battery', 0),
        })
    
    return items


def find_equipped_items(data_or_path) -> dict:
    """
    Find equipped items in save data.
    
    Returns dict with:
        - 'character_gear': Items worn on character (armor, gloves, boots, head, shield, weapons)
        - 'utility_slots': Items assigned to utility belt slots (grenades)
        - 'hotbar': Items assigned to hotbar slots (not yet implemented)
    """
    if isinstance(data_or_path, SaveData):
        save_data = data_or_path
    else:
        save_data = load_save_data(data_or_path)
    
    equipped = {
        'character_gear': [],
        'utility_slots': [],
        'hotbar': [],
    }
    
    # Get all crafted/unique items (these include equipped gear)
    all_items = save_data.get_crafted_items()
    
    # Category keywords for classification
    armor_keywords = ['overcoat', 'armor', 'vest', 'jacket', 'suit', 'robe']
    boots_keywords = ['boot', 'tabi', 'shoe', 'sandal']
    head_keywords = ['balaclava', 'helmet', 'goggles', 'mask', 'hood', 'cap']
    gloves_keywords = ['glove']
    shield_keywords = ['shield', 'emitter']
    weapon_keywords = ['knife', 'sword', 'hammer', 'pistol', 'rifle', 'crossbow', 'fist']
    
    for item in all_items:
        name = item.get('name', '')
        name_lower = name.lower()
        
        # Skip items that are clearly not equipment
        if not name or len(name) < 3:
            continue
        
        # Skip descriptions (usually start with "This" or "These")
        if name_lower.startswith(('this ', 'these ', 'a ', 'an ')):
            continue
        
        # Classify the item
        category = None
        
        # Check if it's a weapon (has weapon stats)
        if item.get('weapon'):
            category = 'Weapons'
        elif any(kw in name_lower for kw in gloves_keywords):
            category = 'Gloves'
        elif any(kw in name_lower for kw in boots_keywords):
            category = 'Boots'
        elif any(kw in name_lower for kw in head_keywords):
            category = 'Head'
        elif any(kw in name_lower for kw in shield_keywords):
            category = 'Shield'
        elif any(kw in name_lower for kw in armor_keywords):
            category = 'Armor'
        
        if category:
            gear_item = {
                'path': None,
                'name': name,
                'category': category,
                'id': item.get('id'),
                'offset': 0,
                'value': item.get('value'),
                'weight': item.get('weight'),
            }
            
            # Add weapon stats if applicable
            if item.get('weapon'):
                weapon = item['weapon']
                gear_item['weapon'] = {
                    'damage_min': weapon.get('damage_min'),
                    'damage_max': weapon.get('damage_max'),
                    'ap_cost': weapon.get('ap_cost'),
                    'crit_chance': weapon.get('crit_chance'),
                    'crit_damage': weapon.get('crit_damage'),
                }
            
            equipped['character_gear'].append(gear_item)
    
    # Get inventory items for utility slots (grenades)
    inventory_items = save_data.get_inventory_items()
    
    # Group grenades (these could be utility belt items)
    grenade_items = []
    for item in inventory_items:
        category = item.get('category', '').lower()
        if category == 'grenades':
            display_name = _extract_item_display_name(item.get('path', ''))
            grenade_items.append({
                'path': item.get('path'),
                'name': display_name,
                'category': 'Grenades',
                'count': item.get('count', 1),
                'id': item.get('id'),
                'offset': 0,
            })
    
    # Note: We can't easily distinguish utility belt grenades from inventory grenades
    # without deeper save file analysis. For now, show all grenades as utility slots
    # if there are 4 or fewer (typical utility belt size).
    if len(grenade_items) <= 4:
        equipped['utility_slots'] = grenade_items
    else:
        # Show first 4 as utility slots (approximation)
        equipped['utility_slots'] = grenade_items[:4]
    
    return equipped


def get_equipment_summary(data_or_path) -> dict:
    """
    Get a summary of equipped items.
    
    Returns dict with:
        - 'character_gear': List of items equipped on character
        - 'utility_slots': List of items in utility belt slots
        - 'hotbar': List of items assigned to hotbar
        - 'total_equipped': Total number of equipped items
    """
    equipped = find_equipped_items(data_or_path)
    
    return {
        'character_gear': equipped['character_gear'],
        'utility_slots': equipped['utility_slots'],
        'hotbar': equipped['hotbar'],
        'total_equipped': (
            len(equipped['character_gear']) +
            len(equipped['utility_slots']) +
            len(equipped['hotbar'])
        ),
    }


def get_inventory_summary(data_or_path) -> dict:
    """
    Get a summary of inventory items grouped by category.
    
    Returns dict with:
        - 'items': list of all items (merged by path)
        - 'by_category': dict of category -> list of items
        - 'total_items': total number of unique item types
        - 'total_stacks': total number of stacks (including duplicates)
    """
    raw_items = find_inventory_items(data_or_path)
    
    # Merge items with same path
    from collections import defaultdict
    items_by_key = defaultdict(list)
    for item in raw_items:
        merge_key = item['path'].lower()
        items_by_key[merge_key].append(item)
    
    merged_items = []
    for merge_key, key_items in items_by_key.items():
        total_count = sum(item['count'] for item in key_items)
        individual_counts = [item['count'] for item in key_items]
        
        merged_item = {
            'path': key_items[0]['path'],
            'name': key_items[0]['name'],
            'category': key_items[0]['category'],
            'count': total_count,
            'stacks': len(key_items),
            'stack_counts': individual_counts if len(key_items) > 1 else None,
        }
        merged_items.append(merged_item)
    
    # Sort by category, then by name
    merged_items.sort(key=lambda x: (x['category'], x['name']))
    
    # Group by category
    by_category = defaultdict(list)
    for item in merged_items:
        by_category[item['category']].append(item)
    
    return {
        'items': merged_items,
        'by_category': dict(by_category),
        'total_items': len(merged_items),
        'total_stacks': len(raw_items),
    }


# =============================================================================
# Game Mechanics Helpers
# =============================================================================

def calculate_max_skill_per_level(level: int) -> int:
    """Calculate maximum points allowed per skill at given level."""
    return 10 + (5 * level)


def calculate_total_skill_points(level: int) -> int:
    """Calculate total skill points available at given level."""
    return 120 + (40 * level)


# =============================================================================
# Legacy Compatibility
# =============================================================================

# These functions are kept for backward compatibility but now use UFE

def load_save(path_input: str | Path | None = None) -> bytes:
    """
    Legacy function - loads save data.
    
    Note: This now returns an empty bytes object since UFE handles parsing.
    Use load_save_data() instead for the new API.
    """
    # For backward compatibility, just return empty bytes
    # The actual parsing is done via load_save_data()
    return b''


def is_packed(data: bytes) -> bool:
    """Legacy function - always returns True (UFE handles packing)."""
    return True


def unpack_data(packed_data: bytes) -> bytes:
    """Legacy function - returns input (UFE handles unpacking)."""
    return packed_data


def pack_data(unpacked_data: bytes) -> bytes:
    """Legacy function - returns input (not implemented with UFE)."""
    raise NotImplementedError(
        "Direct binary packing is not supported with UFE parser. "
        "Use UFE's patch functionality instead."
    )


def write_skill_value(data: bytearray, offset: int, base_value: int, mod_value: int = None):
    """Legacy function - not implemented with UFE parser."""
    raise NotImplementedError(
        "Direct binary writing is not supported with UFE parser. "
        "Use UFE's patch functionality instead."
    )


def write_stat_value(data: bytearray, offset: int, base_value: int, effective_value: int = None):
    """Legacy function - not implemented with UFE parser."""
    raise NotImplementedError(
        "Direct binary writing is not supported with UFE parser. "
        "Use UFE's patch functionality instead."
    )
