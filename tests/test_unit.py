#!/usr/bin/env python3
"""
Unit tests for skill_editor.py and view_save.py core functions.
"""

import unittest
import struct
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
    get_base_stats_from_data,
    write_skill_value,
    write_stat_value,
    read_skill_values,
    PACKED_HEADER,
    SKILL_NAMES_BASE,
    SKILL_NAMES_DLC,
    STAT_NAMES,
    ESI_PATTERN,
)

from view_save import (
    calculate_xp_needed,
    find_xp_current,
    find_currency,
    find_game_version,
    find_character_name,
    find_base_stats,
    detect_dlc,
    detect_xp_system,
    XP_PATTERN,
    VERSION_MARKER,
    CURRENCY_PATHS,
    FEAT_DISPLAY_NAMES,
)


class TestPackedDetection(unittest.TestCase):
    """Tests for is_packed() function."""
    
    def test_packed_header_detected(self):
        """Packed files should be detected by GUID header."""
        # Construct minimal packed data (header + version + gzip)
        fake_packed = PACKED_HEADER + bytes(8) + bytes(100)
        self.assertTrue(is_packed(fake_packed))
    
    def test_unpacked_data_not_detected(self):
        """Unpacked data should not be detected as packed."""
        unpacked = b'eSKC\x02\x00\x00\x00' + bytes(100)
        self.assertFalse(is_packed(unpacked))
    
    def test_empty_data(self):
        """Empty data should not be detected as packed."""
        self.assertFalse(is_packed(b''))
    
    def test_short_data(self):
        """Data shorter than header should not be detected as packed."""
        self.assertFalse(is_packed(PACKED_HEADER[:8]))


class TestPackUnpack(unittest.TestCase):
    """Tests for pack_data() and unpack_data() functions."""
    
    def test_round_trip(self):
        """Data should survive pack/unpack round trip."""
        original = b'Test data with some bytes: \x00\x01\x02\xff'
        packed = pack_data(original)
        unpacked = unpack_data(packed)
        self.assertEqual(original, unpacked)
    
    def test_packed_has_header(self):
        """Packed data should start with GUID header."""
        original = b'Some test data'
        packed = pack_data(original)
        self.assertTrue(packed.startswith(PACKED_HEADER))
    
    def test_packed_is_compressed(self):
        """Packed data should be smaller than original for compressible data."""
        # Create highly compressible data
        original = b'A' * 10000
        packed = pack_data(original)
        # Packed includes 24-byte header, so compare content sizes
        self.assertLess(len(packed), len(original))


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


class TestSkillValueOperations(unittest.TestCase):
    """Tests for read and write skill value functions."""
    
    def test_write_skill_value_base_only(self):
        """write_skill_value should write base value correctly."""
        data = bytearray(20)
        write_skill_value(data, 4, 55)
        value = struct.unpack('<i', data[4:8])[0]
        self.assertEqual(value, 55)
    
    def test_write_skill_value_with_mod(self):
        """write_skill_value should write both base and mod values."""
        data = bytearray(20)
        write_skill_value(data, 4, 55, 83)
        base = struct.unpack('<i', data[4:8])[0]
        mod = struct.unpack('<i', data[8:12])[0]
        self.assertEqual(base, 55)
        self.assertEqual(mod, 83)
    
    def test_read_skill_values(self):
        """read_skill_values should extract values from offsets."""
        # Create test data with known skill values
        data = bytearray(50)
        struct.pack_into('<i', data, 10, 25)  # base at offset 10
        struct.pack_into('<i', data, 14, 40)  # mod at offset 14
        struct.pack_into('<i', data, 30, 50)  # base at offset 30
        struct.pack_into('<i', data, 34, 75)  # mod at offset 34
        
        offsets = [
            {'offset': 10, 'base': 25, 'mod': 40},
            {'offset': 30, 'base': 50, 'mod': 75},
        ]
        
        skills = read_skill_values(bytes(data), offsets)
        
        self.assertEqual(len(skills), 2)
        self.assertEqual(skills[0]['base'], 25)
        self.assertEqual(skills[0]['mod'], 40)
        self.assertEqual(skills[1]['base'], 50)
        self.assertEqual(skills[1]['mod'], 75)


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
    
    def test_write_stat_value_base_only(self):
        """write_stat_value should write base value correctly."""
        data = bytearray(20)
        write_stat_value(data, 4, 8)
        value = struct.unpack('<i', data[4:8])[0]
        self.assertEqual(value, 8)
    
    def test_write_stat_value_with_effective(self):
        """write_stat_value should write both base and effective values."""
        data = bytearray(20)
        write_stat_value(data, 4, 8, 10)
        base = struct.unpack('<i', data[4:8])[0]
        effective = struct.unpack('<i', data[8:12])[0]
        self.assertEqual(base, 8)
        self.assertEqual(effective, 10)
    
    def test_get_base_stats_synthetic(self):
        """get_base_stats_from_data should find synthetic stat patterns."""
        # Build a synthetic stat entry using ESI pattern
        type_id = struct.pack('<I', 1115)  # Variable type ID
        base_val = struct.pack('<i', 8)
        eff_val = struct.pack('<i', 9)
        
        data = bytes(100) + ESI_PATTERN + type_id + base_val + eff_val + bytes(100)
        
        stats = get_base_stats_from_data(data)
        
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]['base'], 8)
        self.assertEqual(stats[0]['effective'], 9)
    
    def test_get_base_stats_filters_invalid(self):
        """get_base_stats_from_data should filter out unreasonable values."""
        type_id = struct.pack('<I', 1115)
        
        # Create entry with invalid value (too high for a stat)
        invalid_base = struct.pack('<i', 50)  # > 30 max
        invalid_eff = struct.pack('<i', 60)   # > 50 max
        
        data = bytes(50) + ESI_PATTERN + type_id + invalid_base + invalid_eff + bytes(50)
        
        stats = get_base_stats_from_data(data)
        
        # Should find 0 stats due to filtering
        self.assertEqual(len(stats), 0)


