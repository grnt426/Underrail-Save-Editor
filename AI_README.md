# Underrail Save File Format - Technical Reference

This document provides technical details for understanding and editing Underrail save files.

## File Structure

### Save Folder Layout
```
<save_name>/
├── global.dat          # Packed main save file (character data, skills, inventory, etc.)
├── global/
│   └── global          # Unpacked version of global.dat
├── info.dat            # Packed metadata file (character name, level, playtime)
└── ... other files
```

### Packed File Format

Both `global.dat` and `info.dat` use the same packing format:

| Offset | Size | Description |
|--------|------|-------------|
| 0-15 | 16 bytes | GUID header: `F9 53 8B 83 1F 36 32 43 BA AE 0D 17 86 5D 08 54` |
| 16-23 | 8 bytes | Version bytes (varies, e.g., `C2 32 0B 72 66 00 00 00`) |
| 24+ | variable | gzip-compressed data |

**Detection**: Check if first 16 bytes match the GUID header.

**Unpacking**: Skip 24 bytes, then `gzip.decompress()` the rest.

**Packing**: Prepend 24-byte header, then `gzip.compress()` the data.

## Character Level Detection

Location: `info.dat` (unpacked)

1. Find keys `SGI:CN` (character name) and `SGI:CL` (character level) - these are around offset 62-69
2. Search bytes 180-350 for a printable ASCII string (character name)
3. Immediately after the string, read 4 bytes as little-endian int32 = character level

```python
# Example: Character name "See Me Now" at offset 192, level (9) at offset 202
for i in range(180, 350):
    if is_printable_string_start(data, i):
        name_end = find_string_end(data, i)
        level = struct.unpack('<i', data[name_end:name_end+4])[0]
        if 1 <= level <= 30:
            # Found it
```

## Skill Data Structure

### Skill Entry Pattern
Skills are identified by searching for this **flexible** pattern:
```
eSKC\x02\x00\x00\x00\x02\x00\x00\x00\x09
```

**IMPORTANT**: The 4 bytes after `\x09` are a **variable type ID** that changes between saves!
- Old saves might have: `\xd6\x02\x00\x00` (726)
- Newer saves might have: `\x5c\x04\x00\x00` (1116)
- Other values are possible

Do NOT hardcode these 4 bytes in the search pattern.

Full structure after the pattern:
- 4 bytes: Variable type ID (skip these)
- 4 bytes: Base skill value (int32 little-endian)
- 4 bytes: Effective/modified skill value (int32 little-endian)

### DLC Detection

The **Expedition DLC** adds the "Temporal Manipulation" skill:
- **Base game**: 23 skills
- **With Expedition DLC**: 24 skills

Detection: Count skill entries found. If >= 24, DLC is present.

### Skill Order (matches game UI)

**Base Game (23 skills):**

| # | Skill | Category |
|---|-------|----------|
| 1 | Guns | Offense |
| 2 | Heavy Guns | Offense |
| 3 | Throwing | Offense |
| 4 | Crossbows | Offense |
| 5 | Melee | Offense |
| 6 | Dodge | Defense |
| 7 | Evasion | Defense |
| 8 | Stealth | Subterfuge |
| 9 | Hacking | Subterfuge |
| 10 | Lockpicking | Subterfuge |
| 11 | Pickpocketing | Subterfuge |
| 12 | Traps | Subterfuge |
| 13 | Mechanics | Technology |
| 14 | Electronics | Technology |
| 15 | Chemistry | Technology |
| 16 | Biology | Technology |
| 17 | Tailoring | Technology |
| 18 | Thought Control | Psi |
| 19 | Psychokinesis | Psi |
| 20 | Metathermics | Psi |
| 21 | Persuasion | Social |
| 22 | Intimidation | Social |
| 23 | Mercantile | Social |

**With Expedition DLC (24 skills):**

| # | Skill | Category |
|---|-------|----------|
| 1-20 | (same as base) | |
| 21 | **Temporal Manipulation** | **Psi (DLC)** |
| 22 | Persuasion | Social |
| 23 | Intimidation | Social |
| 24 | Mercantile | Social |

