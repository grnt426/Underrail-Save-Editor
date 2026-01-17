#!/usr/bin/env python3
"""
Underrail Save Editor - Main Console Screen

This is the main entry point for the Underrail Save Editor.
It provides a simple console menu to access the viewer and editor tools.
"""

import sys
from pathlib import Path

# Module-level state for loaded save context
_loaded_save_path = None
_loaded_char_name = None


def get_loaded_path():
    """Get the currently loaded save path."""
    return _loaded_save_path


def get_loaded_char_name():
    """Get the character name from the loaded save."""
    return _loaded_char_name


def set_loaded_save(path, char_name=None):
    """Set the currently loaded save path and character name."""
    global _loaded_save_path, _loaded_char_name
    _loaded_save_path = path
    _loaded_char_name = char_name


def print_banner():
    """Print the application banner."""
    print()
    print("=" * 60)
    print("  USE - Underrail Save Editor")
    print("=" * 60)
    print()


def print_help():
    """Print help information."""
    print()
    print("Available commands:")
    print()
    print("  load <path>  - Load a save file path for subsequent operations")
    print("                 Sets the path as context for 'view' and 'edit'.")
    print()
    print("  unload       - Clear the loaded save file path")
    print()
    print("  view [path]  - View character data from a save file")
    print("                 Shows stats, skills, feats, XP, and currency")
    print("                 without making any modifications.")
    print("                 Uses loaded path if no path is given.")
    print()
    print("  equip [path] - Show equipped items from a save file")
    print("  equipped       Displays character gear, utility slots, and hotbar")
    print("                 items without showing full inventory.")
    print("                 Uses loaded path if no path is given.")
    print()
    print("  edit [path]  - Edit a save file")
    print("                 Modify base attributes and skill allocations.")
    print("                 Creates a backup before saving changes.")
    print("                 Uses loaded path if no path is given.")
    print()
    print("  help, h      - Show this help message")
    print()
    print("  quit, q      - Exit the program")
    print("  done, exit")
    print()
    print("Path argument:")
    print("  - Can be a save folder (will look for global.dat inside)")
    print("  - Can be a direct path to global.dat")
    print("  - If omitted, uses loaded path or current directory")
    print()


def load_save(args=None):
    """Load a save file path as context for subsequent operations."""
    from .core import resolve_save_path, load_save_data, find_character_name
    
    if not args:
        # Show current loaded path, or help if nothing loaded
        loaded = get_loaded_path()
        if loaded:
            char_name = get_loaded_char_name()
            if char_name:
                print(f"Currently loaded: {loaded} ({char_name})")
            else:
                print(f"Currently loaded: {loaded}")
        else:
            print("No save file is currently loaded.")
            print("Usage: load <path>")
        return
    
    path_arg = args[0]
    
    try:
        # Validate the path resolves to a save file
        resolved = resolve_save_path(path_arg)
        
        # Extract character name from the save
        char_name = None
        try:
            save_data = load_save_data(resolved)
            char_name = find_character_name(save_data)
        except Exception:
            pass  # Character name is optional for the prompt
        
        set_loaded_save(str(resolved), char_name)
        if char_name:
            print(f"Loaded: {resolved} ({char_name})")
        else:
            print(f"Loaded: {resolved}")
    except FileNotFoundError as e:
        print(f"Error: {e}")


def unload_save():
    """Clear the loaded save file path."""
    if get_loaded_path():
        print(f"Unloaded: {get_loaded_path()}")
        set_loaded_save(None, None)
    else:
        print("No save file is currently loaded.")


def run_viewer(args=None):
    """Run the viewer module."""
    from .viewer import main as viewer_main
    
    # Use loaded path if no args provided
    if not args and get_loaded_path():
        args = [get_loaded_path()]
    
    try:
        viewer_main(args)
    except SystemExit:
        pass  # Don't exit the main loop
    except Exception as e:
        print(f"Error: {e}")


def run_editor(args=None):
    """Run the editor module."""
    from .editor import main as editor_main
    
    # Use loaded path if no args provided
    if not args and get_loaded_path():
        args = [get_loaded_path()]
    
    try:
        editor_main(args)
    except SystemExit:
        pass  # Don't exit the main loop
    except KeyboardInterrupt:
        print("\nEditor cancelled.")
    except Exception as e:
        print(f"Error: {e}")