class TestSkillPatternParsing(unittest.TestCase):
    """Tests for skill pattern detection."""
    
    def test_pattern_detection_synthetic(self):
        """get_skill_names_from_data should find synthetic skill patterns."""
        # Build a synthetic skill entry:
        # eSKC + \x02\x00\x00\x00 + \x02\x00\x00\x00 + \x09 + type_id(4) + base(4) + mod(4)
        pattern = b'eSKC\x02\x00\x00\x00\x02\x00\x00\x00\x09'
        type_id = struct.pack('<I', 1116)  # Variable type ID
        base_val = struct.pack('<i', 55)
        mod_val = struct.pack('<i', 83)
        
        data = bytes(100) + pattern + type_id + base_val + mod_val + bytes(100)
        
        skills = get_skill_names_from_data(data)
        
        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0]['base'], 55)
        self.assertEqual(skills[0]['mod'], 83)
    
    def test_pattern_filters_invalid_values(self):
        """get_skill_names_from_data should filter out unreasonable values."""
        pattern = b'eSKC\x02\x00\x00\x00\x02\x00\x00\x00\x09'
        type_id = struct.pack('<I', 1116)
        
        # Create entries with invalid values (too high)
        invalid_base = struct.pack('<i', 500)  # > 300 max
        invalid_mod = struct.pack('<i', 100)
        
        data = bytes(50) + pattern + type_id + invalid_base + invalid_mod + bytes(50)
        
        skills = get_skill_names_from_data(data)
        
        # Should find 0 skills due to filtering
        self.assertEqual(len(skills), 0)
    
    def test_multiple_skills_detected(self):
        """get_skill_names_from_data should find multiple skill entries."""
        pattern = b'eSKC\x02\x00\x00\x00\x02\x00\x00\x00\x09'
        type_id = struct.pack('<I', 1116)
        
        # Create 3 valid skill entries
        skill1 = pattern + type_id + struct.pack('<ii', 10, 15)
        skill2 = pattern + type_id + struct.pack('<ii', 20, 30)
        skill3 = pattern + type_id + struct.pack('<ii', 30, 45)
        
        data = bytes(50) + skill1 + bytes(20) + skill2 + bytes(20) + skill3 + bytes(50)
        
        skills = get_skill_names_from_data(data)
        
        self.assertEqual(len(skills), 3)
        self.assertEqual(skills[0]['base'], 10)
        self.assertEqual(skills[1]['base'], 20)
        self.assertEqual(skills[2]['base'], 30)


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
    
    def test_find_xp_synthetic(self):
        """find_xp_current should extract XP from pattern."""
        # Build synthetic XP data
        xp_value = struct.pack('<i', 42)
        data = bytes(100) + XP_PATTERN + xp_value + bytes(100)
        
        result = find_xp_current(data)
        self.assertEqual(result, 42)
    
    def test_find_xp_zero(self):
        """find_xp_current should handle zero XP."""
        xp_value = struct.pack('<i', 0)
        data = bytes(100) + XP_PATTERN + xp_value + bytes(100)
        
        result = find_xp_current(data)
        self.assertEqual(result, 0)
    
    def test_find_xp_invalid_too_high(self):
        """find_xp_current should reject unreasonably high values."""
        # Value > 10 million should be rejected
        xp_value = struct.pack('<i', 20000000)
        data = bytes(100) + XP_PATTERN + xp_value + bytes(100)
        
        result = find_xp_current(data)
        self.assertIsNone(result)
    
    def test_find_xp_not_found(self):
        """find_xp_current should return None if pattern not found."""
        data = bytes(1000)  # No XP pattern
        
        result = find_xp_current(data)
        self.assertIsNone(result)


