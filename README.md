# Underrail Skill Editor

A Python script to edit skill point allocations in Underrail save files.

## Requirements

- Python 3.6 or higher
- No additional packages required (uses only standard library)

## Usage

1. **Copy the script** to your save folder, or navigate to the folder containing it.

2. **Run the script**:
   ```
   python skill_editor.py
   ```

3. **The script will automatically**:
   - Find your save file (`global.dat` or `global/global`)
   - Detect your character name and level from `info.dat`
   - Detect if you have the Expedition DLC (adds Temporal Manipulation skill)
   - Display all skills with current values

4. **Edit skills interactively**:
   - For each skill, enter a new base value or press **Enter** to keep the current value
   - The script warns if you exceed the per-skill maximum for your level
   - After all skills, it warns if total points exceed your available pool

5. **Save changes**:
   - Original save is backed up to `global.dat.OLD`
   - New save is written to `global.dat`

## Example Output

```
Underrail Save File Skill Editor
============================================================

Found unpacked file: 'global/global'
Character: See Me Now
Auto-detected level: 9

At level 9:
  - Maximum points per skill: 55
  - Total available skill points: 480

Found 24 skill entries
  (Expedition DLC detected - Temporal Manipulation skill present)

============================================================
Current Skill Values
============================================================
#   Skill Name                Base  Effective
------------------------------------------------------------
1   Guns                         0          0
2   Heavy Guns                   0          0
3   Throwing                    20         30
4   Crossbows                    0          0
5   Melee                       55         83
6   Dodge                       55         78
7   Evasion                     55         78
...
11  Pickpocketing               30         45
...
```

## Skill List

The script automatically detects whether you have the Expedition DLC based on the number of skills in your save file.

### Base Game (23 skills)

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

### With Expedition DLC (24 skills)

Same as above, but **Temporal Manipulation** is added at position 21, shifting Social skills to positions 22-24.

| # | Skill | Category |
|---|-------|----------|
| ... | (1-20 same as above) | |
| 21 | Temporal Manipulation | Psi (DLC) |
| 22 | Persuasion | Social |
| 23 | Intimidation | Social |
| 24 | Mercantile | Social |

## Restoring Original Save

If something goes wrong, rename `global.dat.OLD` back to `global.dat`.

## Notes

- The "Effective" value includes bonuses from gear, feats, etc.
- The game recalculates effective values when loading, so changes to base values will be reflected properly.
- Always back up your saves before editing!
