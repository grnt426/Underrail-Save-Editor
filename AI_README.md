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

## Inventory Items

### Item Storage Structure

All inventory items use the same storage pattern as currency, with paths like:
```
category\itemname
```

### Common Item Categories
| Category | Description | Examples |
|----------|-------------|----------|
| `currency` | Money | stygiancoin -> Stygian Coin, sgscredits -> SGS Credits |
| `devices` | Tools and equipment | fishingrod -> Fishing Rod, lockpick -> Lockpick |
| `weapons` | Weapons | throwingknife -> Throwing Knife, jackknife -> Jackknife |
| `armor` | Armor and belts | waistpack -> Waist Pack |
| `consumables` | Medicines | healthhypo -> Health Hypo, bandage -> Bandage |
| `grenades` | Explosives | frag1 -> Frag Grenade, he2 -> HE Grenade Mk II |
| `traps` | Traps | beartrap -> Bear Trap, fragmine1 -> Frag Mine |
| `components` | Crafting materials | rubbersole -> Rubber Sole, plasmacore -> Plasma Core |
| `expendables` | Ammo/power | fusioncell -> Fusion Cell, sclicell -> Supercharged Lithium Cell |

### Item Entry Pattern
Items are found with this pattern:
```
\x0a\x0a\x06 INDEX(2) \x00\x00 LENGTH PATH \x05 ID(2) \x00\x00
```

Full structure:
- `\x0a\x0a\x06` - Item header marker (3 bytes)
- `INDEX` - 2-byte little-endian item index
- `\x00\x00` - Padding
- `LENGTH` - 1 byte, length of path string
- `PATH` - ASCII string (e.g., "traps\beartrap")
- `\x05` - ID marker
- `ID` - 2-byte little-endian item ID
- `\x00\x00` - Padding

### Item Count Pattern
Item quantities use the same reference pattern as currency:
1. Extract item ID from item entry
2. Search for: `count(4 bytes) + \x09 + (ID-1)(2 bytes) + \x00\x00`
3. Count is the 4-byte little-endian int before the `\x09`

### Stacking
Items with the same path can appear multiple times as separate stacks:
- Throwing Knives might appear twice: 25 + 30 = 55 total
- Same item type in different inventory slots

### Item Container Types (LIDP/IIDP markers)
Different inventory containers are identified by container markers:

**LIDP containers (List Item Data Provider - Inventory items):**
| Marker | Description |
|--------|-------------|
| `LIDP#G1>C00#` | Currency (Stygian Coins) |
| `LIDP#G1>NEI#` | Currency (SGS Credits) |
| `LIDP#G1>CI#` | Components (scraps, materials) |
| `LIDP#G1>ABCI#` | Components (leather, animal parts) |
| `LIDP#G1>ESI2#` | Expendables (energy sources) |
| `LIDP#G1>EXI#` | Expendables (explosives) |
| `LIDP#G1>GI#` | Grenades |
| `LIDP#G1>MI#` | Medical items |
| `LIDP#G1>QSI#` | Quick Slot Items (devices, ammo) |
| `LIDP#G1>T5#` | Traps |
| `LIDP#G1>TI#` | Tools (repair kits, devices) |
| `LIDP#G1>WI#` | Weapons |
| `LIDP#G1>BI1#` | Belt Items (belt armor in inventory) |

**IIDP containers (Instance Item Data Provider - Equipped/assigned items):**
| Marker | Description |
|--------|-------------|
| `IIDP#G1>HI#` | Hotbar Items (assigned to hotbar slots) |
| `IIDP#G1>TI#` | Trap Items (assigned to utility belt) |
| `IIDP#G1>BI#` | Belt Items (assigned to utility belt) |

**CGS marker (Character Gear Slot - Equipped equipment):**
Items with `CGS` marker and `DEI:DT:A` context are equipped on the character:
- Armor (body armor, boots, helmet, etc.)
- Belt (waist pack, utility belt)
- Weapons (main hand, off hand)
- Utility slot items (grenades, tools assigned to belt slots)

### Detection Code
```python
ITEM_HEADER = b'\x0a\x0a\x06'

def find_inventory_items(data: bytes) -> list:
    items = []
    idx = 0
    while True:
        idx = data.find(ITEM_HEADER, idx)
        if idx == -1:
            break
        
        item_index = struct.unpack('<H', data[idx+3:idx+5])[0]
        path_length = data[idx + 7]
        path = data[idx + 8:idx + 8 + path_length].decode('ascii')
        
        if '\\' in path:  # Valid item path
            id_offset = idx + 8 + path_length + 1
            item_id = struct.unpack('<H', data[id_offset:id_offset+2])[0]
            count = find_item_count(data, item_id)
            items.append({'path': path, 'id': item_id, 'count': count})
        
        idx += 1
    return items
```

## Item Display Names

### Source: Game .item Files

Display names are extracted from the game's `.item` files located at:
```
<game_install>/data/rules/items/**/*.item
```

These files use the same packed format as save files (24-byte header + gzip).

### .item File Structure

Each `.item` file contains:
- Internal name (camelCase or lowercase): `throwingKnife`, `beartrap`
- Display name (with spaces, proper capitalization): `Throwing Knife`, `Bear Trap`
- Description text

### Implementation

