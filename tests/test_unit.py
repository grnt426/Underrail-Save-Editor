#!/usr/bin/env python3
"""
Unit tests for USE (Underrail Save Editor) core functions.

These tests verify the UFE-based parser and core functionality.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from use.core import (
    get_skill_names,
    calculate_xp_needed,
    _extract_item_display_name,
    SKILL_NAMES_BASE,
    SKILL_NAMES_DLC,
    STAT_NAMES,
    FEAT_DISPLAY_NAMES,
    ITEM_CATEGORIES,
)


class TestSkillNameLists(unittest.TestCase):
    """Tests for skill name list functions."""
    
    def test_base_game_has_23_skills(self):
        """Base game should have 23 skills."""
        self.assertEqual(len(SKILL_NAMES_BASE), 23)
    
    def test_dlc_has_24_skills(self):
        """DLC version should have 24 skills."""
        self.assertEqual(len(SKILL_NAMES_DLC), 24)
    
    def test_get_skill_names_base(self):
        """get_skill_names should return base list for < 24 skills."""
        names = get_skill_names(23)
        self.assertEqual(names, SKILL_NAMES_BASE)
        self.assertEqual(len(names), 23)
    
    def test_get_skill_names_dlc(self):
        """get_skill_names should return DLC list for >= 24 skills."""
        names = get_skill_names(24)
        self.assertEqual(names, SKILL_NAMES_DLC)
        self.assertEqual(len(names), 24)
    
    def test_temporal_manipulation_in_dlc(self):
        """Temporal Manipulation should be in DLC skill list."""
        self.assertIn("Temporal Manipulation", SKILL_NAMES_DLC)
        self.assertNotIn("Temporal Manipulation", SKILL_NAMES_BASE)
    
    def test_temporal_manipulation_position(self):
        """Temporal Manipulation should be at index 20 (position 21)."""
        self.assertEqual(SKILL_NAMES_DLC[20], "Temporal Manipulation")


class TestBaseStatOperations(unittest.TestCase):
    """Tests for base stat (attribute) functions."""
    
    def test_stat_names_has_7_entries(self):
        """Should have 7 base attributes."""
        self.assertEqual(len(STAT_NAMES), 7)
    
    def test_stat_names_order(self):
        """Stat names should be in correct order."""
        self.assertEqual(STAT_NAMES[0], 'Strength')
        self.assertEqual(STAT_NAMES[1], 'Dexterity')
        self.assertEqual(STAT_NAMES[2], 'Agility')
        self.assertEqual(STAT_NAMES[6], 'Intelligence')


class TestXPCalculation(unittest.TestCase):
    """Tests for XP-related functions."""
    
    # Oddity XP System tests (default)
    def test_oddity_xp_level_1(self):
        """Oddity: Level 1 should need 4 XP to reach level 2."""
        self.assertEqual(calculate_xp_needed(1, 'oddity'), 4)
    
    def test_oddity_xp_level_10(self):
        """Oddity: Level 10 should need 22 XP to reach level 11."""
        self.assertEqual(calculate_xp_needed(10, 'oddity'), 22)
    
    def test_oddity_xp_level_11(self):
        """Oddity: Level 11 should need 24 XP to reach level 12."""
        self.assertEqual(calculate_xp_needed(11, 'oddity'), 24)
    
    def test_oddity_xp_caps_at_30(self):
        """Oddity: XP needed caps at 30 for level 14+."""
        self.assertEqual(calculate_xp_needed(14, 'oddity'), 30)
        self.assertEqual(calculate_xp_needed(20, 'oddity'), 30)
        self.assertEqual(calculate_xp_needed(25, 'oddity'), 30)
    
    def test_oddity_is_default(self):
        """Oddity should be the default XP system."""
        self.assertEqual(calculate_xp_needed(1), calculate_xp_needed(1, 'oddity'))
        self.assertEqual(calculate_xp_needed(10), calculate_xp_needed(10, 'oddity'))
    
    # Classic XP System tests
    def test_classic_xp_level_1(self):
        """Classic: Level 1 should need 1000 XP to reach level 2."""
        self.assertEqual(calculate_xp_needed(1, 'classic'), 1000)
    
    def test_classic_xp_level_10(self):
        """Classic: Level 10 should need 10000 XP to reach level 11."""
        self.assertEqual(calculate_xp_needed(10, 'classic'), 10000)
    
    def test_classic_xp_higher_levels(self):
        """Classic: XP needed scales linearly with level * 1000."""
        self.assertEqual(calculate_xp_needed(20, 'classic'), 20000)
        self.assertEqual(calculate_xp_needed(25, 'classic'), 25000)


class TestFeatDisplayNames(unittest.TestCase):
    """Tests for feat display name mapping."""
    
    def test_single_letter_feats_mapped(self):
        """Single letter feats should have display names."""
        self.assertEqual(FEAT_DISPLAY_NAMES.get('o'), 'Opportunist')
    
    def test_two_letter_feats_mapped(self):
        """Two letter feats should have display names."""
        self.assertEqual(FEAT_DISPLAY_NAMES.get('pe'), 'Psi Empathy')
    
    def test_multiword_feats_mapped(self):
        """Multi-word feats should have proper display names."""
        self.assertEqual(FEAT_DISPLAY_NAMES.get('heavypunch'), 'Heavy Punch')
        self.assertEqual(FEAT_DISPLAY_NAMES.get('lightningpunches'), 'Lightning Punches')


class TestInventoryItemDisplayNames(unittest.TestCase):
    """Tests for item display name conversion."""
    
    def test_special_names_mapped(self):
        """Special item names should be mapped correctly from game files."""
        self.assertEqual(_extract_item_display_name('devices\\fishingrod'), 'Fishing Rod')
        self.assertEqual(_extract_item_display_name('traps\\beartrap'), 'Bear Trap')
        self.assertEqual(_extract_item_display_name('armor\\waistpack'), 'Waist Pack')
    
    def test_camelcase_conversion(self):
        """CamelCase names should be converted to Title Case with spaces."""
        self.assertEqual(_extract_item_display_name('components\\MetalScraps'), 'Metal Scraps')
    
    def test_case_insensitive_special_names(self):
        """Special names should be case insensitive."""
        self.assertEqual(_extract_item_display_name('Devices\\FishingRod'), 'Fishing Rod')
        self.assertEqual(_extract_item_display_name('TRAPS\\BEARTRAP'), 'Bear Trap')
    
    def test_currency_names(self):
        """Currency names should be properly formatted."""
        self.assertEqual(_extract_item_display_name('currency\\stygiancoin'), 'Stygian Coin')
        self.assertEqual(_extract_item_display_name('currency\\sgscredits'), 'SGS Credits')
    
    def test_ammo_names(self):
        """Ammo names should be properly formatted."""
        self.assertEqual(_extract_item_display_name('Ammo\\caliber_5_std'), 'Caliber 5 Std')
        self.assertEqual(_extract_item_display_name('Ammo\\bolt'), 'Bolt')


class TestInventoryCategories(unittest.TestCase):
    """Tests for item category mapping."""
    
    def test_common_categories_defined(self):
        """Common item categories should be defined."""
        self.assertIn('devices', ITEM_CATEGORIES)
        self.assertIn('weapons', ITEM_CATEGORIES)
        self.assertIn('consumables', ITEM_CATEGORIES)
        self.assertIn('grenades', ITEM_CATEGORIES)
        self.assertIn('traps', ITEM_CATEGORIES)
    
    def test_case_variations_mapped(self):
        """Category names should handle case variations."""
        self.assertEqual(ITEM_CATEGORIES.get('devices'), 'Devices')
        self.assertEqual(ITEM_CATEGORIES.get('Devices'), 'Devices')
        self.assertEqual(ITEM_CATEGORIES.get('weapons'), 'Weapons')
        self.assertEqual(ITEM_CATEGORIES.get('Weapons'), 'Weapons')
    
    def test_plot_category_mapped(self):
        """Plot items should map to Quest Items."""
        self.assertEqual(ITEM_CATEGORIES.get('plot'), 'Quest Items')


if __name__ == '__main__':
    unittest.main()
