#!/usr/bin/env python3
"""
End-to-end tests for skill_editor.py using real save files.

Tests validate:
- Both level 9 and level 10 saves can be read
- Skill data is correctly parsed from actual game saves
- 40 skill points difference between level 9 and level 10
- DLC detection works on real save files
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from skill_editor import (
    is_packed,
    unpack_data,
    pack_data,
    get_skill_names_from_data,
    get_skill_names,
)


# Fixture paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
LEVEL_9_SAVE = FIXTURES_DIR / "see_me_now" / "level_9" / "global.dat"
LEVEL_10_SAVE = FIXTURES_DIR / "see_me_now" / "level_10" / "global.dat"


class TestSaveFileLoading(unittest.TestCase):
    """Tests for loading and unpacking save files."""
    
    @classmethod
    def setUpClass(cls):
        """Load both save files once for all tests."""
        # Level 9
        with open(LEVEL_9_SAVE, 'rb') as f:
            cls.level_9_packed = f.read()
        cls.level_9_data = unpack_data(cls.level_9_packed)
        
        # Level 10
        with open(LEVEL_10_SAVE, 'rb') as f:
            cls.level_10_packed = f.read()
        cls.level_10_data = unpack_data(cls.level_10_packed)
    
    def test_level_9_file_exists(self):
        """Level 9 save file should exist."""
        self.assertTrue(LEVEL_9_SAVE.exists())
    
    def test_level_10_file_exists(self):
        """Level 10 save file should exist."""
        self.assertTrue(LEVEL_10_SAVE.exists())
    
    def test_level_9_is_packed(self):
        """Level 9 save should be detected as packed."""
        self.assertTrue(is_packed(self.level_9_packed))
    
    def test_level_10_is_packed(self):
        """Level 10 save should be detected as packed."""
        self.assertTrue(is_packed(self.level_10_packed))
    
    def test_level_9_unpacks_successfully(self):
        """Level 9 save should unpack to non-empty data."""
        self.assertGreater(len(self.level_9_data), 0)
    
    def test_level_10_unpacks_successfully(self):
        """Level 10 save should unpack to non-empty data."""
        self.assertGreater(len(self.level_10_data), 0)


class TestSkillParsing(unittest.TestCase):
    """Tests for parsing skills from real save files."""
    
    @classmethod
    def setUpClass(cls):
        """Load and parse both save files."""
        with open(LEVEL_9_SAVE, 'rb') as f:
            cls.level_9_data = unpack_data(f.read())
        with open(LEVEL_10_SAVE, 'rb') as f:
            cls.level_10_data = unpack_data(f.read())
        
        cls.level_9_skills = get_skill_names_from_data(cls.level_9_data)
        cls.level_10_skills = get_skill_names_from_data(cls.level_10_data)
    
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
    
    def test_dlc_detection_consistent(self):
        """DLC detection should be consistent between saves."""
        has_dlc_9 = len(self.level_9_skills) >= 24
        has_dlc_10 = len(self.level_10_skills) >= 24
        self.assertEqual(has_dlc_9, has_dlc_10)
    
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
        with open(LEVEL_9_SAVE, 'rb') as f:
            level_9_data = unpack_data(f.read())
        with open(LEVEL_10_SAVE, 'rb') as f:
            level_10_data = unpack_data(f.read())
        
        cls.level_9_skills = get_skill_names_from_data(level_9_data)
        cls.level_10_skills = get_skill_names_from_data(level_10_data)
        
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
    
    def test_level_10_total_within_expected_range(self):
        """Level 10 total should be within expected range.
        
        Maximum at level 10: 120 + (40 * 10) = 520 points
        """
        max_points = 120 + (40 * 10)  # 520
        self.assertLessEqual(self.level_10_total, max_points)
        self.assertGreater(self.level_10_total, 0)


class TestRoundTrip(unittest.TestCase):
    """Tests for pack/unpack round trip on real saves."""
    
    def test_level_9_round_trip(self):
        """Level 9 data should survive pack/unpack round trip."""
        with open(LEVEL_9_SAVE, 'rb') as f:
            original_packed = f.read()
        
        unpacked = unpack_data(original_packed)
        repacked = pack_data(unpacked)
        reunpacked = unpack_data(repacked)
        
        self.assertEqual(unpacked, reunpacked)
    
    def test_level_10_round_trip(self):
        """Level 10 data should survive pack/unpack round trip."""
        with open(LEVEL_10_SAVE, 'rb') as f:
            original_packed = f.read()
        
        unpacked = unpack_data(original_packed)
        repacked = pack_data(unpacked)
        reunpacked = unpack_data(repacked)
        
        self.assertEqual(unpacked, reunpacked)
    
    def test_skills_unchanged_after_round_trip(self):
        """Skills should be unchanged after pack/unpack round trip."""
        with open(LEVEL_9_SAVE, 'rb') as f:
            original_packed = f.read()
        
        original_unpacked = unpack_data(original_packed)
        original_skills = get_skill_names_from_data(original_unpacked)
        
        repacked = pack_data(original_unpacked)
        reunpacked = unpack_data(repacked)
        roundtrip_skills = get_skill_names_from_data(reunpacked)
        
        self.assertEqual(len(original_skills), len(roundtrip_skills))
        
        for orig, rt in zip(original_skills, roundtrip_skills):
            self.assertEqual(orig['base'], rt['base'])
            self.assertEqual(orig['mod'], rt['mod'])


class TestSkillDetails(unittest.TestCase):
    """Detailed tests for specific skill values from known save."""
    
    @classmethod
    def setUpClass(cls):
        """Load level 9 save and parse skills with names."""
        with open(LEVEL_9_SAVE, 'rb') as f:
            cls.level_9_data = unpack_data(f.read())
        
        cls.skills = get_skill_names_from_data(cls.level_9_data)
        cls.skill_names = get_skill_names(len(cls.skills))
        
        # Build dict for easy lookup
        cls.skill_dict = {}
        for i, skill in enumerate(cls.skills):
            if i < len(cls.skill_names):
                cls.skill_dict[cls.skill_names[i]] = skill
    
    def test_melee_skill_present(self):
        """Melee skill should be present in save."""
        self.assertIn("Melee", self.skill_dict)
    
    def test_melee_has_expected_values(self):
        """Melee should have expected values from AI_README.md (base=55, effective=83)."""
        melee = self.skill_dict.get("Melee")
        if melee:
            self.assertEqual(melee['base'], 55, 
                           f"Expected Melee base=55, got {melee['base']}")
            self.assertEqual(melee['mod'], 83,
                           f"Expected Melee effective=83, got {melee['mod']}")
    
    def test_dodge_has_expected_values(self):
        """Dodge should have expected values from AI_README.md (base=55, effective=78)."""
        dodge = self.skill_dict.get("Dodge")
        if dodge:
            self.assertEqual(dodge['base'], 55)
            self.assertEqual(dodge['mod'], 78)
    
    def test_stealth_has_expected_values(self):
        """Stealth should have expected values (base=50, effective=90)."""
        stealth = self.skill_dict.get("Stealth")
        if stealth:
            self.assertEqual(stealth['base'], 50)
            self.assertEqual(stealth['mod'], 90)
    
    def test_intimidation_has_expected_values(self):
        """Intimidation should have expected values from AI_README.md (base=0, effective=5)."""
        intimidation = self.skill_dict.get("Intimidation")
        if intimidation:
            self.assertEqual(intimidation['base'], 0)
            self.assertEqual(intimidation['mod'], 5)


if __name__ == '__main__':
    unittest.main()
