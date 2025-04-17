#!/usr/bin/env python
"""
installer.py — LazyTag Hook Installer

Installs lazytag CLI as a Git pre-commit hook.
It adds a call to the lazytag tag command inside .git/hooks/pre-commit.
"""

import os
import shutil
from pathlib import Path

def install_hook():
    repo_root = Path(__file__).resolve().parent
    git_hook_path = repo_root / ".git" / "hooks" / "pre-commit"
    lazytag_script = repo_root / "lazytag.py"

    if not lazytag_script.exists():
        print("[ERROR] lazytag.py not found in the repository root.")
        return

    # Backup existing hook if it exists
    if git_hook_path.exists():
        backup_path = git_hook_path.with_suffix(".bak")
        shutil.copy(git_hook_path, backup_path)
        print(f"[BACKUP] Existing pre-commit hook backed up to: {backup_path}")

    # Write the hook content
    hook_content = f"""#!/bin/bash
# Auto-generated by lazytag installer
python3 {lazytag_script} tag
"""
    with open(git_hook_path, 'w') as f:
        f.write(hook_content)

    os.chmod(git_hook_path, 0o755)
    print(f"[SUCCESS] lazytag hook installed at: {git_hook_path}")

if __name__ == "__main__":
    install_hook()