def run_equipment(args=None):
    """Show equipped items from a save file."""
    from .core import (
        resolve_save_path,
        load_save_data,
        find_character_name,
        get_equipment_summary,
    )
    
    # Determine path to use
    if args:
        path_arg = args[0]
    elif get_loaded_path():
        path_arg = get_loaded_path()
    else:
        path_arg = None
    
    try:
        save_path = resolve_save_path(path_arg)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    
    # Load and parse
    try:
        save_data = load_save_data(save_path)
        char_name = find_character_name(save_data)
        equipment = get_equipment_summary(save_data)
    except Exception as e:
        print(f"Error loading save: {e}")
        return
    
    # Display
    print()
    print("=" * 60)
    print("EQUIPPED ITEMS")
    print("=" * 60)
    print(f"Save file: {save_path}")
    if char_name:
        print(f"Character: {char_name}")
    print()
    
    if equipment['total_equipped'] == 0:
        print("No equipped items found.")
        print()
        return
    
    # Character gear (armor, weapons, belt)
    if equipment['character_gear']:
        print("CHARACTER GEAR")
        print("-" * 40)
        for item in equipment['character_gear']:
            print(f"  {item['name']:<30} [{item['category']}]")
            # Show stats on second line for crafted items
            stats = []
            if item.get('value') is not None:
                stats.append(f"Value: {item['value']:,.0f}")
            if item.get('weight') is not None:
                stats.append(f"Weight: {item['weight']:.1f}")
            if stats:
                print(f"    {', '.join(stats)}")
        print()
    
    # Utility slots (belt slots for grenades, tools, etc.)
    if equipment['utility_slots']:
        print("UTILITY SLOTS")
        print("-" * 40)
        for item in equipment['utility_slots']:
            count = item.get('count', 1)
            if count > 1:
                print(f"  {item['name']:<30} x{count}")
            else:
                print(f"  {item['name']:<30}")
        print()
    
    # Hotbar items
    if equipment['hotbar']:
        print("HOTBAR")
        print("-" * 40)
        for item in equipment['hotbar']:
            print(f"  {item['name']:<30} [{item['category']}]")
        print()
    
    print("=" * 60)
    print(f"Total equipped: {equipment['total_equipped']}")
    print("=" * 60)


def get_prompt():
    """Generate the command prompt, showing loaded save if any."""
    loaded = get_loaded_path()
    if loaded:
        # Show abbreviated path in prompt
        p = Path(loaded)
        # Try to show save folder name for brevity
        if p.name == 'global.dat':
            save_name = p.parent.name
        elif p.name == 'global':
            save_name = p.parent.parent.name
        else:
            save_name = p.name
        
        # Include character name if available, underlined for clarity
        char_name = get_loaded_char_name()
        if char_name:
            # ANSI underline: \033[4m starts underline, \033[0m resets
            return f"use [{save_name}:\033[4m{char_name}\033[0m]> "
        return f"use [{save_name}]> "
    return "use> "


def main():
    """Main entry point - runs the interactive console."""
    print_banner()
    print("Type 'help' for available commands, or 'quit' to exit.")
    print()
    
    quit_commands = {'quit', 'q', 'done', 'exit'}
    help_commands = {'help', 'h', '?'}
    
    while True:
        try:
            user_input = input(get_prompt()).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        # Parse command and arguments
        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1].split() if len(parts) > 1 else None
        
        # Handle commands
        if command in quit_commands:
            print("Goodbye!")
            break
        
        elif command in help_commands:
            print_help()
        
        elif command == 'load':
            load_save(args)
            print()
        
        elif command == 'unload':
            unload_save()
            print()
        
        elif command == 'view':
            run_viewer(args)
            print()  # Extra newline after viewer output
        
        elif command in ('equip', 'equipped'):
            run_equipment(args)
            print()  # Extra newline after equipment output
        
        elif command == 'edit':
            run_editor(args)
            print()  # Extra newline after editor output
        
        else:
            print(f"Unknown command: '{command}'")
            print("Type 'help' for available commands.")
            print()


if __name__ == "__main__":
    main()
