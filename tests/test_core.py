"""
test_core.py — Unit tests for LazyTag core tagging logic
"""

import pytest
from core import (
    extract_tags,
    align_tags_with_comments,
    align_tags_to_col_80_preserve_deleted,
    should_tag_comment_line,
    is_code_line,
    COMMENT_CHARS,
    MAX_LINE_LENGTH
)
from pathlib import Path

def test_extract_tags():
    assert extract_tags("ABC-123") == ["ABC-123"]
    assert extract_tags("ABC-123, XYZ-999") == ["ABC-123", "XYZ-999"]
    assert extract_tags("not-a-tag, DEF-1") == ["DEF-1"]
    assert extract_tags("") == []

def test_align_tags_with_existing_comment():
    line = "int x = 10; // units: feet"
    tags = ["ABC-123"]
    result = align_tags_with_comments(line, tags.copy(), "//", "XYZ-999")
    assert "units: feet" in result
    assert "ABC-123" in result and "XYZ-999" in result
    assert len(result) <= MAX_LINE_LENGTH or result.endswith("XYZ-999")

def test_align_tags_preserve_deleted_line():
    line = "# deleted print('Done')                                    # OLD-1"
    tags = ["OLD-1"]
    result = align_tags_to_col_80_preserve_deleted(line, tags.copy(), "#", "NEW-2")
    assert "# deleted print('Done')" in result
    assert "OLD-1" in result and "NEW-2" in result
    assert len(result) == MAX_LINE_LENGTH or result.endswith("NEW-2")

def test_should_tag_comment_line():
    assert should_tag_comment_line("//deleted something", ".cpp")
    assert should_tag_comment_line("// deleted something", ".c")
    assert should_tag_comment_line("# deleted line", ".py")
    assert should_tag_comment_line("--deleted text", ".adb")
    assert not should_tag_comment_line("//normal comment", ".cpp")
    assert not should_tag_comment_line("deleted x = 10", ".py")

def test_is_code_line():
    assert is_code_line("int x = 10;", ".c")
    assert is_code_line("   let x = 5;", ".rs")
    assert not is_code_line("// comment", ".cpp")
    assert not is_code_line("", ".py")

def test_case_insensitive_extensions():
    path = Path("file.ADB")
    assert path.suffix.lower() in COMMENT_CHARS
    assert COMMENT_CHARS[path.suffix.lower()] == "--"

def test_extract_tags_handles_spaces_and_commas():
    assert extract_tags("// SMR-1010") == ["SMR-1010"]
    assert extract_tags("//SMR-1010") == ["SMR-1010"]
    assert extract_tags("// SMR-1010, SMR-1010") == ["SMR-1010", "SMR-1010"]
    assert extract_tags("// SMR-1010 XYZ-999") == ["SMR-1010", "XYZ-999"]

def test_extract_tags_handles_punctuation():
    assert extract_tags("//SMR-1010") == ["SMR-1010"]
    assert extract_tags("#SMR-1010") == ["SMR-1010"]
    assert extract_tags("--SMR-1010") == ["SMR-1010"]