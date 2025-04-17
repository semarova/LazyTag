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
    """Preserve original inline comment and append tags, avoiding duplicate comment chars."""
    all_existing_tags = extract_tags(line)
    if new_tag in all_existing_tags:
        return line  # Already tagged

    line = line.rstrip()

    # Find first comment position
    split_index = line.find(comment_char)
    if split_index != -1:
        code_part = line[:split_index].rstrip()
        comment_tail = line[split_index:].replace(comment_char, '').strip()
    else:
        code_part = line
        comment_tail = ""

    # Split and clean comment tail
    parts = re.split(r'[,\s]+', comment_tail)
    comment_words = []
    existing_tags = []

    for part in parts:
        cleaned = part.strip("/#-")
        if re.fullmatch(r'[A-Z]+-\d+', cleaned):
            existing_tags.append(cleaned)
        else:
            comment_words.append(part)

    if new_tag not in existing_tags:
        existing_tags.append(new_tag)

    # Rebuild single comment block
    comment_content = " ".join(comment_words).strip()
    tag_block = f"{', '.join(existing_tags)}"

    if comment_content:
        final_comment = f"{comment_char} {comment_content} {comment_char} {tag_block}"
    else:
        final_comment = f"{comment_char} {tag_block}"

    # Align to 80
    total_len = len(code_part) + 1 + len(final_comment)
    if total_len > MAX_LINE_LENGTH:
        return f"{code_part} {final_comment}"
    else:
        padding = MAX_LINE_LENGTH - len(code_part) - len(final_comment)
        return f"{code_part}{' ' * padding}{final_comment}"

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
    tagged_lines = 0
    skipped_lines = 0

    for idx, line in enumerate(lines, start=1):
        original = line.rstrip('\n')
        modified_line = original
        update_needed = False

        if idx in changes:
            existing_all_tags = extract_tags(original)
            if tag in existing_all_tags:
                skipped_lines += 1
                if dry_run:
                    print(f"[SKIP]    {filepath}:{idx} (tag already exists)")
                update_needed = False
            else:
                if is_code_line(original, ext):
                    comment_parts = original.split(comment_char)
                    if len(comment_parts) >= 2:
                        code_part = comment_parts[0].rstrip()
                        comment_segments = comment_parts[1:]
                        non_tags = []
                        tag_candidates = []
                        for segment in comment_segments:
                            segment = segment.strip()
                            if any(re.fullmatch(r'[A-Z]+-\d+', t.strip('/#-')) for t in segment.split()):
                                tag_candidates.append(segment)
                            else:
                                non_tags.append(segment)

                        all_tag_text = ' '.join(tag_candidates)
                        tags = extract_tags(all_tag_text)
                        if tag not in tags:
                            tags.append(tag)

                        new_comment = f" {comment_char} {non_tags[0]} {comment_char} {', '.join(tags)}" if non_tags else f" {comment_char} {', '.join(tags)}"
                        total_len = len(code_part) + len(new_comment) + 1
                        if total_len > MAX_LINE_LENGTH:
                            modified_line = f"{code_part}{new_comment}"
                        else:
                            padding = MAX_LINE_LENGTH - len(code_part) - len(new_comment)
                            modified_line = f"{code_part}{' ' * padding}{new_comment}"

                        update_needed = True
                    else:
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
            tagged_lines += 1
            log_type = "DRY-RUN" if dry_run else "TAGGED"
            print(f"[{log_type}] {filepath}:{idx}\n  BEFORE: {original}\n  AFTER:  {modified_line}\n")

        updated_lines.append(modified_line + '\n')

    if modified and not dry_run:
        with open(filepath, 'w') as f:
            f.writelines(updated_lines)
        subprocess.run(['git', 'add', filepath])

    return tagged_lines, skipped_lines

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