**Key difference**: Temporal Manipulation is inserted at position 21, shifting Social skills to 22-24.

## Base Attributes (Stats)

### Attribute Entry Pattern
Base attributes use the `ESI` marker, similar to skills:
```
ESI\x02\x00\x00\x00\x02\x00\x00\x00\x09
```

Full structure after the pattern:
- 4 bytes: Variable type ID (1115 observed, skip these)
- 4 bytes: Base attribute value (int32 little-endian)
- 4 bytes: Effective attribute value (int32 little-endian)

### Attribute Order (7 total)

| # | Attribute | Description |
|---|-----------|-------------|
| 1 | Strength | Physical power |
| 2 | Dexterity | Manual dexterity, aim |
| 3 | Agility | Speed, reflexes |
| 4 | Constitution | Health, endurance |
| 5 | Perception | Awareness, senses |
| 6 | Will | Mental fortitude |
| 7 | Intelligence | Mental acuity |

### Attribute Limits
- Base values: 3-10 at character creation
- Effective values can exceed base due to items/effects (e.g., Agility 8 base, 9 effective)

## Feats

### Feat Storage
Feats are stored as **lowercase strings** in the save file, in a region shortly after the skill data.

**IMPORTANT**: Many feats use abbreviated internal names, sometimes just 1-2 characters:
- `o` = Opportunist
- `pe` = Psi Empathy
- `nimble` = Nimble
- `snooping` = Snooping
- `heavypunch` = Heavy Punch
- `lightningpunches` = Lightning Punches
- `deflection`, `parry`, `expertise`, etc.

### Feat Pattern
Feats are found within ~5000 bytes after the last skill entry, with this structure:
```
\x0a\x0a\x06 XX XX \x00\x00 + length_byte + feat_name
```

Example:
```
0a 0a 06 04 04 00 00 06 6e 69 6d 62 6c 65    = "nimble" (length=6)
0a 0a 06 05 04 00 00 08 73 6e 6f 6f 70 69 6e 67  = "snooping" (length=8)
0a 0a 06 06 04 00 00 02 70 65                 = "pe" (length=2, Psi Empathy)
```

The `XX XX` bytes after `\x0a\x0a\x06` appear to be an incrementing ID.

## Experience Points (XP)

### XP Storage Pattern
Current XP is stored using the `eGD` marker with a `value__` field:
```
eGD\x01\x00\x00\x00\x07value__\x00\x08\x02\x00\x00\x00 + XP_VALUE(4 bytes)
```

- XP value is int32 little-endian
- This represents current XP towards next level, NOT total lifetime XP
- XP needed for next level is calculated by game based on character level

### Detection Code
```python
XP_PATTERN = b'eGD\x01\x00\x00\x00\x07value__\x00\x08\x02\x00\x00\x00'
idx = data.find(XP_PATTERN)
if idx != -1:
    xp = struct.unpack('<i', data[idx + len(XP_PATTERN):idx + len(XP_PATTERN) + 4])[0]
```

## Currency

### Currency Types
The game has two main currencies:
- **Stygian Coins** - Primary currency, used for most transactions
- **SGS Credits** - Secondary currency, used at SGS (starting area) vendors

### Currency Internal Paths
```
currency\stygiancoin    # Stygian Coins
currency\sgscredits     # SGS Credits
```

### Currency Storage Pattern
Currency items use a two-part storage:
1. **Definition area** (near end of file): Contains the item path and a 2-byte item ID
2. **Inventory area** (earlier in file): Contains the actual count

Pattern for finding count:
1. Find currency path (e.g., `currency\stygiancoin`)
2. Extract item ID from bytes after path: `\x05 + ID_lo ID_hi + \x00\x00`
3. Search for reference pattern: `count(4 bytes) + \x09 + (ID-1)(2 bytes) + \x00\x00`
4. The count is the 4 bytes before the `\x09` reference

