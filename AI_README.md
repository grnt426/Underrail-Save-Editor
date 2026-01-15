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

### skill_editor.py
Main editor script with core functions:
- `is_packed(data)` - detect packed files
- `unpack_data(packed_data)` - decompress
- `pack_data(unpacked_data)` - compress with header
- `get_skill_names_from_data(data)` - find all skill entries
- `get_skill_names(num_skills)` - return correct skill list based on DLC detection
- `write_skill_value(data, offset, base, mod)` - modify skill values

### explore_save.py
Diagnostic tool for analyzing save file structure. Useful for reverse-engineering new data patterns or debugging.

```bash
# Full analysis of default test save
python explore_save.py

# Analyze a specific save file
python explore_save.py path/to/global.dat

# Show only base attributes
python explore_save.py --stats

# Show only skills
python explore_save.py --skills

# Show only feats
python explore_save.py --feats

# Hexdump a region (offset, length)
python explore_save.py --hexdump 205900 300

# Search for a string pattern
python explore_save.py --search "opportunist"

# Find all lowercase strings in a region
python explore_save.py --strings 205000 207000
```

## Verification Values (from test saves)

### Character "See Me Now", Level 10 (with Expedition DLC)

**Base Attributes:**

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

**Sample Skills (Level 9 snapshot):**

| Skill | Base | Effective |
|-------|------|-----------|
| Melee | 55 | 83 |
| Dodge | 55 | 78 |
| Evasion | 55 | 78 |
| Stealth | 50 | 90 |
| Hacking | 53 | 50 |
| Lockpicking | 40 | 60 |
| Pickpocketing | 30 | 45 |
| Traps | 17 | 32 |
| Intimidation | 0 | 5 |
| Mercantile | 5 | 14 |
| Temporal Manipulation | 0 | 0 |

### Character "Granite", Level 1 (originally pre-DLC, converted)

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

### Skill Point Verification

- Level 9 total skill points: 440 (formula: 120 + 40*level = 120 + 40*8 = 440)
- Level 10 total skill points: 480 (formula: 120 + 40*9 = 480)
- Difference confirms 40 points per level mechanic