The `use/item_names.py` module contains `ITEM_DISPLAY_NAMES` dictionary mapping:
```python
ITEM_DISPLAY_NAMES = {
    'throwingknife': 'Throwing Knife',
    'beartrap': 'Bear Trap',
    'fusioncell': 'Fusion Cell',
    'sclicell': 'Supercharged Lithium Cell',
    # ... 200+ mappings from game files
}
```

### Lookup Function
```python
from use.item_names import get_display_name

name = get_display_name('throwingknife')  # Returns 'Throwing Knife'
name = get_display_name('unknown')        # Returns None
```

### Fallback Pattern

For items not in the mapping, `_extract_item_display_name()` in `core.py` uses pattern-based conversion:
1. Replace underscores with spaces
2. Insert spaces before uppercase letters (camelCase)
3. Insert space before trailing numbers
4. Capitalize words, with acronyms (EMP, HE, SMG, etc.) staying uppercase

### Key Corrections from Game Files

| Internal Name | Actual Display Name | Notes |
|--------------|---------------------|-------|
| `waistpack` | Waist Pack | Different from "Utility Belt" (separate item) |
| `utilitybelt` | Utility Belt | Different from "Waist Pack" (both exist) |
| `barrel5` | 5mm Firearm Barrel | Not "5mm Barrel" - per wiki/game |
| `omnitool` | Omni-Tool | Hyphenated per game files |
| `sclicell` | Supercharged Lithium Cell | |
| `fusioncell` | Fusion Cell | |
| `emfieldstabilizer` | Electromagnetic Field Stabilizer | |
| `animalheart` | Healthy Animal Heart | |
| `frag1` | Frag Grenade | Not "Frag 1" |
| `emp1` | EMP Grenade | |
| `he1` | HE Grenade | |

**Verified against**: [Underrail Wiki - Items](https://www.stygiansoftware.com/wiki/index.php?title=Items)

## Item Definition Files (.k)

The game's knowledge files are stored as `.k` files in:
```
<game_install>/data/knowledge/*.k
```

### File Format

Same format as save files:
- 24-byte header (16-byte GUID + 8-byte version)
- gzip-compressed data

### Content Structure

Contains item descriptions (not display names):
```
KI:S:Count -> number of entries
KI:S:N:Key -> internal item name (e.g., "psibooster")
KI:S:N:Value -> item description (e.g., "Immediately restores {0} psi.")
```

Note: Display names come from `.item` files, not `.k` files.

### Known Exceptions

Some items have display names that differ from the pattern:
- `waistpack` → "Utility Belt" (not "Waist Pack")
- `fusioncell` → Unknown (might be "Plasma Cell" in-game)
- `sclicell` → Unknown (Small Caliber Li Cell?)

### Available Definition Files

Located in `items/` directory:
- `ammo.k` - Ammunition types
- `armors.k` - Armor items
- `consumables.k` - Medical items, boosters
- `food.k` - Food items
- `grenades.k` - (in mods.k) Grenade types
- `repairkits.k` - Repair kit types
- `utilities.k` - Tools and utility items
- `weapons.k` - Weapon types

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
- `find_inventory_items(data)` - find all inventory items with counts
- `get_inventory_summary(data)` - get grouped/merged inventory summary
- `find_equipped_items(data)` - find equipped items (character gear, utility slots, hotbar)
- `get_equipment_summary(data)` - get equipment summary with categories
- `_extract_item_display_name(path)` - convert internal name to display name

### use/item_names.py
Item display name mappings extracted from game `.item` files:
- `ITEM_DISPLAY_NAMES` - dictionary of internal_name -> display_name (200+ entries)
- `get_display_name(internal_name)` - lookup display name (returns None if not found)
- `has_display_name(internal_name)` - check if mapping exists

### use/viewer.py
Read-only viewer module. Displays character name, game version, DLC detection,
XP, currency, base attributes, skills (grouped by category), feats, and inventory
(items grouped by category with stack counts).

### use/editor.py
Interactive editor module. Allows editing base attributes and skill point allocations.
Creates backups before saving.

### use/main_screen.py
Console menu interface. Provides commands: load, unload, view, equip/equipped, edit, help, quit.

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

**Inventory (Level 10, selected items):**

| Item | Count | Notes |
|------|-------|-------|
| Throwing Knife | 55 (25+30) | Two stacks in inventory |
| Bear Trap | 14 | Single stack |
| Fishing Rod | 1 | |
| Rubber Sole | 1 | |
| Plasma Core | 2 (1+1) | Two separate items |
| Waist Pack | 1 | Internal: armor\waistPack |
| Health Hypo | 13 | |
| Bandage | 19 | |
| Lockpick | 39 | |
| Metal Scraps | 20 | |
| Electronic Scraps | 19 | |
| Fabric Scraps | 21 | |

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

**Equipped Items (Level 10):**

| Slot Type | Item | Category |
|-----------|------|----------|
| Character Gear | Waist Pack | Armor (belt) |
| Character Gear | Frag Grenade Mk II | Grenades (utility) |
| Character Gear | Molotov Cocktail | Grenades (utility) |
| Character Gear | Jackknife | Weapons |
| Utility Slots | Bear Trap | Traps |
| Utility Slots | Burrower Poison Bear Trap | Traps |
| Utility Slots | Midazolam | Components |
| Hotbar | Lockpick Mk III | Devices |
| Hotbar | Hotwiring Kit | Devices |

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