class TestCurrencyDetection(unittest.TestCase):
    """Tests for currency detection functions."""
    
    def test_currency_paths_defined(self):
        """Currency paths should be defined for coins and credits."""
        self.assertIn('stygian_coins', CURRENCY_PATHS)
        self.assertIn('sgs_credits', CURRENCY_PATHS)
    
    def test_find_currency_not_found(self):
        """find_currency should return None for missing currencies."""
        data = bytes(1000)  # No currency data
        
        result = find_currency(data)
        
        self.assertIsNone(result.get('stygian_coins'))
        self.assertIsNone(result.get('sgs_credits'))
    
    def test_find_currency_returns_dict(self):
        """find_currency should always return a dictionary."""
        data = bytes(100)
        
        result = find_currency(data)
        
        self.assertIsInstance(result, dict)


class TestGameVersionDetection(unittest.TestCase):
    """Tests for game version detection."""
    
    def test_find_version_synthetic(self):
        """find_game_version should extract version from pattern."""
        # Build synthetic version data
        # Marker + 4 null bytes (field terminator) + 4 type bytes + 4 int32 values
        version_data = (
            VERSION_MARKER +
            b'\x00\x00\x00\x00' +  # Field nulls
            b'\x00\x00\x00\x00' +  # Type bytes
            struct.pack('<i', 1) +   # Major
            struct.pack('<i', 3) +   # Minor
            struct.pack('<i', 0) +   # Build
            struct.pack('<i', 17)    # Revision
        )
        data = bytes(100) + version_data + bytes(100)
        
        result = find_game_version(data)
        
        self.assertEqual(result, (1, 3, 0, 17))
    
    def test_find_version_not_found(self):
        """find_game_version should return None if pattern not found."""
        data = bytes(1000)
        
        result = find_game_version(data)
        
        self.assertIsNone(result)
    
    def test_find_version_filters_invalid(self):
        """find_game_version should reject unreasonable values."""
        # Create version with invalid major version (> 10)
        version_data = (
            VERSION_MARKER +
            b'\x00\x00\x00\x00' +
            b'\x00\x00\x00\x00' +
            struct.pack('<i', 99) +   # Major too high
            struct.pack('<i', 3) +
            struct.pack('<i', 0) +
            struct.pack('<i', 17)
        )
        data = bytes(100) + version_data + bytes(100)
        
        result = find_game_version(data)
        
        self.assertIsNone(result)


class TestCharacterNameDetection(unittest.TestCase):
    """Tests for character name detection."""
    
    def test_find_name_synthetic(self):
        """find_character_name should extract name from pattern."""
        # Build synthetic name data
        # \x06 + any byte + XX + \x00\x00 + length + name + sentinel "eG"
        name = b'TestChar'
        name_data = (
            b'\x06' +           # Pattern start
            b'\x99' +           # Variable byte
            b'\x04\x00\x00' +   # XX + nulls
            bytes([len(name)]) +  # Length
            name +              # Name
            b'\x00' * 5 +       # Padding
            b'eG'               # Sentinel
        )
        data = bytes(100) + name_data + bytes(100)
        
        result = find_character_name(data)
        
        self.assertEqual(result, 'TestChar')
    
    def test_find_name_with_spaces(self):
        """find_character_name should handle names with spaces."""
        name = b'Test Character'
        name_data = (
            b'\x06\x99\x04\x00\x00' +
            bytes([len(name)]) +
            name +
            b'\x00' * 5 +
            b'eG'
        )
        data = bytes(100) + name_data + bytes(100)
        
        result = find_character_name(data)
        
        self.assertEqual(result, 'Test Character')
    
    def test_find_name_not_found(self):
        """find_character_name should return None if not found."""
        data = bytes(1000)
        
        result = find_character_name(data)
        
        self.assertIsNone(result)
    
    def test_find_name_filters_short_names(self):
        """find_character_name should reject names shorter than 3 chars."""
        name = b'AB'  # Too short
        name_data = (
            b'\x06\x99\x04\x00\x00' +
            bytes([len(name)]) +
            name +
            b'\x00' * 5 +
            b'eG'
        )
        data = bytes(100) + name_data + bytes(100)
        
        result = find_character_name(data)
        
        self.assertIsNone(result)


