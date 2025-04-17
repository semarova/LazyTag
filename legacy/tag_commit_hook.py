#!/usr/bin/env python
"""
Git Pre-Commit Hook: Tag Source Code with Jira Issue ID

Features:
- Extracts Jira-style tag (e.g., SMR-1010) from the current branch name.
- Adds or appends tags to modified lines of source code (C/C++, Rust, Python, Ada).
- Appends tag blocks while preserving existing comments.
- Aligns tags to column 80 if possible.
- Tags special deleted-comment lines (e.g., "# deleted ...").
- Automatically re-stages modified files.
- Supports dry-run mode (`--dry-run`).
- Logs all tagging activity per line and file.
"""

import os
import re
import subprocess
import sys
import argparse
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
DRY_RUN = False  # Will be set inside main() by argparse


def get_branch_tag():
    """Extract the Jira-style tag from the current branch name."""
    try:
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode().strip()
        match = re.search(r'([A-Z]+-\d+)', branch)
        return match.group(1) if match else None
    except subprocess.CalledProcessError:
        return None


def get_staged_files():
    """Return a list of staged source files with supported extensions."""
    output = subprocess.check_output(['git', 'diff', '--cached', '--name-only']).decode()
    return [line.strip() for line in output.splitlines() if Path(line.strip()).suffix.lower() in COMMENT_CHARS]


def get_file_diff_lines(filename):
    """Return the line numbers that are modified in the staged diff for a file."""
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


def extract_tags(comment):
    """Extract all Jira-style tags from an inline comment block."""
    return [t.strip() for t in comment.split(',') if re.match(r'[A-Z]+-\d+', t)]


def should_tag_comment_line(line, ext):
    """Check if this comment line is a 'deleted' marker (e.g., # deleted ...)."""
    comment_char = COMMENT_CHARS.get(ext, '').lower()
    stripped = line.strip().lower()
    return stripped.startswith(f"{comment_char}deleted") or stripped.startswith(f"{comment_char} deleted")


def is_code_line(line, ext):
    """Return True if the line is a valid code line (not blank or comment)."""
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith(COMMENT_CHARS[ext])


def align_tags_with_comments(line, tags, comment_char, new_tag):
    """Preserve existing inline comments and append Jira tags at the end, aligned to column 80."""
    if new_tag not in tags:
        tags.append(new_tag)

    tag_block = f"{comment_char} {', '.join(tags)}"
    line = line.rstrip()

    if comment_char in line:
        split_index = line.find(comment_char)
        code_part = line[:split_index].rstrip()
        comment_part = line[split_index:].rstrip()
    else:
        code_part = line
        comment_part = ""

    # Combine original comment and new tag
    if comment_part:
        combined_comment = f"{comment_part} {tag_block}"
    else:
        combined_comment = f"{tag_block}"

    total_len = len(code_part) + 1 + len(combined_comment)
    if total_len > MAX_LINE_LENGTH:
        return f"{code_part} {combined_comment}"
    else:
        padding = MAX_LINE_LENGTH - len(code_part) - len(combined_comment)
        return f"{code_part}{' ' * padding}{combined_comment}"


def align_tags_to_col_80_preserve_deleted(line, tags, comment_char, new_tag):
    """Align tags to column 80 for 'deleted' lines without removing their original content."""
    if new_tag not in tags:
        tags.append(new_tag)

    tag_block = f"{comment_char} {', '.join(tags)}"
    line = line.rstrip()

    # Assume first 40 characters are code, search for comment char after
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


def process_file(filepath, tag):
    """Process and tag modified lines in a source file."""
    ext = Path(filepath).suffix.lower()
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
                # Extract tags from any existing inline comment
                match = re.search(rf'{re.escape(comment_char)}\s*(.*)$', original)
                tags = extract_tags(match.group(1)) if match else []
                modified_line = align_tags_with_comments(original, tags, comment_char, tag)
                update_needed = True

            elif should_tag_comment_line(original, ext):
                # Handle "# deleted ..." or "// deleted ..." lines
                match = re.search(rf'{re.escape(comment_char)}\s*(.*)$', original)
                tags = extract_tags(match.group(1)) if match else []
                modified_line = align_tags_to_col_80_preserve_deleted(original, tags, comment_char, tag)
                update_needed = True

        if update_needed:
            modified = True
            log_type = "DRY-RUN" if DRY_RUN else "TAGGED"
            print(f"[{log_type}] {filepath}:{idx} --> {modified_line}")

        updated_lines.append(modified_line + '\n')

    if modified and not DRY_RUN:
        with open(filepath, 'w') as f:
            f.writelines(updated_lines)
        subprocess.run(['git', 'add', filepath])  # Restage


def main():
    parser = argparse.ArgumentParser(description="Git Pre-Commit Hook: Append Jira tags to modified lines.")
    parser.add_argument('--tag', help="Preferred Jira tag to use (overrides tag from branch name)")
    parser.add_argument('--dry-run', action='store_true', help="Preview changes without modifying files")
    args = parser.parse_args()

    global DRY_RUN
    DRY_RUN = args.dry_run

    tag = args.tag if args.tag else get_branch_tag()
    if not tag:
        print("[ERROR] No Jira-style tag found (use --tag or a branch like SMR-1010-feature).")
        sys.exit(1)

    files = get_staged_files()
    if not files:
        print("[INFO] No staged source files to process.")
        sys.exit(0)

    print(f"[INFO] Tagging with: {tag}\n")
    for file in files:
        process_file(file, tag)

    if DRY_RUN:
        print("\n[DRY-RUN] Complete. No files were modified.")
    else:
        print("\n[SUCCESS] Pre-commit tagging completed.")


if __name__ == "__main__":
    main()