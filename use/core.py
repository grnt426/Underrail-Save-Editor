#!/usr/bin/env python3
"""
Core save file processing functions for Underrail Save Editor.

This module handles:
- Packing/unpacking save files (gzip compression with GUID header)
- Parsing skills, attributes, feats, XP, and currency from save data
- Writing modified values back to save data

All other modules (viewer, editor) import from here.
"""

import struct
import gzip
from pathlib import Path


# =============================================================================
# Constants
# =============================================================================

# GUID header for packed files (16 bytes)
PACKED_HEADER = bytes([
    0xF9, 0x53, 0x8B, 0x83, 0x1F, 0x36, 0x32, 0x43,
    0xBA, 0xAE, 0x0D, 0x17, 0x86, 0x5D, 0x08, 0x54
])

# Full 24-byte header for repacking (GUID + version bytes)
PACK_HEADER_FULL = bytes([
    0xF9, 0x53, 0x8B, 0x83, 0x1F, 0x36, 0x32, 0x43,
    0xBA, 0xAE, 0x0D, 0x17, 0x86, 0x5D, 0x08, 0x54,
    0xC2, 0x32, 0x0B, 0x72, 0x66, 0x00, 0x00, 0x00
])

# Pattern markers for data structures
ESI_PATTERN = b'ESI\x02\x00\x00\x00\x02\x00\x00\x00\x09'
SKILL_PATTERN = b'eSKC\x02\x00\x00\x00\x02\x00\x00\x00\x09'
VERSION_MARKER = b'System.Version\x04\x00\x00\x00\x06_Major\x06_Minor\x06_Build\x09_Revision'
XP_PATTERN = b'eGD\x01\x00\x00\x00\x07value__\x00\x08\x02\x00\x00\x00'

# Currency internal paths
CURRENCY_PATHS = {
    'stygian_coins': b'currency\\stygiancoin',
    'sgs_credits': b'currency\\sgscredits',
}

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
    # Replace forward slashes with the OS-appropriate separator
    # Path() handles this automatically, but let's be explicit
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
    # Handle None/empty - use current directory
    if path_input is None or (isinstance(path_input, str) and not path_input.strip()):
        path = Path('.').resolve()
    elif isinstance(path_input, str):
        # Normalize string paths (handles forward/back slashes)
        path = Path(path_input.replace('\\', '/')).resolve()
    else:
        path = Path(path_input).resolve()
    
    # Check existence
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")
    
    # If it's a file, return it directly
    if path.is_file():
        return path
    
    # It's a directory - search for save files
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


# =============================================================================
# File Packing/Unpacking
# =============================================================================

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
    compressed = gzip.compress(unpacked_data)
    return PACK_HEADER_FULL + compressed


def load_save(path_input: str | Path | None = None) -> bytes:
    """
    Load and unpack a save file, returning raw bytes.
    
    Accepts file path, directory path, or None (current directory).
    Handles mixed slash styles.
    """
    path = resolve_save_path(path_input)
    
    with open(path, 'rb') as f:
        data = f.read()
    
    if is_packed(data):
        data = unpack_data(data)
    
    return data


def find_save_file(save_dir: str | Path | None = None) -> tuple:
    """
    Find save file in directory, checking multiple locations.
    
    Accepts file path, directory path, or None (current directory).
    Handles mixed slash styles.
    
    Returns (path, is_packed, data) or (None, None, None) if not found.
    """
    try:
        path = resolve_save_path(save_dir)
    except FileNotFoundError:
        return (None, None, None)
    
    try:
        with open(path, 'rb') as f:
            data = f.read()
        return (path, is_packed(data), data)
    except (PermissionError, IOError):
        return (None, None, None)


# =============================================================================
# Skill Data
# =============================================================================

def get_skill_entries(data: bytes) -> list:
    """
    Find all skill entries in save data.
    
    Returns list of dicts with 'offset', 'base', 'mod' keys.
    
    Pattern structure:
        eSKC (4 bytes) + markers (9 bytes) + variable_type_id (4 bytes)
        + base_value (4 bytes) + effective_value (4 bytes)
    """
    idx = 0
    results = []
    
    while True:
        idx = data.find(SKILL_PATTERN, idx)
        if idx == -1:
            break
        
        # Values are at: pattern_start + len(pattern) + 4 (skip variable type ID)
        value_offset = idx + len(SKILL_PATTERN) + 4
        
        if value_offset + 8 <= len(data):
            base = struct.unpack('<i', data[value_offset:value_offset+4])[0]
            mod = struct.unpack('<i', data[value_offset+4:value_offset+8])[0]
            
            # Filter for reasonable skill values
            if 0 <= base <= 300 and 0 <= mod <= 600:
                results.append({
                    'offset': value_offset,
                    'base': base,
                    'mod': mod
                })
        
        idx += 1
    
    return results


