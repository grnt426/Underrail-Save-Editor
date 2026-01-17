#!/usr/bin/env python3
"""
End-to-end tests for USE (Underrail Save Editor) using real save files.

Tests validate:
- Save files can be loaded via UFE parser
- Skill data is correctly parsed from actual game saves
- Character info, attributes, and equipment are parsed correctly
- 40 skill points difference between level 9 and level 10
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from use.core import (
    load_save_data,
    get_skill_entries,
    get_skill_names,
    find_character_name,
    find_character_level,
    get_stat_entries,
    find_feats,
    find_currency,
    find_inventory_items,
    get_inventory_summary,
    get_equipment_summary,
    clear_cache,
)
from use.ufe_parser import SaveData


# Fixture paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
LEVEL_9_SAVE = FIXTURES_DIR / "see_me_now" / "level_9" / "global.dat"
LEVEL_10_SAVE = FIXTURES_DIR / "see_me_now" / "level_10" / "global.dat"
LEVEL_11_SAVE = FIXTURES_DIR / "see_me_now" / "level_11" / "global.dat"
GRANITE_SAVE = FIXTURES_DIR / "granite" / "level_1" / "global.dat"


class TestSaveFileLoading(unittest.TestCase):
    """Tests for loading and parsing save files via UFE."""
    
    @classmethod
    def setUpClass(cls):
        """Clear cache before tests."""
        clear_cache()
    
    def test_level_9_file_exists(self):
        """Level 9 save file should exist."""
        self.assertTrue(LEVEL_9_SAVE.exists())
    
    def test_level_10_file_exists(self):
        """Level 10 save file should exist."""
        self.assertTrue(LEVEL_10_SAVE.exists())
    
    def test_level_11_file_exists(self):
        """Level 11 save file should exist."""
        self.assertTrue(LEVEL_11_SAVE.exists())
    
    def test_level_9_loads_successfully(self):
        """Level 9 save should load via UFE parser."""
        save_data = load_save_data(LEVEL_9_SAVE)
        self.assertIsInstance(save_data, SaveData)
    
    def test_level_10_loads_successfully(self):
        """Level 10 save should load via UFE parser."""
        save_data = load_save_data(LEVEL_10_SAVE)
        self.assertIsInstance(save_data, SaveData)
    
    def test_level_11_loads_successfully(self):
        """Level 11 save should load via UFE parser."""
        save_data = load_save_data(LEVEL_11_SAVE)
        self.assertIsInstance(save_data, SaveData)


class TestCharacterInfo(unittest.TestCase):
    """Tests for character info parsing."""
    
    @classmethod
    def setUpClass(cls):
        """Load save data."""
        clear_cache()
        cls.level_9 = load_save_data(LEVEL_9_SAVE)
        cls.level_11 = load_save_data(LEVEL_11_SAVE)
    
    def test_character_name_level_9(self):
        """Level 9 character name should be 'See Me Now'."""
        name = find_character_name(self.level_9)
        self.assertEqual(name, "See Me Now")
    
    def test_character_name_level_11(self):
        """Level 11 character name should be 'See Me Now'."""
        name = find_character_name(self.level_11)
        self.assertEqual(name, "See Me Now")
    
    def test_character_level_9(self):
        """Level 9 save should report level 9."""
        level = find_character_level(self.level_9)
        self.assertEqual(level, 9)
    
    def test_character_level_11(self):
        """Level 11 save should report level 11."""
        level = find_character_level(self.level_11)
        self.assertEqual(level, 11)


class TestBaseAttributes(unittest.TestCase):
    """Tests for base attribute parsing."""
    
    @classmethod
    def setUpClass(cls):
        """Load save data."""
        clear_cache()
        cls.level_9 = load_save_data(LEVEL_9_SAVE)
    
    def test_has_7_attributes(self):
        """Should have 7 base attributes."""
        attrs = get_stat_entries(self.level_9)
        self.assertEqual(len(attrs), 7)
    
    def test_attribute_names(self):
        """Attributes should have expected names."""
        attrs = get_stat_entries(self.level_9)
        names = [a['name'] for a in attrs]
        self.assertIn('Strength', names)
        self.assertIn('Intelligence', names)
    
    def test_attribute_values_reasonable(self):
        """Attribute values should be within game limits."""
        attrs = get_stat_entries(self.level_9)
        for attr in attrs:
            self.assertGreaterEqual(attr['base'], 3)  # Minimum base stat
            self.assertLessEqual(attr['base'], 18)    # Maximum starting stat
            self.assertGreaterEqual(attr['effective'], 1)
            self.assertLessEqual(attr['effective'], 50)


class TestSkillParsing(unittest.TestCase):
    """Tests for parsing skills from real save files."""
    
    @classmethod
    def setUpClass(cls):
        """Load and parse save files."""
        clear_cache()
        cls.level_9 = load_save_data(LEVEL_9_SAVE)
        cls.level_10 = load_save_data(LEVEL_10_SAVE)
        
        cls.level_9_skills = get_skill_entries(cls.level_9)
        cls.level_10_skills = get_skill_entries(cls.level_10)
    
    def test_level_9_has_skills(self):
        """Level 9 save should have skill entries."""
        self.assertGreater(len(self.level_9_skills), 0)
    
    def test_level_10_has_skills(self):
        """Level 10 save should have skill entries."""
        self.assertGreater(len(self.level_10_skills), 0)
    
    def test_same_skill_count(self):
        """Both saves should have the same number of skills."""
        self.assertEqual(len(self.level_9_skills), len(self.level_10_skills))
    
    def test_has_expected_skill_count(self):
        """Should have 23 (base) or 24 (DLC) skills."""
        count = len(self.level_9_skills)
        self.assertIn(count, [23, 24], 
                      f"Expected 23 or 24 skills, got {count}")
    
    def test_skill_values_are_reasonable(self):
        """All skill values should be within game limits."""
        for skill in self.level_9_skills + self.level_10_skills:
            self.assertGreaterEqual(skill['base'], 0)
            self.assertLessEqual(skill['base'], 300)
            self.assertGreaterEqual(skill['mod'], 0)
            self.assertLessEqual(skill['mod'], 600)


class TestSkillPointProgression(unittest.TestCase):
    """Tests for skill point allocation between levels."""
    
    @classmethod
    def setUpClass(cls):
        """Load and calculate total skill points for both saves."""
        clear_cache()
        cls.level_9 = load_save_data(LEVEL_9_SAVE)
        cls.level_10 = load_save_data(LEVEL_10_SAVE)
        
        cls.level_9_skills = get_skill_entries(cls.level_9)
        cls.level_10_skills = get_skill_entries(cls.level_10)
        
        cls.level_9_total = sum(s['base'] for s in cls.level_9_skills)
        cls.level_10_total = sum(s['base'] for s in cls.level_10_skills)
        cls.point_difference = cls.level_10_total - cls.level_9_total
    
    def test_level_10_has_more_points(self):
        """Level 10 should have more skill points than level 9."""
        self.assertGreater(self.level_10_total, self.level_9_total)
    
    def test_exactly_40_point_difference(self):
        """Level 10 should have exactly 40 more skill points than level 9.
        
        Game mechanic: Each level grants 40 skill points.
        """
        self.assertEqual(self.point_difference, 40,
                         f"Expected 40 point difference, got {self.point_difference}")
    
    def test_level_9_total_within_expected_range(self):
        """Level 9 total should be within expected range.
        
        Maximum at level 9: 120 + (40 * 9) = 480 points
        """
        max_points = 120 + (40 * 9)  # 480
        self.assertLessEqual(self.level_9_total, max_points)
        self.assertGreater(self.level_9_total, 0)


class TestSkillDetails(unittest.TestCase):
    """Detailed tests for specific skill values from known save."""
    
    @classmethod
    def setUpClass(cls):
        """Load level 9 save and parse skills with names."""
        clear_cache()
        cls.level_9 = load_save_data(LEVEL_9_SAVE)
        cls.skills = get_skill_entries(cls.level_9)
        
        # Build dict for easy lookup
        cls.skill_dict = {skill['name']: skill for skill in cls.skills}
    
    def test_melee_skill_present(self):
        """Melee skill should be present in save."""
        self.assertIn("Melee", self.skill_dict)
    
    def test_melee_has_expected_values(self):
        """Melee should have expected values (base=55, effective=83)."""
        melee = self.skill_dict.get("Melee")
        if melee:
            self.assertEqual(melee['base'], 55, 
                           f"Expected Melee base=55, got {melee['base']}")
            self.assertEqual(melee['mod'], 83,
                           f"Expected Melee effective=83, got {melee['mod']}")
    
    def test_dodge_has_expected_values(self):
        """Dodge should have expected values (base=55, effective=78)."""
        dodge = self.skill_dict.get("Dodge")
        if dodge:
            self.assertEqual(dodge['base'], 55)
            self.assertEqual(dodge['mod'], 78)


class TestFeatParsing(unittest.TestCase):
    """Tests for feat parsing."""
    
    @classmethod
    def setUpClass(cls):
        """Load save data."""
        clear_cache()
        cls.level_11 = load_save_data(LEVEL_11_SAVE)
    
    def test_has_feats(self):
        """Level 11 should have feats."""
        feats = find_feats(self.level_11)
        self.assertGreater(len(feats), 0)
    
    def test_feat_structure(self):
        """Feats should have expected structure."""
        feats = find_feats(self.level_11)
        if feats:
            feat = feats[0]
            self.assertIn('name', feat)
            self.assertIn('internal', feat)


class TestInventoryParsing(unittest.TestCase):
    """Tests for inventory parsing."""
    
    @classmethod
    def setUpClass(cls):
        """Load save data."""
        clear_cache()
        cls.level_11 = load_save_data(LEVEL_11_SAVE)
    
    def test_has_inventory_items(self):
        """Level 11 should have inventory items."""
        items = find_inventory_items(self.level_11)
        self.assertGreater(len(items), 0)
    
    def test_inventory_item_structure(self):
        """Inventory items should have expected structure."""
        items = find_inventory_items(self.level_11)
        if items:
            item = items[0]
            self.assertIn('path', item)
            self.assertIn('name', item)
            self.assertIn('category', item)
            self.assertIn('count', item)
    
    def test_inventory_summary(self):
        """Inventory summary should have expected structure."""
        summary = get_inventory_summary(self.level_11)
        self.assertIn('items', summary)
        self.assertIn('by_category', summary)
        self.assertIn('total_items', summary)
        self.assertIn('total_stacks', summary)


class TestEquipmentParsing(unittest.TestCase):
    """Tests for equipment parsing on real saves."""
    
    @classmethod
    def setUpClass(cls):
        """Load test saves."""
        clear_cache()
        cls.level_10 = load_save_data(LEVEL_10_SAVE)
        cls.level_11 = load_save_data(LEVEL_11_SAVE)
        cls.granite = load_save_data(GRANITE_SAVE)
    
    def test_level_11_has_character_gear(self):
        """Level 11 save should have crafted character gear equipped."""
        equipment = get_equipment_summary(self.level_11)
        # Level 11 has crafted armor, boots, gloves, etc.
        self.assertGreater(len(equipment['character_gear']), 0)
    
    def test_level_11_has_utility_slots(self):
        """Level 11 save should have utility belt items."""
        equipment = get_equipment_summary(self.level_11)
        # Level 11 has grenades on utility belt
        self.assertGreater(len(equipment['utility_slots']), 0)
    
    def test_granite_equipment_structure(self):
        """Granite (level 1) equipment parsing should work."""
        equipment = get_equipment_summary(self.granite)
        # Just verify the structure is correct
        self.assertIn('character_gear', equipment)
        self.assertIn('utility_slots', equipment)
        self.assertIn('hotbar', equipment)
        self.assertIn('total_equipped', equipment)
    
    def test_equipment_item_structure(self):
        """Equipped items should have expected structure."""
        equipment = get_equipment_summary(self.level_11)
        
        # Check character gear item (level 11 has crafted items)
        if equipment['character_gear']:
            item = equipment['character_gear'][0]
            self.assertIn('path', item)
            self.assertIn('name', item)
            self.assertIn('category', item)
            self.assertIn('id', item)
    
    def test_equipment_categories_are_valid(self):
        """All equipped items should have valid categories."""
        equipment = get_equipment_summary(self.level_11)
        
        # Categories for worn gear and utility belt items
        valid_categories = {'Armor', 'Boots', 'Gloves', 'Head', 'Shield',
                           'Weapons', 'Devices', 'Grenades', 'Traps', 
                           'Components', 'Consumables', 'Expendables', 'Ammo'}
        
        all_items = (equipment['character_gear'] + 
                    equipment['utility_slots'] + 
                    equipment['hotbar'])
        
        for item in all_items:
            self.assertIn(item['category'], valid_categories,
                         f"Item '{item['name']}' has unexpected category '{item['category']}'")


if __name__ == '__main__':
    unittest.main()