### Detection Code
```python
CURRENCY_PATHS = {
    'stygian_coins': b'currency\\stygiancoin',
    'sgs_credits': b'currency\\sgscredits',
}

# Find path, extract ID, then search for count
idx = data.find(path)
item_id = struct.unpack('<H', data[idx + len(path) + 1:idx + len(path) + 3])[0]
ref_pattern = b'\x09' + struct.pack('<H', item_id - 1) + b'\x00\x00'
ref_idx = data.find(ref_pattern)
count = struct.unpack('<i', data[ref_idx - 4:ref_idx])[0]  # Count is 4-8 bytes before ref
```

## Derived Stats

Derived stats (Health, AP, MP, Fortitude, Resolve, etc.) are calculated from base attributes and feats. Their storage location is less predictable than skills/attributes. Key derived stats:

- **Health**: Based on Constitution
- **Action Points (AP)**: Based on Dexterity
- **Movement Points (MP)**: Based on Agility
- **Fortitude**: Physical resistance
- **Resolve**: Mental resistance
- **Detection**: Awareness of hidden things
- **Stealth**: Ability to remain hidden

## Game Mechanics

### Skill Point Limits
- **Per-skill maximum**: `10 + (5 × character_level)`
- **Total skill points**: `120 + (40 × character_level)`

### Effective vs Base Values
- Base value = player-allocated points
- Effective value = base + bonuses from gear, feats, etc.
- The game recalculates effective values on load
- When editing, adjust effective value by same delta as base (preserves bonus)

## Code Reference

### Project Structure

```
Underrail Character Editor/
├── run.bat              # Windows launcher
├── run.sh               # Unix launcher  
├── use/                 # Python package (Underrail Save Editor)
│   ├── __init__.py      # Package init
│   ├── core.py          # Shared save file processing functions
│   ├── viewer.py        # Character data viewer
│   ├── editor.py        # Save file editor
│   └── main_screen.py   # Console menu interface
├── tests/               # Unit and e2e tests
├── README.md            # User documentation
└── AI_README.md         # This file (technical reference)
```

### use/core.py
Core module with all shared save file processing functions:
- `is_packed(data)` - detect packed files
- `unpack_data(packed_data)` - decompress
- `pack_data(unpacked_data)` - compress with header
- `load_save(path)` - load and unpack a save file
- `find_save_file(save_dir)` - find save file in directory
- `get_skill_entries(data)` - find all skill entries
- `get_skill_names(num_skills)` - return correct skill list based on DLC detection
- `get_stat_entries(data)` - find all base attribute entries
- `write_skill_value(data, offset, base, mod)` - modify skill values
- `write_stat_value(data, offset, base, effective)` - modify attribute values
- `find_character_name(data)` - extract character name
- `find_game_version(data)` - extract game version
- `find_character_level(save_path, total_skill_points)` - detect character level
- `find_xp_current(data)` - find current XP
- `detect_xp_system(data)` - detect Oddity vs Classic XP
- `find_currency(data)` - find currency counts
- `find_feats(data, skills)` - find character feats
- `detect_dlc(data, skill_count)` - detect installed DLC

### use/viewer.py
Read-only viewer module. Displays character name, game version, DLC detection,
XP, currency, base attributes, skills (grouped by category), and feats.

### use/editor.py
Interactive editor module. Allows editing base attributes and skill point allocations.
Creates backups before saving.

### use/main_screen.py
Console menu interface. Provides commands: view, edit, help, quit.

### Running the Application

```bash
# Windows
run.bat

# Unix/Linux/macOS
./run.sh

# Or directly with Python
python -m use.main_screen
```

## Verification Values (from test saves)

### Character "See Me Now" (with Expedition DLC)

**Progression across saves:**

| Level | XP | Stygian Coins | SGS Credits | Skill Points |
|-------|-----|---------------|-------------|--------------|
| 9 | 1 | 654 | 855 | 440 |
| 10 | 1 | 1,636 | 32 | 480 |
| 11 | 1 | 2,682 | 862 | 1,540 (edited) |

