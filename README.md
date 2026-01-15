# USE - Underrail Save Editor

A Python tool for viewing and editing Underrail save files. View character stats, skills, feats, XP, and currency, or edit skill point allocations and base attributes.

## Quick Start

### Windows (PowerShell - recommended)

```powershell
.\run.ps1
```

### Windows (Command Prompt)

```batch
run.bat
```

### Linux/macOS

```bash
chmod +x run.sh
./run.sh
```

## Requirements

- Python 3.6 or higher
- No additional packages required (uses only standard library)

## Installation

1. Download/clone the repository
2. Copy the `use/` folder and the appropriate launcher:
   - Windows: `run.ps1` (PowerShell) or `run.bat` (CMD)
   - Unix/Linux/macOS: `run.sh`
3. Run the script from your Underrail save folder, or run it and specify a path

## Usage

The main console provides three commands:

### View Character Data

```
use> view
```

Displays:
- Character name, level, and game version
- DLC detection (Expedition)
- XP system (Oddity/Classic) with current progress
- Currency (Stygian Coins, SGS Credits)
- All 7 base attributes with effective values
- All 23-24 skills grouped by category
- Detected feats

You can also specify a path: `view path/to/global.dat`

### Edit Save File

```
use> edit
```

Interactive editor for:
- Base attributes (Strength, Dexterity, etc.)
- All skill point allocations

Features:
- Auto-detects character level from `info.dat`
- Warns when exceeding skill caps
- Creates backup (`global.dat.OLD`) before saving
- Preserves effective value bonuses from gear/feats

### Help

```
use> help
```

### Exit

```
use> quit
```
(Also accepts: `exit`, `done`, `q`)

## Example Output (Viewer)

```
============================================================
UNDERRAIL CHARACTER DATA
============================================================
Save file: global.dat
Character: See Me Now
Game version: 1.3.0.17
DLC detected: Expedition
Level: 10
Experience: 1 / ~22 (Oddity XP)

CURRENCY
----------------------------------------
  Stygian Coins:    1,636
  SGS Credits:      32

BASE ATTRIBUTES
----------------------------------------
  Strength            6
  Dexterity          10
  Agility             8  (9)
  Constitution        5
  Perception          7
  Will                3
  Intelligence        3

SKILLS
----------------------------------------
  Offense:
    Guns                         0
    Heavy Guns                   0
    Throwing                    20  (30)
    Crossbows                    0
    Melee                       60  (88)
  ...
```

## File Structure

```
Underrail Character Editor/
├── run.ps1              # Windows launcher (PowerShell)
├── run.bat              # Windows launcher (CMD)
├── run.sh               # Unix launcher
├── use/                 # Python package
│   ├── __init__.py
│   ├── core.py          # Shared save file processing
│   ├── viewer.py        # Character data viewer
│   ├── editor.py        # Save file editor
│   └── main_screen.py   # Console menu interface
├── tests/               # Unit and e2e tests
└── README.md
```

## Skill List

The tool automatically detects whether you have the Expedition DLC based on the number of skills in your save file.

### Base Game (23 skills)

| # | Skill | Category |
|---|-------|----------|
| 1-5 | Guns, Heavy Guns, Throwing, Crossbows, Melee | Offense |
| 6-7 | Dodge, Evasion | Defense |
| 8-12 | Stealth, Hacking, Lockpicking, Pickpocketing, Traps | Subterfuge |
| 13-17 | Mechanics, Electronics, Chemistry, Biology, Tailoring | Technology |
| 18-20 | Thought Control, Psychokinesis, Metathermics | Psi |
| 21-23 | Persuasion, Intimidation, Mercantile | Social |

### With Expedition DLC (24 skills)

Same as above, but **Temporal Manipulation** is added at position 21 (Psi category), shifting Social skills to positions 22-24.

## Restoring Original Save

If something goes wrong, rename `global.dat.OLD` back to `global.dat`.

## Notes

- The "Effective" value includes bonuses from gear, feats, etc.
- The game recalculates effective values when loading
- Always back up your saves before editing!

## Running Tests

```bash
python -m pytest tests/ -v
```
