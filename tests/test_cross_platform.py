#!/usr/bin/env python3
"""
Cross-platform tests comparing JavaScript and Python save editing implementations.

These tests validate that both implementations:
1. Can parse save files correctly
2. Produce identical results when making the same edits
3. Generate valid save files that can be re-parsed

Test workflow:
1. Copy fixture to temp directory
2. Make edits using JS CLI
3. Export patched file to JSON using UFE
4. Make same edits using Python/UFE
5. Export patched file to JSON using UFE
6. Compare the relevant JSON values
"""

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from use.ufe_parser import (
    export_to_json,
    load_json,
    SaveData,
    SaveEditor,
    UFE_PATH,
)

# Paths
TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / "fixtures"
WEB_DIR = TESTS_DIR.parent / "web"
LEVEL_11_SAVE = FIXTURES_DIR / "see_me_now" / "level_11" / "global.dat"


def run_js_cli(*args, cwd=None) -> subprocess.CompletedProcess:
    """Run the JS CLI and return the result."""
    cmd = ["npx", "tsx", "cli.ts"] + list(args)
    return subprocess.run(
        cmd,
        cwd=cwd or WEB_DIR,
        capture_output=True,
        text=True,
        timeout=60,
        shell=True,  # Required for npx on Windows
    )


def run_js_parse(save_path: Path) -> dict:
    """Parse a save file using JS CLI and return JSON."""
    result = run_js_cli("parse", str(save_path), "--json")
    if result.returncode != 0:
        raise RuntimeError(f"JS CLI failed: {result.stderr}")
    return json.loads(result.stdout)


def run_js_patch(input_path: Path, output_path: Path, *patch_args) -> bool:
    """Patch a save file using JS CLI."""
    result = run_js_cli("patch", str(input_path), str(output_path), *patch_args)
    return result.returncode == 0


class TestJSCliBasic(unittest.TestCase):
    """Basic tests for the JS CLI."""
    
    def test_cli_exists(self):
        """JS CLI file should exist."""
        cli_path = WEB_DIR / "cli.ts"
        self.assertTrue(cli_path.exists(), f"CLI not found at {cli_path}")
    
    def test_cli_help(self):
        """CLI help should work."""
        result = run_js_cli("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage", result.stdout)
    
    def test_cli_parse(self):
        """CLI parse should work on fixture."""
        result = run_js_cli("parse", str(LEVEL_11_SAVE))
        self.assertEqual(result.returncode, 0)
        self.assertIn("See Me Now", result.stdout)
        self.assertIn("Level: 11", result.stdout)
    
    def test_cli_parse_json(self):
        """CLI parse --json should output valid JSON."""
        result = run_js_cli("parse", str(LEVEL_11_SAVE), "--json")
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data["character"]["name"], "See Me Now")
        self.assertEqual(data["character"]["level"], 11)


class TestJSPythonParsing(unittest.TestCase):
    """Tests comparing JS and Python parsing of the same file."""
    
    @classmethod
    def setUpClass(cls):
        """Load save data from both implementations."""
        # JS parsing
        result = run_js_cli("parse", str(LEVEL_11_SAVE), "--json")
        cls.js_data = json.loads(result.stdout)
        
        # Python parsing via UFE
        json_path = export_to_json(LEVEL_11_SAVE)
        try:
            cls.py_raw = load_json(json_path)
            cls.py_data = SaveData(cls.py_raw)
        finally:
            json_path.unlink()
    
    def test_character_name_matches(self):
        """Character name should match between implementations."""
        self.assertEqual(
            self.js_data["character"]["name"],
            self.py_data.get_character_name()
        )
    
    def test_character_level_matches(self):
        """Character level should match between implementations."""
        self.assertEqual(
            self.js_data["character"]["level"],
            self.py_data.get_character_level()
        )
    
    def test_attribute_count_matches(self):
        """Attribute count should match."""
        js_attrs = self.js_data["attributes"]
        py_attrs = self.py_data.get_base_attributes()
        self.assertEqual(len(js_attrs), len(py_attrs))
    
    def test_attribute_values_match(self):
        """Attribute values should match."""
        js_attrs = self.js_data["attributes"]
        py_attrs = self.py_data.get_base_attributes()
        
        for js_attr, py_attr in zip(js_attrs, py_attrs):
            self.assertEqual(
                js_attr["base"], py_attr["base"],
                f"Mismatch for {js_attr['name']} base"
            )
            self.assertEqual(
                js_attr["effective"], py_attr["effective"],
                f"Mismatch for {js_attr['name']} effective"
            )
    
    def test_skill_count_matches(self):
        """Skill count should match."""
        js_skills = self.js_data["skills"]
        py_skills = self.py_data.get_skills()
        self.assertEqual(len(js_skills), len(py_skills))
    
    def test_skill_values_match(self):
        """Skill values should match."""
        js_skills = self.js_data["skills"]
        py_skills = self.py_data.get_skills()
        
        for i, (js_skill, py_skill) in enumerate(zip(js_skills, py_skills)):
            self.assertEqual(
                js_skill["base"], py_skill["base"],
                f"Mismatch for skill {i} ({js_skill['name']}) base"
            )
            self.assertEqual(
                js_skill["effective"], py_skill["effective"],
                f"Mismatch for skill {i} ({js_skill['name']}) effective"
            )


