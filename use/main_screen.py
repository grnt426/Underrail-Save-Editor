#!/usr/bin/env python3
"""
Underrail Save Editor - Main Console Screen

This is the main entry point for the Underrail Save Editor.
It provides a simple console menu to access the viewer and editor tools.
"""

import sys


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
    print("  view [path]  - View character data from a save file")
    print("                 Shows stats, skills, feats, XP, and currency")
    print("                 without making any modifications.")
    print()
    print("  edit [path]  - Edit a save file")
    print("                 Modify base attributes and skill allocations.")
    print("                 Creates a backup before saving changes.")
    print()
    print("  help, h      - Show this help message")
    print()
    print("  quit, q      - Exit the program")
    print("  done, exit")
    print()
    print("Path argument:")
    print("  - Can be a save folder (will look for global.dat inside)")
    print("  - Can be a direct path to global.dat")
    print("  - If omitted, uses current directory")
    print()


def run_viewer(args=None):
    """Run the viewer module."""
    from .viewer import main as viewer_main
    try:
        viewer_main(args)
    except SystemExit:
        pass  # Don't exit the main loop
    except Exception as e:
        print(f"Error: {e}")


def run_editor(args=None):
    """Run the editor module."""
    from .editor import main as editor_main
    try:
        editor_main(args)
    except SystemExit:
        pass  # Don't exit the main loop
    except KeyboardInterrupt:
        print("\nEditor cancelled.")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main entry point - runs the interactive console."""
    print_banner()
    print("Type 'help' for available commands, or 'quit' to exit.")
    print()
    
    quit_commands = {'quit', 'q', 'done', 'exit'}
    help_commands = {'help', 'h', '?'}
    
    while True:
        try:
            user_input = input("use> ").strip()
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
        
        elif command == 'view':
            run_viewer(args)
            print()  # Extra newline after viewer output
        
        elif command == 'edit':
            run_editor(args)
            print()  # Extra newline after editor output
        
        else:
            print(f"Unknown command: '{command}'")
            print("Type 'help' for available commands.")
            print()


if __name__ == "__main__":
    main()