**Base Attributes (Level 10):**

| Attribute | Base | Effective |
|-----------|------|-----------|
| Strength | 6 | 6 |
| Dexterity | 10 | 10 |
| Agility | 8 | 9 |
| Constitution | 5 | 5 |
| Perception | 7 | 7 |
| Will | 3 | 3 |
| Intelligence | 3 | 3 |

**Feats (7 total):**
- Expertise
- Heavy Punch
- Nimble
- Opportunist (stored as `o`)
- Lightning Punches
- Parry
- Deflection

### Character "Granite", Level 1 (originally pre-DLC, converted)

**Currency:**
- Stygian Coins: 0 (not yet acquired)
- SGS Credits: 200

**Base Attributes:**

| Attribute | Base | Effective |
|-----------|------|-----------|
| Strength | 4 | 4 |
| Dexterity | 5 | 5 |
| Agility | 8 | 8 |
| Constitution | 5 | 5 |
| Perception | 5 | 5 |
| Will | 7 | 7 |
| Intelligence | 6 | 6 |

**Feats (3 total):**
- Nimble
- Snooping
- Psi Empathy (stored as `pe`)

**Notes:**
- This save was created before Expedition DLC but now shows 24 skills
- Temporal Manipulation skill is present (with 0 points allocated)
- The game appears to convert saves on first boot after DLC installation

### Skill Point Formula

- **Formula**: `total_skill_points = 80 + (40 * level)`
- **Level detection**: `level = (total_skill_points - 80) / 40`

| Level | Skill Points |
|-------|--------------|
| 1 | 120 |
| 9 | 440 |
| 10 | 480 |
| 11 | 520 |

- Each level grants 40 additional skill points
- Level can be calculated from skill points (used as fallback when info.dat unavailable)

### Experience Systems

Underrail has two XP systems, chosen at character creation (cannot be changed):

**Wiki Reference**: https://www.stygiansoftware.com/wiki/index.php?title=Experience

#### Oddity XP System
Players gain XP by collecting oddities and completing quests. Small numbers.

**Formula**: 
- Levels 1-13: `2 * (level + 1)` XP needed
- Levels 14+: 30 XP needed (capped)
- Max level: 25 (30 with Expedition DLC veteran levels)

| Level | XP to Next |
|-------|------------|
| 1 | 4 |
| 10 | 22 |
| 11 | 24 |
| 14+ | 30 |

#### Classic XP System
Players gain XP by killing enemies, quests, and skill usage. Large numbers.

**Formula**: `level * 1000` XP needed

| Level | XP to Next |
|-------|------------|
| 1 | 1,000 |
| 10 | 10,000 |
| 11 | 11,000 |
| 25 | 25,000 |

#### Auto-Detection
We detect the XP system by looking for studied oddities in the save data:
- If `Oddity.` entries exist (e.g., `Oddity.PsiBeetleBrain`): **Definitely Oddity XP**
- If no `Oddity.` entries: **Likely Classic XP** (but could be Oddity with no oddities studied yet)

The display shows:
- `(Oddity XP)` - confirmed Oddity system
- `(Classic XP?)` - assumed Classic but uncertain (the `?` indicates this could be an early-game Oddity character)

**Limitation**: A fresh Oddity XP character who hasn't studied any oddities is indistinguishable from Classic.

#### Observed Discrepancies
The wiki formulas don't always match observed in-game values:

| Level | Wiki (Oddity) | Observed |
|-------|---------------|----------|
| 5 | 12 | 12 ✓ |
| 6 | 14 | 16 ✗ |
| 8 | 18 | 18 ✓ |
| 10 | 22 | 21 ✗ |
| 11 | 24 | 23 ✗ |

**Conclusion**: The calculated XP needed is displayed as an *estimate* (`~` prefix). 
The actual XP value read from the save file is always accurate. Scripts should
not enforce calculated values - players can freely edit saves.
