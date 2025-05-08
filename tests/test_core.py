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
    MAX_LINE_LENGTH,
    get_merge_base
)
from pathlib import Path
from unittest import mock

def test_extract_tags():
    assert extract_tags("ABC-123") == ["ABC-123"]
    assert extract_tags("ABC-123, XYZ-999") == ["ABC-123", "XYZ-999"]
    assert extract_tags("not-a-tag, DEF-1") == ["DEF-1"]
    assert extract_tags("") == []

# def test_align_tags_with_existing_comment():
#     line = "int x = 10; // units: feet"
#     tags = ["ABC-123"]
#     result = align_tags_with_comments(line, tags.copy(), "//", "XYZ-999")
#     assert "units: feet" in result
#     assert "ABC-123" in result and "XYZ-999" in result
#     assert len(result) <= MAX_LINE_LENGTH or result.endswith("XYZ-999")

def test_align_tags_with_existing_comment_2():
    line = "int x = 10; // units: feet, ABC-123"
    result = align_tags_with_comments(line, [], "//", "XYZ-999")
    assert "units: feet" in result
    assert "ABC-123" in result and "XYZ-999" in result

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

def test_does_not_duplicate_existing_tag():
    line = "int x = 10; // HMR-101, SMR-1010"
    tags = ["HMR-101", "SMR-1010"]
    result = align_tags_with_comments(line, tags.copy(), "//", "SMR-1010")
    assert result.count("SMR-1010") == 1

def test_no_duplicate_when_tag_already_present():
    line = "int x = 10; // HMR-101, SMR-1010"
    tags = ["HMR-101", "SMR-1010"]
    result = align_tags_with_comments(line, tags.copy(), "//", "SMR-1010")
    assert result.count("SMR-1010") == 1
    assert "HMR-101" in result

def test_no_duplicate_when_tag_in_original_comment():
    line = "int x = 10; //SMR-1010"
    tags = []
    result = align_tags_with_comments(line, tags.copy(), "//", "SMR-1010")
    assert result.count("SMR-1010") == 1

def test_tag_added_if_not_present():
    line = "int x = 10;"
    tags = []
    result = align_tags_with_comments(line, tags.copy(), "//", "SMR-1010")
    assert "SMR-1010" in result
    assert result.count("SMR-1010") == 1

def test_multiple_tags_deduplicated():
    line = "int x = 10; // HMR-101, SMR-1010"
    tags = ["HMR-101", "SMR-1010"]
    result = align_tags_with_comments(line, tags + ["SMR-1010"], "//", "SMR-1010")
    assert result.count("SMR-1010") == 1
    assert result.count("HMR-101") == 1

def test_formatting_preserved_on_comment_with_new_tag():
    line = "int x = 10; // original comment"
    tags = ["original comment"]
    result = align_tags_with_comments(line, tags.copy(), "//", "SMR-2023")
    assert "original comment" in result
    assert "SMR-2023" in result

def test_tag_appends_with_comma_not_extra_comment():
    line = 'print("Hello World")          # Ian-001'
    result = align_tags_with_comments(line, ["Ian-001"], "#", "Ian-002")
    assert result.count("#") == 1
    assert "Ian-001" in result
    assert "Ian-002" in result
    assert "# Ian-001, Ian-002" in result

def test_get_merge_base_with_fallback():
    with mock.patch("subprocess.run") as mock_run:
        # Simulate origin/main failing, main succeeding
        mock_run.side_effect = [
            mock.Mock(returncode=1, stdout=""),                      # origin/main fails
            mock.Mock(returncode=0, stdout="abc123fallback\n")       # main succeeds
        ]

        result = get_merge_base("origin/development")
        assert result == "abc123fallback"
        assert mock_run.call_count == 2
        mock_run.assert_any_call(["git", "merge-base", "HEAD", "origin/development"], capture_output=True, text=True)
        mock_run.assert_any_call(["git", "merge-base", "HEAD", "development"], capture_output=True, text=True)