def get_skill_names(num_skills: int) -> list:
    """Return appropriate skill name list based on detected skill count."""
    if num_skills >= 24:
        return SKILL_NAMES_DLC
    return SKILL_NAMES_BASE


def write_skill_value(data: bytearray, offset: int, base_value: int, mod_value: int = None):
    """Write a skill value to the data."""
    struct.pack_into('<i', data, offset, base_value)
    if mod_value is not None:
        struct.pack_into('<i', data, offset + 4, mod_value)


# =============================================================================
# Base Attributes (Stats)
# =============================================================================

def get_stat_entries(data: bytes) -> list:
    """
    Find all base attribute entries in save data.
    
    Returns list of dicts with 'offset', 'base', 'effective' keys.
    """
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
            
            # Filter for reasonable attribute values
            if 1 <= base <= 30 and 1 <= effective <= 50:
                results.append({
                    'offset': value_offset,
                    'base': base,
                    'effective': effective
                })
        idx += 1
    
    return results


def write_stat_value(data: bytearray, offset: int, base_value: int, effective_value: int = None):
    """Write a stat value to the data."""
    struct.pack_into('<i', data, offset, base_value)
    if effective_value is not None:
        struct.pack_into('<i', data, offset + 4, effective_value)


# =============================================================================
# Character Info
# =============================================================================

def find_character_name(data: bytes) -> str:
    """Find character name in save data."""
    for i in range(len(data) - 50):
        if (data[i] == 0x06 and data[i+3:i+5] == b'\x00\x00'):
            length_offset = i + 5
            length = data[length_offset]
            
            if 3 <= length <= 30:
                name_start = length_offset + 1
                name_end = name_start + length
                
                if name_end + 20 <= len(data):
                    potential_name = data[name_start:name_end]
                    if all(32 <= b <= 126 for b in potential_name):
                        if b'eG' in data[name_end:name_end+20]:
                            return potential_name.decode('ascii')
    return None


def find_game_version(data: bytes) -> tuple:
    """Find game version (System.Version structure)."""
    idx = data.find(VERSION_MARKER)
    
    if idx >= 0:
        values_offset = idx + len(VERSION_MARKER) + 4 + 4
        if values_offset + 16 <= len(data):
            major = struct.unpack('<i', data[values_offset:values_offset+4])[0]
            minor = struct.unpack('<i', data[values_offset+4:values_offset+8])[0]
            build = struct.unpack('<i', data[values_offset+8:values_offset+12])[0]
            revision = struct.unpack('<i', data[values_offset+12:values_offset+16])[0]
            
            if 0 <= major <= 10 and 0 <= minor <= 100 and 0 <= build <= 1000 and 0 <= revision <= 10000:
                return (major, minor, build, revision)
    return None


def find_character_level(save_path: Path, total_skill_points: int = None) -> int:
    """
    Find character level from info.dat or calculate from skill points.
    """
    info_paths = [
        save_path.parent / 'info.dat',
        save_path.parent.parent / 'info.dat',
    ]
    
    for info_path in info_paths:
        if not info_path.exists():
            continue
        
        try:
            with open(info_path, 'rb') as f:
                info_data = f.read()
            
            if is_packed(info_data):
                info_data = unpack_data(info_data)
            
            cn_key = info_data.find(b'SGI:CN')
            cl_key = info_data.find(b'SGI:CL')
            
            if cn_key >= 0 and cl_key >= 0:
                for i in range(180, min(350, len(info_data) - 20)):
                    if all(32 <= info_data[j] <= 126 for j in range(i, min(i+3, len(info_data)))):
                        str_end = i
                        while str_end < len(info_data) and 32 <= info_data[str_end] <= 126:
                            str_end += 1
                        str_len = str_end - i
                        
                        if 3 <= str_len <= 30:
                            if str_end + 4 <= len(info_data):
                                level = struct.unpack('<i', info_data[str_end:str_end+4])[0]
                                if 1 <= level <= 30:
                                    return level
        except Exception:
            continue
    
    # Fallback: calculate from total skill points
    # Formula: total_skill_points = 80 + (40 * level)
    if total_skill_points is not None and total_skill_points >= 120:
        calculated_level = (total_skill_points - 80) // 40
        if 1 <= calculated_level <= 30:
            expected_points = 80 + (40 * calculated_level)
            if abs(total_skill_points - expected_points) <= 40:
                return calculated_level
    
    return None


