import pytest
from tag_commit_hook import extract_tags, align_tag, is_code_line, should_tag_comment_line

def test_extract_tags():
    assert extract_tags("SMR-1001") == ["SMR-1001"]
    assert extract_tags("SMR-1001, SMR-1002") == ["SMR-1001", "SMR-1002"]
    assert extract_tags("junk, SMR-2000") == ["SMR-2000"]
    assert extract_tags("") == []

def test_align_tag_ends_at_80():
    code = "int x = 10;"
    tags = ["SMR-1001"]
    result = align_tag(code, tags.copy(), "//", "SMR-1001")
    assert len(result) <= 80

def test_align_tag_appends_if_too_long():
    long_code = "x = " + "1" * 70  # force overflow
    tags = []
    result = align_tag(long_code, tags.copy(), "#", "SMR-2020")
    assert "SMR-2020" in result
    assert result.startswith("x = ")

def test_align_deleted_line_with_existing_tags():
    line = "# deleted print('Now, let us split the bill.')                                    # SCR-001"
    tags = ["SCR-001"]
    new_tag = "SCR-006"
    result = align_tags_to_col_80_preserve_deleted(line, tags.copy(), "#", new_tag)
    assert result.startswith("# deleted print")
    assert "# SCR-001, SCR-006" in result
    assert len(result) == 80

def test_is_code_line_true_for_code():
    assert is_code_line("int x = 10;", ".c") is True
    assert is_code_line("    int y;", ".cpp") is True

def test_is_code_line_false_for_comment():
    assert is_code_line("// this is a comment", ".cpp") is False
    assert is_code_line("   // comment here", ".cpp") is False
    assert is_code_line("-- Ada comment", ".ada") is False
    assert is_code_line("", ".c") is False

def test_should_tag_comment_line_valid_cases():
    assert should_tag_comment_line("//deleted int x = 10;", ".c") is True
    assert should_tag_comment_line("// deleted int x = 10;", ".cpp") is True

def test_should_tag_comment_line_invalid_cases():
    assert should_tag_comment_line("// something else", ".cpp") is False
    assert should_tag_comment_line("--deleted", ".ada") is False

def test_preserve_existing_inline_comment():
    line = "int x = 10; // units: feet"
    tags = []
    tag = "SMR-1010"
    result = align_tags_with_comments(line, tags.copy(), "//", tag)
    assert "units: feet" in result
    assert "SMR-1010" in result
    assert len(result) <= 80 or result.endswith(f"// SMR-1010")