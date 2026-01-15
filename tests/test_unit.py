#!/usr/bin/env python3
"""
Unit tests for skill_editor.py core functions.
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
    write_skill_value,
    read_skill_values,
    PACKED_HEADER,
    SKILL_NAMES_BASE,
    SKILL_NAMES_DLC,
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


if __name__ == '__main__':
    unittest.main()