# =============================================================================
# Experience Points
# =============================================================================

def find_xp_current(data: bytes) -> int:
    """Find current XP using the eGD + value__ pattern."""
    idx = data.find(XP_PATTERN)
    
    if idx != -1:
        value_offset = idx + len(XP_PATTERN)
        if value_offset + 4 <= len(data):
            xp = struct.unpack('<i', data[value_offset:value_offset+4])[0]
            if 0 <= xp <= 10000000:
                return xp
    return None


def detect_xp_system(data: bytes) -> tuple:
    """
    Detect XP system by looking for studied oddities.
    
    Returns (system_name, is_certain):
    - ('oddity', True) - Definitely Oddity XP
    - ('classic', False) - Likely Classic XP (uncertain)
    """
    if b'Oddity.' in data:
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

def find_currency(data: bytes) -> dict:
    """Find currency counts (Stygian Coins and SGS Credits)."""
    results = {}
    
    for name, path in CURRENCY_PATHS.items():
        idx = data.find(path)
        if idx == -1:
            results[name] = None
            continue
        
        id_offset = idx + len(path) + 1
        if id_offset + 2 <= len(data):
            item_id = struct.unpack('<H', data[id_offset:id_offset+2])[0]
            
            ref_id = item_id - 1
            id_bytes_ref = struct.pack('<H', ref_id) + b'\x00\x00'
            
            ref_idx = 0
            found_count = None
            
            while True:
                ref_idx = data.find(b'\x09' + id_bytes_ref, ref_idx)
                if ref_idx == -1:
                    break
                
                for offset_back in [4, 5, 6, 7, 8]:
                    if ref_idx >= offset_back:
                        potential_count = struct.unpack('<i', data[ref_idx-offset_back:ref_idx-offset_back+4])[0]
                        if 0 <= potential_count <= 100000:
                            found_count = potential_count
                            break
                
                if found_count is not None:
                    break
                ref_idx += 1
            
            results[name] = found_count
    
    return results


# =============================================================================
# DLC Detection
# =============================================================================

def detect_dlc(data: bytes, skill_count: int) -> dict:
    """Detect installed DLC based on save file content."""
    dlc = {
        'expedition': skill_count >= 24,
    }
    
    if b'xpbl_' in data or b'expedition_' in data:
        dlc['expedition'] = True
    
    return dlc


# =============================================================================
# Feats
# =============================================================================

def find_feats(data: bytes, skills: list = None) -> list:
    """
    Find player feats in the save data.
    
    Pattern: \\x0a\\x0a\\x06 XX XX \\x00\\x00 + length_byte + feat_name
    """
    results = []
    seen_offsets = set()
    
    if skills:
        last_skill_offset = skills[-1]['offset']
        search_start = last_skill_offset
        search_end = min(len(data), last_skill_offset + 5000)
    else:
        search_start = len(data) // 4
        search_end = len(data) * 3 // 4
    
    feat_header = b'\x0a\x0a\x06'
    
    idx = search_start
    while idx < search_end:
        idx = data.find(feat_header, idx, search_end)
        if idx == -1:
            break
        
        length_offset = idx + 7
        if length_offset >= len(data):
            idx += 1
            continue
        
        length = data[length_offset]
        if 1 <= length <= 30:
            name_start = length_offset + 1
            name_end = name_start + length
            
            if name_end <= len(data) and name_start not in seen_offsets:
                try:
                    feat_name = data[name_start:name_end].decode('ascii')
                    if feat_name.islower() and feat_name.isalpha():
                        seen_offsets.add(name_start)
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


# =============================================================================
# Game Mechanics Helpers
# =============================================================================

def calculate_max_skill_per_level(level: int) -> int:
    """Calculate maximum points allowed per skill at given level."""
    return 10 + (5 * level)


def calculate_total_skill_points(level: int) -> int:
    """Calculate total skill points available at given level."""
    return 120 + (40 * level)
