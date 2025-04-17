#!/usr/bin/env python
"""
Git Hook Installer: Pre-Commit Hook Setup Utility

Features:
- Installs the tag_commit_hook.py as your .git/hooks/pre-commit script.
- Creates a backup of any existing pre-commit hook.
- Makes the hook executable.
"""

import os
import shutil
from pathlib import Path

def install_hook():
    """Install the pre-commit hook from this directory into .git/hooks."""
    repo_root = Path(__file__).resolve().parent
    hook_path = repo_root / '.git' / 'hooks' / 'pre-commit'
    script_source = repo_root / 'tag_commit_hook.py'

    if not script_source.exists():
        print("[ERROR] tag_commit_hook.py not found in this directory.")
        return

    if hook_path.exists():
        backup = hook_path.with_suffix('.bak')
        shutil.copy(hook_path, backup)
        print(f"[BACKUP] Existing pre-commit hook backed up to: {backup}")

    # Write the shell wrapper to execute our Python script
    with open(hook_path, 'w') as f:
        f.write(f"#!/bin/bash\npython3 {script_source.absolute()}\n")

    os.chmod(hook_path, 0o755)
    print(f"[SUCCESS] Pre-commit hook installed at: {hook_path}")

if __name__ == "__main__":
    install_hook()