class TestDLCDetection(unittest.TestCase):
    """Tests for DLC detection."""
    
    def test_expedition_detected_by_skill_count(self):
        """Expedition DLC should be detected with 24+ skills."""
        data = bytes(100)
        
        result = detect_dlc(data, 24)
        
        self.assertTrue(result['expedition'])
    
    def test_expedition_not_detected_with_23_skills(self):
        """Base game (23 skills) should not flag Expedition."""
        data = bytes(100)
        
        result = detect_dlc(data, 23)
        
        self.assertFalse(result['expedition'])
    
    def test_expedition_detected_by_content_marker(self):
        """Expedition DLC should be detected by content markers."""
        data = b'some data xpbl_jetski more data'
        
        result = detect_dlc(data, 23)
        
        self.assertTrue(result['expedition'])
    
    def test_expedition_detected_by_expedition_marker(self):
        """Expedition DLC should be detected by expedition_ marker."""
        data = b'some data expedition_quest more data'
        
        result = detect_dlc(data, 23)
        
        self.assertTrue(result['expedition'])


class TestXPSystemDetection(unittest.TestCase):
    """Tests for XP system detection."""
    
    def test_oddity_detected_with_studied_oddities(self):
        """Oddity XP should be detected when studied oddities are present."""
        data = b'some data Oddity.PsiBeetleBrain more data'
        
        system, certain = detect_xp_system(data)
        
        self.assertEqual(system, 'oddity')
        self.assertTrue(certain)
    
    def test_multiple_oddities_detected(self):
        """Oddity XP should be detected with multiple oddity entries."""
        data = b'Oddity.ChewToy Oddity.OmegaIdCard Oddity.StrangeCommDevice'
        
        system, certain = detect_xp_system(data)
        
        self.assertEqual(system, 'oddity')
        self.assertTrue(certain)
    
    def test_no_oddities_returns_classic_uncertain(self):
        """Without studied oddities, returns classic but uncertain."""
        data = b'some save data without oddity entries'
        
        system, certain = detect_xp_system(data)
        
        self.assertEqual(system, 'classic')
        self.assertFalse(certain)
    
    def test_empty_data_returns_classic_uncertain(self):
        """Empty data returns classic but uncertain."""
        data = bytes(100)
        
        system, certain = detect_xp_system(data)
        
        self.assertEqual(system, 'classic')
        self.assertFalse(certain)
    
    def test_oddity_substring_not_matched(self):
        """'Oddity' without dot should not trigger detection."""
        # The word "Oddity" alone (without the dot) might appear in other contexts
        data = b'OddityXP or just Oddity text'
        
        system, certain = detect_xp_system(data)
        
        self.assertEqual(system, 'classic')
        self.assertFalse(certain)


class TestViewSaveBaseStats(unittest.TestCase):
    """Tests for view_save's find_base_stats function."""
    
    def test_find_base_stats_synthetic(self):
        """find_base_stats should find synthetic stat patterns."""
        # Build a synthetic stat entry using ESI pattern
        from view_save import ESI_PATTERN as VIEW_ESI
        
        type_id = struct.pack('<I', 1115)
        base_val = struct.pack('<i', 8)
        eff_val = struct.pack('<i', 9)
        
        data = bytes(100) + VIEW_ESI + type_id + base_val + eff_val + bytes(100)
        
        stats = find_base_stats(data)
        
        self.assertEqual(len(stats), 1)
        self.assertEqual(stats[0]['base'], 8)
        self.assertEqual(stats[0]['effective'], 9)
    
    def test_find_base_stats_filters_invalid(self):
        """find_base_stats should filter out unreasonable values."""
        from view_save import ESI_PATTERN as VIEW_ESI
        
        type_id = struct.pack('<I', 1115)
        invalid_base = struct.pack('<i', 50)  # > 30 max
        invalid_eff = struct.pack('<i', 60)   # > 50 max
        
        data = bytes(50) + VIEW_ESI + type_id + invalid_base + invalid_eff + bytes(50)
        
        stats = find_base_stats(data)
        
        self.assertEqual(len(stats), 0)


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


if __name__ == '__main__':
    unittest.main()