class TestCrossPlatformEditing(unittest.TestCase):
    """Tests comparing JS and Python editing results."""
    
    def setUp(self):
        """Create temp directory and copy fixture."""
        self.temp_dir = tempfile.mkdtemp()
        self.js_save = Path(self.temp_dir) / "js_global.dat"
        self.py_save = Path(self.temp_dir) / "py_global.dat"
        
        # Copy fixture to both paths
        shutil.copy2(LEVEL_11_SAVE, self.js_save)
        shutil.copy2(LEVEL_11_SAVE, self.py_save)
    
    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_skill_edit_matches(self):
        """Skill edits should produce matching results."""
        skill_index = 0  # Guns
        new_base = 75
        new_effective = 100
        
        # Edit with JS
        js_output = Path(self.temp_dir) / "js_patched.dat"
        success = run_js_patch(
            self.js_save, js_output,
            "--skill", str(skill_index), str(new_base), str(new_effective)
        )
        self.assertTrue(success, "JS patch failed")
        
        # Edit with Python
        editor = SaveEditor(self.py_save)
        editor.set_skill_value(skill_index, new_base, new_effective)
        editor.apply(cleanup_json=False)
        
        # Export both to JSON using UFE
        js_json = export_to_json(js_output)
        py_json = export_to_json(self.py_save)
        
        try:
            js_data = SaveData(load_json(js_json))
            py_data = SaveData(load_json(py_json))
            
            # Compare the edited skill
            js_skills = js_data.get_skills()
            py_skills = py_data.get_skills()
            
            self.assertEqual(
                js_skills[skill_index]["base"],
                py_skills[skill_index]["base"],
                f"Base value mismatch after edit"
            )
            self.assertEqual(
                js_skills[skill_index]["effective"],
                py_skills[skill_index]["effective"],
                f"Effective value mismatch after edit"
            )
            
            # Verify the values are what we set
            self.assertEqual(js_skills[skill_index]["base"], new_base)
            self.assertEqual(js_skills[skill_index]["effective"], new_effective)
        finally:
            js_json.unlink()
            py_json.unlink()
    
    def test_attribute_edit_matches(self):
        """Attribute edits should produce matching results."""
        attr_index = 0  # Strength
        new_base = 15
        new_effective = 15
        
        # Edit with JS
        js_output = Path(self.temp_dir) / "js_patched.dat"
        success = run_js_patch(
            self.js_save, js_output,
            "--attr", str(attr_index), str(new_base), str(new_effective)
        )
        self.assertTrue(success, "JS patch failed")
        
        # Edit with Python
        editor = SaveEditor(self.py_save)
        editor.set_attribute_value(attr_index, new_base, new_effective)
        editor.apply(cleanup_json=False)
        
        # Export both to JSON using UFE
        js_json = export_to_json(js_output)
        py_json = export_to_json(self.py_save)
        
        try:
            js_data = SaveData(load_json(js_json))
            py_data = SaveData(load_json(py_json))
            
            # Compare the edited attribute
            js_attrs = js_data.get_base_attributes()
            py_attrs = py_data.get_base_attributes()
            
            self.assertEqual(
                js_attrs[attr_index]["base"],
                py_attrs[attr_index]["base"],
                f"Base value mismatch after edit"
            )
            self.assertEqual(
                js_attrs[attr_index]["effective"],
                py_attrs[attr_index]["effective"],
                f"Effective value mismatch after edit"
            )
            
            # Verify the values are what we set
            self.assertEqual(js_attrs[attr_index]["base"], new_base)
            self.assertEqual(js_attrs[attr_index]["effective"], new_effective)
        finally:
            js_json.unlink()
            py_json.unlink()
    
    def test_multiple_edits_match(self):
        """Multiple edits should produce matching results."""
        # Edit with JS - multiple changes
        js_output = Path(self.temp_dir) / "js_patched.dat"
        success = run_js_patch(
            self.js_save, js_output,
            "--skill", "0", "50", "75",    # Guns
            "--skill", "4", "80", "120",   # Melee
            "--attr", "0", "12", "12",     # Strength
        )
        self.assertTrue(success, "JS patch failed")
        
        # Edit with Python - same changes
        editor = SaveEditor(self.py_save)
        editor.set_skill_value(0, 50, 75)
        editor.set_skill_value(4, 80, 120)
        editor.set_attribute_value(0, 12, 12)
        editor.apply(cleanup_json=False)
        
        # Export both to JSON using UFE
        js_json = export_to_json(js_output)
        py_json = export_to_json(self.py_save)
        
        try:
            js_data = SaveData(load_json(js_json))
            py_data = SaveData(load_json(py_json))
            
            # Compare skills
            js_skills = js_data.get_skills()
            py_skills = py_data.get_skills()
            
            # Skill 0 (Guns)
            self.assertEqual(js_skills[0]["base"], 50)
            self.assertEqual(py_skills[0]["base"], 50)
            self.assertEqual(js_skills[0]["effective"], 75)
            self.assertEqual(py_skills[0]["effective"], 75)
            
            # Skill 4 (Melee)
            self.assertEqual(js_skills[4]["base"], 80)
            self.assertEqual(py_skills[4]["base"], 80)
            self.assertEqual(js_skills[4]["effective"], 120)
            self.assertEqual(py_skills[4]["effective"], 120)
            
            # Compare attribute
            js_attrs = js_data.get_base_attributes()
            py_attrs = py_data.get_base_attributes()
            
            self.assertEqual(js_attrs[0]["base"], 12)
            self.assertEqual(py_attrs[0]["base"], 12)
        finally:
            js_json.unlink()
            py_json.unlink()


