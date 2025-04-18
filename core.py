#!/usr/bin/env python
"""
core.py — LazyTag Core Logic

Provides the main functionality for tagging modified lines in staged files.
Used by both the CLI (lazytag.py) and Git hook integration.
"""

import subprocess
import re
from pathlib import Path

COMMENT_CHARS = {
    '.py': '#',
    '.c': '//',
    '.cpp': '//',
    '.h': '//',
    '.hpp': '//',
    '.rs': '//',
    '.adb': '--',
    '.ads': '--',
    '.ada': '--',
}

MAX_LINE_LENGTH = 80

def get_branch_tag():
    try:
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
        match = re.search(r'([A-Z]+-\d+)', branch)
        return match.group(1) if match else None
    except subprocess.CalledProcessError:
        return None

def get_staged_files():
    output = subprocess.check_output(['git', 'diff', '--cached', '--name-only']).decode()
    return [line.strip() for line in output.splitlines() if Path(line.strip()).suffix.lower() in COMMENT_CHARS]

def get_file_diff_lines(filename):
    output = subprocess.check_output(['git', 'diff', '--cached', '-U0', filename]).decode()
    changes = []
    for line in output.splitlines():
        if line.startswith('@@'):
            m = re.search(r'\+(\d+)(?:,(\d+))?', line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2) or 1)
                for i in range(start, start + count):
                    changes.append(i)
    return set(changes)

def get_merge_base(base_branch="origin/development"):
        return subprocess.run(
            ["git", "merge-base", "HEAD", branch],
            capture_output=True, text=True
        )

    result = run_merge_base(base_branch)
    if result.returncode == 0:
        return result.stdout.strip()
    else:
        # fallback to main
        fallback = "main"
        fallback_result = run_merge_base(fallback)
        if fallback_result.returncode == 0:
            print(f"[WARN] Branch '{base_branch}' not found. Falling back to '{fallback}'.")
            return fallback_result.stdout.strip()
        else:
            raise RuntimeError(f"Could not find merge base with '{base_branch}' or fallback '{fallback}'.")

def get_diff_lines_from_base(base_commit: str) -> dict[str, set[int]]:
    result = subprocess.run(
        ["git", "diff", "--unified=0", base_commit, "HEAD"],
        capture_output=True, text=True, check=True
    )
    diff_text = result.stdout
    changes = {}
    current_file = None

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:].strip()
            changes[current_file] = set()
        elif line.startswith("@@") and current_file:
            match = re.search(r'\+(\d+)(?:,(\d+))?', line)
            if match:
                start = int(match.group(1))
                count = int(match.group(2)) if match.group(2) else 1
                changes[current_file].update(range(start, start + count))
    return changes

# ... all previous functions like extract_tags, align_tags_with_comments, etc. remain unchanged

# Replace the original function with this extended version

def process_files_with_tag(preferred_tag=None, dry_run=False, scope="staged", base_branch="origin/development"):
    tag = preferred_tag or get_branch_tag()
    if not tag:
        print("[ERROR] No Jira-style tag found (use --tag or a branch like ABC-1234-feature)")
        return

    if scope == "base":
        try:
            base_commit = get_merge_base(base_branch)
        except RuntimeError as e:
            print(f"[ERROR] {e}")
            return
        all_changes = get_diff_lines_from_base(base_commit)
    else:
        files = get_staged_files()
        all_changes = {f: get_file_diff_lines(f) for f in files}

    files_to_process = list(all_changes.keys())

    if not files_to_process:
        print("[INFO] No modified source files to process.")
        return

    print(f"[INFO] Tagging with: {tag}\n")

    for file in files_to_process:
        process_file(file, tag, dry_run=dry_run, override_lines=all_changes[file])

    if dry_run:
        print("\n[DRY-RUN] Complete. No files were modified.")
    else:
        print("\n[SUCCESS] Tagging complete.")

def process_file(filepath, tag, dry_run=False, override_lines=None):
    ext = Path(filepath).suffix.lower()
    comment_char = COMMENT_CHARS[ext]
    changes = override_lines if override_lines is not None else get_file_diff_lines(filepath)

    with open(filepath, 'r') as f:
        lines = f.readlines()

    updated_lines = []
    modified = False

    for idx, line in enumerate(lines, start=1):
        original = line.rstrip('\n')
        modified_line = original
        update_needed = False

        if idx in changes:
            existing_all_tags = extract_tags(original)
            if tag in existing_all_tags:
                if dry_run:
                    print(f"[SKIP]    {filepath}:{idx} (tag already exists)")
                update_needed = False
            else:
                if is_code_line(original, ext):
                    match = re.search(rf'{re.escape(comment_char)}\s*(.*)$', original)
                    tags = extract_tags(match.group(1)) if match else []
                    modified_line = align_tags_with_comments(original, tags, comment_char, tag)
                    update_needed = True

                elif should_tag_comment_line(original, ext):
                    match = re.search(rf'{re.escape(comment_char)}\s*(.*)$', original)
                    tags = extract_tags(match.group(1)) if match else []
                    modified_line = align_tags_to_col_80_preserve_deleted(original, tags, comment_char, tag)
                    update_needed = True

        if update_needed:
            modified = True
            log_type = "DRY-RUN" if dry_run else "TAGGED"
            print(f"[{log_type}] {filepath}:{idx}\n  BEFORE: {original}\n  AFTER:  {modified_line}\n")

        updated_lines.append(modified_line + '\n')

    if modified and not dry_run:
        with open(filepath, 'w') as f:
            f.writelines(updated_lines)
        subprocess.run(['git', 'add', filepath])
