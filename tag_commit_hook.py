#!/usr/bin/env python
import os
import re
import subprocess
import sys
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
DRY_RUN = '--dry-run' in sys.argv

def get_branch_tag():
    try:
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
        match = re.search(r'([A-Z]+-\d+)', branch)
        return match.group(1) if match else None
    except subprocess.CalledProcessError:
        return None

def get_staged_files():
    output = subprocess.check_output(['git', 'diff', '--cached', '--name-only']).decode()
    return [line.strip() for line in output.splitlines() if Path(line.strip()).suffix in COMMENT_CHARS]

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

def should_tag_comment_line(line, ext):
    """Check if the line starts with a valid 'deleted' comment tag for the given language."""
    comment_char = COMMENT_CHARS.get(ext, '').lower()
    stripped = line.strip().lower()
    return (
        stripped.startswith(f"{comment_char}deleted")  or 
        stripped.startswith(f"{comment_char} deleted") or
        stripped.startswith(f"{comment_char}delete")   or 
        stripped.startswith(f"{comment_char} delete")  or
        stripped.startswith(f"{comment_char}removed")  or
        stripped.startswith(f"{comment_char} removed") or
        stripped.startswith(f"{comment_char}remove")   or
        stripped.startswith(f"{comment_char} remove")
    )

def align_tags_to_col_80_preserve_deleted(line, tags, comment_char, new_tag):
    """Align tags so they end at column 80 without breaking lines that start with a comment prefix."""
    if new_tag not in tags:
        tags.append(new_tag)

    # Build new tag block
    tag_block = f"{comment_char} {', '.join(tags)}"

    # Strip existing trailing tag block (but NOT the first comment section like '# deleted')
    # We assume any tag block starts after 40 characters
    tag_search_start = 40
    tag_pos = line.find(comment_char, tag_search_start)

    if tag_pos != -1:
        code_part = line[:tag_pos].rstrip()
    else:
        code_part = line.rstrip()

    total_len = len(code_part) + 1 + len(tag_block)
    if total_len > MAX_LINE_LENGTH:
        return f"{code_part} {tag_block}"
    else:
        padding = MAX_LINE_LENGTH - len(code_part) - len(tag_block)
        return f"{code_part}{' ' * padding}{tag_block}"

def extract_tags(comment):
    return [t.strip() for t in comment.split(',') if re.match(r'[A-Z]+-\d+', t)]

def process_file(filepath, tag):
    ext = Path(filepath).suffix
    comment_char = COMMENT_CHARS[ext]
    changes = get_file_diff_lines(filepath)

    with open(filepath, 'r') as f:
        lines = f.readlines()

    updated_lines = []
    modified = False

    for idx, line in enumerate(lines, start=1):
        original = line.rstrip('\n')
        modified_line = original
        update_needed = False

        if idx in changes:
            if is_code_line(original, ext):
                # Handle existing comment
                match = re.search(rf'{re.escape(comment_char)}\s*(.*)$', original)
                if match:
                    tags = extract_tags(match.group(1))
                    base = original[:match.start()]
                else:
                    tags = []
                    base = original

                modified_line = align_tags_to_col_80_preserve_deleted(original, tags, comment_char, tag)
                update_needed = True

            elif should_tag_comment_line(original, ext):
                # Don't strip any part of the line — preserve it all
                match = re.search(rf'{re.escape(comment_char)}\s*(.*)$', original)
                tags = extract_tags(match.group(1)) if match else []
                modified_line = align_tags_to_col_80_preserve_deleted(original, tags, comment_char, tag)
                update_needed = True

        if update_needed:
            modified = True
            if DRY_RUN:
                print(f"[DRY-RUN] {filepath}:{idx} --> {modified_line}")
            else:
                print(f"[TAGGED]  {filepath}:{idx} --> {modified_line}")

        updated_lines.append(modified_line + '\n')

    if modified and not DRY_RUN:
        with open(filepath, 'w') as f:
            f.writelines(updated_lines)
        subprocess.run(['git', 'add', filepath])

def is_code_line(line, ext):
    stripped = line.strip()
    if not stripped:
        return False
    if ext in COMMENT_CHARS:
        return not stripped.startswith(COMMENT_CHARS[ext])
    return False

def main():
    tag = get_branch_tag()
    if not tag:
        print("[WARN]  No JIRA-style tag found in branch name.")
        sys.exit(1)

    files = get_staged_files()
    if not files:
        print("[SUCCESS] No staged files matching language targets.")
        sys.exit(0)

    print(f"[INFO] Tagging with: {tag}\n")
    for file in files:
        process_file(file, tag)

    if DRY_RUN:
        print("\n[DRY-RUN] Dry-run complete. No files were modified.")
    else:
        print("\n[SUCCESS] Pre-commit tagging completed.")

if __name__ == "__main__":
    main()