class TestRoundTrip(unittest.TestCase):
    """Tests for save file round-trip (edit -> save -> load -> verify)."""
    
    def setUp(self):
        """Create temp directory."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_js_edit_roundtrip(self):
        """JS-edited file should be parseable by both JS and Python."""
        # Copy fixture
        save_path = Path(self.temp_dir) / "global.dat"
        output_path = Path(self.temp_dir) / "patched.dat"
        shutil.copy2(LEVEL_11_SAVE, save_path)
        
        # Edit with JS
        skill_index = 2  # Throwing
        new_base = 150
        new_effective = 200
        
        success = run_js_patch(
            save_path, output_path,
            "--skill", str(skill_index), str(new_base), str(new_effective)
        )
        self.assertTrue(success, "JS patch failed")
        
        # Parse with JS
        result = run_js_cli("parse", str(output_path), "--json")
        self.assertEqual(result.returncode, 0, f"JS parse failed: {result.stderr}")
        js_data = json.loads(result.stdout)
        
        # Parse with Python/UFE
        json_path = export_to_json(output_path)
        try:
            py_data = SaveData(load_json(json_path))
            
            # Verify JS parsing shows correct values
            self.assertEqual(js_data["skills"][skill_index]["base"], new_base)
            self.assertEqual(js_data["skills"][skill_index]["effective"], new_effective)
            
            # Verify Python parsing shows correct values
            py_skills = py_data.get_skills()
            self.assertEqual(py_skills[skill_index]["base"], new_base)
            self.assertEqual(py_skills[skill_index]["effective"], new_effective)
        finally:
            json_path.unlink()
    
    def test_python_edit_roundtrip(self):
        """Python-edited file should be parseable by both JS and Python."""
        # Copy fixture
        save_path = Path(self.temp_dir) / "global.dat"
        shutil.copy2(LEVEL_11_SAVE, save_path)
        
        # Edit with Python
        attr_index = 2  # Agility
        new_base = 14
        new_effective = 15
        
        editor = SaveEditor(save_path)
        editor.set_attribute_value(attr_index, new_base, new_effective)
        editor.apply(cleanup_json=True)
        
        # Parse with JS
        result = run_js_cli("parse", str(save_path), "--json")
        self.assertEqual(result.returncode, 0, f"JS parse failed: {result.stderr}")
        js_data = json.loads(result.stdout)
        
        # Parse with Python/UFE
        json_path = export_to_json(save_path)
        try:
            py_data = SaveData(load_json(json_path))
            
            # Verify JS parsing shows correct values
            self.assertEqual(js_data["attributes"][attr_index]["base"], new_base)
            self.assertEqual(js_data["attributes"][attr_index]["effective"], new_effective)
            
            # Verify Python parsing shows correct values
            py_attrs = py_data.get_base_attributes()
            self.assertEqual(py_attrs[attr_index]["base"], new_base)
            self.assertEqual(py_attrs[attr_index]["effective"], new_effective)
        finally:
            json_path.unlink()


if __name__ == "__main__":
    unittest.main()
