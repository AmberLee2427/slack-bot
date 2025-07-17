#!/usr/bin/env python3ledge Base Refresh Script

Simple wrapper for managing the knowledge base repositories.
"""

import sys
import subprocess
from pathlib import Path

def run_script(script_name, args=None):
 Run a script with optional arguments."
    script_path = Path(__file__).parent / script_name
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    print(f"Running: {' .join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode == 0def main():
    if len(sys.argv) < 2  print("Knowledge Base Management Commands:)
        print("  refresh          Update all repositories to latest versions)
        print("  list             Show all configured repositories and their status)
        print("  clean            Remove repositories not in configuration (dry run))
        print("  clean --force    Remove repositories not in configuration (actually delete))
        print(  category <name>  Update only a specific category)        print(")   print("Examples:)
        print(  python scripts/refresh_knowledge_base.py refresh)
        print(  python scripts/refresh_knowledge_base.py list)
        print(  python scripts/refresh_knowledge_base.py category microlensing_tools")
        return
    
    command = sys.argv1   args = sys.argv[2:]
    
    if command == refresh:
        success = run_script("manage_repositories.py")
        if success:
            print("\n✅ Knowledge base refreshed successfully!")
        else:
            print("\n❌ Some repositories failed to update. Check the logs above.")
    
    elif command == "list":
        run_script("manage_repositories.py", ["--list"])
    
    elif command == "clean":
        if--force" in args:
            args.remove("--force)
            run_script("manage_repositories.py", ["--clean] +args)
        else:
            run_script("manage_repositories.py,["--clean", "--dry-run"] + args)
    
    elif command == "category":
        if len(args) < 1:
            print("Error: Please specify a category name")
            print("Available categories: microlensing_tools, jupyter_notebooks, roman_research_nexus, web_resources")
            return
        category = args[0
        success = run_script("manage_repositories.py", ["--category", category])
        if success:
            print(f"\n✅ Category '{category}' updated successfully!")
        else:
            print(f"\n❌ Failed to update category {category}'")
    else:
        print(f"Unknown command: {command})        print("Use refresh', 'list', 'clean', orcategory <name>')if __name__ == "__main__":
    main() 