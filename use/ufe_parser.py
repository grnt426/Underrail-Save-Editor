#!/usr/bin/env python3
"""
UFE (Underrail File Exporter) wrapper for parsing save files.

This module handles:
- Running UFE.exe to export save files to JSON
- Parsing the resulting JSON into Python data structures
- Building a reference map for resolving object references
"""

import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Any, Optional


# Path to UFE executable (relative to project root)
UFE_PATH = Path(__file__).parent.parent / "UFE" / "UFE.exe"


class UFEError(Exception):
    """Exception raised when UFE fails to parse a file."""
    pass


def export_to_json(save_path: Path, output_path: Optional[Path] = None) -> Path:
    """
    Run UFE to export a save file to JSON.
    
    Args:
        save_path: Path to the save file (e.g., global.dat)
        output_path: Optional path for JSON output. If None, uses save_path + ".json"
    
    Returns:
        Path to the generated JSON file
        
    Raises:
        UFEError: If UFE fails to export the file
        FileNotFoundError: If UFE.exe or save file doesn't exist
    """
    if not UFE_PATH.exists():
        raise FileNotFoundError(f"UFE.exe not found at {UFE_PATH}")
    
    save_path = Path(save_path).resolve()
    if not save_path.exists():
        raise FileNotFoundError(f"Save file not found: {save_path}")
    
    # Default output path is save_path + ".json"
    if output_path is None:
        output_path = save_path.with_suffix(save_path.suffix + ".json")
    
    # Run UFE
    result = subprocess.run(
        [str(UFE_PATH), "-e", str(save_path)],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    # Check for errors
    if result.returncode != 0:
        raise UFEError(f"UFE failed with code {result.returncode}: {result.stderr}")
    
    # Verify output file was created
    if not output_path.exists():
        raise UFEError(f"UFE did not create output file: {output_path}")
    
    return output_path


def load_json(json_path: Path) -> dict:
    """Load and parse a JSON file exported by UFE."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


class SaveData:
    """
    Parsed save file data with easy access to game objects.
    
    The UFE JSON format uses object references ({"reference": id}) to link
    objects together. This class builds a reference map for easy lookup.
    """
    
    def __init__(self, json_data: dict):
        self._raw = json_data
        self._records = json_data.get('records', [])
        self._ref_map = {}  # id -> record
        self._build_ref_map()
    
    def _build_ref_map(self):
        """Build a map of object IDs to their records."""
        for record in self._records:
            # Records can have 'class' or 'class_id' at the top level
            if 'class' in record:
                obj_id = record['class'].get('id')
                if obj_id is not None:
                    self._ref_map[obj_id] = record['class']
            elif 'class_id' in record:
                obj_id = record['class_id'].get('id')
                if obj_id is not None:
                    self._ref_map[obj_id] = record['class_id']
            # Handle array records
            elif 'array_id' in record:
                self._ref_map[record['array_id']] = record
    
    def get_by_id(self, obj_id: int) -> Optional[dict]:
        """Get a record by its object ID."""
        return self._ref_map.get(obj_id)
    
    def resolve_ref(self, ref: dict) -> Optional[dict]:
        """Resolve a reference object to its target."""
        if isinstance(ref, dict) and 'reference' in ref:
            return self.get_by_id(ref['reference'])
        return None
    
    def get_member(self, obj: dict, key: str) -> Any:
        """Get a member value from an object, resolving references if needed."""
        if obj is None:
            return None
        members = obj.get('members', {})
        value = members.get(key)
        
        # If it's a reference, resolve it
        if isinstance(value, dict) and 'reference' in value:
            return self.resolve_ref(value)
        
        # If it's an inline value (e.g., obj_string_id), extract value
        if isinstance(value, dict) and 'value' in value:
            return value['value']
        
        # If it's an enum (class with value__), extract the value
        if isinstance(value, dict):
            if 'class' in value and 'members' in value['class']:
                return value['class']['members'].get('value__')
            if 'class_id' in value and 'members' in value['class_id']:
                return value['class_id']['members'].get('value__')
        
        return value
    
    def get_root(self) -> Optional[dict]:
        """Get the root TG (The Game) object."""
        for record in self._records:
            if 'class' in record and record['class'].get('name') == 'TG':
                return record['class']
        return None
    
    def get_player(self) -> Optional[dict]:
        """Get the player character (P2) object."""
        root = self.get_root()
        if root:
            return self.get_member(root, 'TG:PC')
        return None
    
    def get_game_version(self) -> Optional[tuple]:
        """Get the game version from the first System.Version record."""
        for record in self._records:
            obj = record.get('class') or record.get('class_id')
            if obj and obj.get('name') == 'System.Version':
                members = obj.get('members', {})
                return (
                    members.get('_Major', 0),
                    members.get('_Minor', 0),
                    members.get('_Build', 0),
                    members.get('_Revision', 0)
                )
        return None
    
    # === Character Info ===
    
    def get_character_name(self) -> Optional[str]:
        """Get the character name."""
        player = self.get_player()
        return self.get_member(player, 'C1:N') if player else None
    
    def get_character_level(self) -> Optional[int]:
        """Get the character level."""
        player = self.get_player()
        return self.get_member(player, 'C1:L') if player else None
    
    # === Base Attributes ===
    
    def get_base_attributes(self) -> list:
        """
        Get all base attributes (Strength, Dexterity, etc.).
        
        Returns list of dicts with 'name', 'base', 'effective' keys.
        """
        player = self.get_player()
        if not player:
            return []
        
        # Get the base attributes container (BA3)
        ba_container = self.get_member(player, 'C1:BA')
        if not ba_container:
            return []
        
        # Get count and iterate
        count = self.get_member(ba_container, 'BA3:BA:Count')
        if not count:
            return []
        
        attributes = []
        for i in range(count):
            attr_ref = self.get_member(ba_container, f'BA3:BA:{i}')
            if attr_ref:
                name = self.get_member(attr_ref, 'BA2:N')
                base = self.get_member(attr_ref, 'S4:V')
                effective = self.get_member(attr_ref, 'S4:MV')
                
                if name is not None:
                    attributes.append({
                        'name': name,
                        'base': base or 0,
                        'effective': effective or 0
                    })
        
        return attributes
    
    # === Skills ===
    
    def get_skills(self) -> list:
        """
        Get all skills.
        
        Returns list of dicts with 'name', 'base', 'effective', 'category' keys.
        Note: Skill names aren't stored in save - we use skill categories to match names.
        """
        player = self.get_player()
        if not player:
            return []
        
        # Get the skills container (DSS)
        skills_container = self.get_member(player, 'C1:S')
        if not skills_container:
            return []
        
        count = self.get_member(skills_container, 'S3:S:Count')
        if not count:
            return []
        
        skills = []
        for i in range(count):
            skill_ref = self.get_member(skills_container, f'S3:S:{i}')
            if skill_ref:
                base = self.get_member(skill_ref, 'S4:V')
                effective = self.get_member(skill_ref, 'S4:MV')
                category = self.get_member(skill_ref, 'S5:C')
                
                skills.append({
                    'base': base or 0,
                    'effective': effective or 0,
                    'category': category
                })
        
        return skills
    
    # === Feats ===
    
    def get_feats(self) -> list:
        """
        Get all feats.
        
        Returns list of dicts with 'internal' (internal name) key.
        """
        player = self.get_player()
        if not player:
            return []
        
        # Get the feats container (F)
        feats_container = self.get_member(player, 'C1:F')
        if not feats_container:
            return []
        
        count = self.get_member(feats_container, 'F:F:Count')
        if not count:
            return []
        
        feats = []
        for i in range(count):
            feat_ref = self.get_member(feats_container, f'F:F:{i}')
            if feat_ref:
                internal_name = self.get_member(feat_ref, 'FR:FTN')
                if internal_name:
                    feats.append({
                        'internal': internal_name
                    })
        
        return feats
    
    # === Inventory and Items ===
    
    def get_all_items(self) -> list:
        """
        Get all items from the save file.
        
        Returns list of dicts with item properties.
        """
        items = []
        
        for record in self._records:
            obj = record.get('class') or record.get('class_id')
            if not obj:
                continue
            
            members = obj.get('members')
            if not members:
                continue
            
            # Check for item definition (has I:N for name)
            if 'I:N' in members:
                name_field = members['I:N']
                if isinstance(name_field, dict) and 'value' in name_field:
                    item = self._parse_item(obj)
                    if item:
                        items.append(item)
        
        return items
    
    def _parse_item(self, obj: dict) -> Optional[dict]:
        """Parse an item object into a dictionary."""
        members = obj.get('members')
        if not members:
            return None
        
        # Get name
        name_field = members.get('I:N', {})
        name = name_field.get('value') if isinstance(name_field, dict) else None
        if not name:
            return None
        
        # Get basic properties
        item = {
            'id': obj.get('id'),
            'name': name,
            'value': members.get('I:CV'),
            'weight': members.get('I:W'),
            'level': members.get('I:L'),
            'max_battery': members.get('I:MB'),
            'craftable': members.get('I:CR', False),
        }
        
        # Get description
        desc_field = members.get('I:D', {})
        if isinstance(desc_field, dict) and 'value' in desc_field:
            item['description'] = desc_field['value']
        
        # Weapon stats (if applicable)
        if 'WI:AP' in members:
            item['weapon'] = {
                'ap_cost': members.get('WI:AP'),
                'crit_chance': members.get('WI:CSC'),
                'crit_damage': members.get('WI:CDB'),
                'speed': members.get('WI:S'),
            }
            
            # Damage range
            damage_field = members.get('WI:D:0')
            if isinstance(damage_field, dict):
                dmg_class = damage_field.get('class_id') or damage_field.get('class')
                if dmg_class:
                    dmg_members = dmg_class.get('members', {})
                    item['weapon']['damage_min'] = dmg_members.get('L')
                    item['weapon']['damage_max'] = dmg_members.get('U')
        
        return item
    
    def get_inventory_items(self) -> list:
        """
        Get inventory items (items with paths like 'grenades\\flashbang').
        
        These are stored in LIDP (List Item Data Provider) records.
        """
        items = []
        item_instances = {}  # path -> instance data
        
        # First pass: collect item instances (II records) with their data
        for record in self._records:
            obj = record.get('class') or record.get('class_id')
            if not obj:
                continue
            
            members = obj.get('members')
            if not members:
                continue
            
            # Item instances have II:S (stack count) and II:DP (data provider reference)
            if 'II:S' in members and 'II:DP' in members:
                dp_ref = members['II:DP']
                if isinstance(dp_ref, dict) and 'reference' in dp_ref:
                    dp_id = dp_ref['reference']
                    instance = {
                        'count': members.get('II:S', 1),
                        'durability': members.get('II:D', 0),
                        'battery': members.get('II:B', 0),
                        'dp_id': dp_id
                    }
                    item_instances[dp_id] = instance
        
        # Second pass: collect LIDP records (inventory items with paths)
        for record in self._records:
            obj = record.get('class') or record.get('class_id')
            if not obj:
                continue
            
            name = obj.get('name', '')
            # LIDP records have names like "LIDP#G1>C00#-"
            if not name or not name.startswith('LIDP'):
                continue
            
            members = obj.get('members')
            if not members:
                continue
            
            path_field = members.get('LIDP:P', {})
            
            if isinstance(path_field, dict) and 'value' in path_field:
                path = path_field['value']
                obj_id = obj.get('id')
                
                # Parse path to get category and item name
                if '\\' in path:
                    parts = path.split('\\')
                    category = parts[0]
                    item_name = parts[-1]
                    
                    # Get instance data if available
                    instance = item_instances.get(obj_id, {})
                    
                    items.append({
                        'path': path,
                        'category': category,
                        'name': item_name,
                        'count': instance.get('count', 1),
                        'durability': instance.get('durability', 0),
                        'battery': instance.get('battery', 0),
                        'id': obj_id
                    })
        
        return items
    
    def get_crafted_items(self) -> list:
        """
        Get crafted/unique items (items with display names like 'Pneumatic Bladed Tungsten Steel Gloves').
        
        These are full item objects with I:N (name) field.
        """
        return self.get_all_items()


def parse_save(save_path: Path, keep_json: bool = False) -> SaveData:
    """
    Parse a save file and return structured data.
    
    Args:
        save_path: Path to the save file
        keep_json: If True, keep the JSON file; if False, delete it after parsing
    
    Returns:
        SaveData object with parsed game data
    """
    json_path = export_to_json(save_path)
    
    try:
        json_data = load_json(json_path)
        return SaveData(json_data)
    finally:
        if not keep_json and json_path.exists():
            json_path.unlink()
