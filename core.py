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

def extract_tags(comment):
    """Extract Jira-style tags from a comment string using robust splitting and cleanup."""
    parts = re.split(r'[,\s]+', comment)
    tags = []
    for part in parts:
        cleaned = part.lstrip("/#-")  # Strip leading slashes, hashes, dashes
        if re.fullmatch(r'[A-Z]+-\d+', cleaned):
            tags.append(cleaned)
    return tags

def should_tag_comment_line(line, ext):
    comment_char = COMMENT_CHARS.get(ext, '').lower()
    stripped = line.strip().lower()
    return stripped.startswith(f"{comment_char}deleted") or stripped.startswith(f"{comment_char} deleted")

def is_code_line(line, ext):
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith(COMMENT_CHARS[ext])

def align_tags_with_comments(line, tags, comment_char, new_tag):
    """Preserve non-tag comment content, and append tag block only once."""
    all_existing_tags = extract_tags(line)
    if new_tag in all_existing_tags:
        return line  # Skip tagging if already present

    # Parse and split comment
    line = line.rstrip()
    if comment_char in line:
        split_index = line.find(comment_char)
        code_part = line[:split_index].rstrip()
        comment_part = line[split_index:].strip()
    else:
        code_part = line
        comment_part = ""

    # Extract tags from comment and remove them
    raw_parts = re.split(r'[,\s]+', comment_part)
    non_tag_comment = " ".join([
        part for part in raw_parts
        if not re.fullmatch(r'[A-Z]+-\d+', part.strip("/#-"))
    ])

    # Build updated tag list
    existing_tags = extract_tags(comment_part)
    if new_tag not in existing_tags:
        existing_tags.append(new_tag)

    tag_block = f"{comment_char} {', '.join(existing_tags)}"

    # Combine everything
    if non_tag_comment.strip() and not non_tag_comment.strip().startswith(comment_char):
        non_tag_comment = f"{comment_char} {non_tag_comment.strip()}"

    combined_comment = f"{non_tag_comment} {tag_block}".strip()

    total_len = len(code_part) + 1 + len(combined_comment)
    if total_len > MAX_LINE_LENGTH:
        return f"{code_part} {combined_comment}"
    else:
        padding = MAX_LINE_LENGTH - len(code_part) - len(combined_comment)
        return f"{code_part}{' ' * padding}{combined_comment}"

def align_tags_to_col_80_preserve_deleted(line, tags, comment_char, new_tag):
    if new_tag not in tags:
        tags.append(new_tag)

    tag_block = f"{comment_char} {', '.join(tags)}"
    line = line.rstrip()

    tag_search_start = 40
    tag_pos = line.find(comment_char, tag_search_start)
    code_part = line[:tag_pos].rstrip() if tag_pos != -1 else line.rstrip()

    total_len = len(code_part) + 1 + len(tag_block)
    if total_len > MAX_LINE_LENGTH:
        return f"{code_part} {tag_block}"
    else:
        padding = MAX_LINE_LENGTH - len(code_part) - len(tag_block)
        return f"{code_part}{' ' * padding}{tag_block}"

def process_file(filepath, tag, dry_run=False):
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
            # If the tag is already anywhere in the line, skip tagging
            existing_all_tags = extract_tags(original)
            if tag in existing_all_tags:
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
            print(f"[{log_type}] {filepath}:{idx} --> {modified_line}")

        updated_lines.append(modified_line + '\n')

    if modified and not dry_run:
        with open(filepath, 'w') as f:
            f.writelines(updated_lines)
        subprocess.run(['git', 'add', filepath])

def process_files_with_tag(preferred_tag=None, dry_run=False):
    tag = preferred_tag or get_branch_tag()
    if not tag:
        print("[ERROR] No Jira-style tag found (use --tag or a branch like ABC-1234-feature)")
        return

    files = get_staged_files()
    if not files:
        print("[INFO] No staged source files to process.")
        return

    print(f"[INFO] Tagging with: {tag}\n")
    for file in files:
        process_file(file, tag, dry_run)

    if dry_run:
        print("\n[DRY-RUN] Complete. No files were modified.")
    else:
        print("\n[SUCCESS] Tagging complete.")