# LazyTag
 Tags changes with Jira issues style tags. 

# 🔖 LazyTag a Git Pre-Commit Hook with JIRA-style Tag Inserter

This pre-commit hook automatically injects JIRA-style issue tags (e.g. `SMR-1010`) into modified source code lines during a Git commit. It aligns tags to column 80 when possible and helps enforce traceability across your codebase.

---

## 🚀 Features

- Extracts JIRA issue tag from the current Git branch name.
- Tags modified lines of supported languages (C/C++, Python, Rust, Ada).
- Automatically aligns tag comments to column 80 when possible.
- Preserves existing tags and appends new ones (e.g., `// SMR-1001, SMR-1010`).
- Skips whitespace-only changes.
- Tags only the last line of multiline statements.
- Adds tags to comment lines only if they begin with `//deleted` or `// deleted`.
- Automatically restages modified files for commit.
- Supports dry-run mode for safe testing.
- Logs all tagged lines during commit.

---

## 🛠️ Supported Languages & Comment Styles

| Extension | Language | Comment Style |
|-----------|----------|----------------|
| `.c`, `.cpp`, `.h`, `.hpp` | C/C++ | `//` |
| `.rs` | Rust | `//` |
| `.py` | Python | `#` |
| `.adb`, `.ads`, `.ada` | Ada | `--` |

---

## 📦 Installation

### 1. Clone or copy this repo into your project.

### 2. Install the pre-commit hook:

```bash
python install_pre_commit_hook.py
This script will:

Install the tag_commit_hook.py as .git/hooks/pre-commit

Backup any existing hook to .pre-commit.bak

Make the hook executable

## ✅ Usage
Make changes in your code, stage them, and commit as usual:

``` bash
git checkout -b SMR-1010-add-logging
git add my_file.c
git commit -m "Refactor: rename variable"
```
If a line was changed, it will be updated like:

``` c
int x = 10;
// becomes:
int limit = 10;                                              // SMR-1010
```

### 🧪 Dry Run Mode
To preview what would be tagged without modifying any files:

``` bash
python tag_commit_hook.py --dry-run
```
### 🧪 Testing
Install dev requirements and run the test suite:

bash
Copy
Edit
pip install -r requirements.txt
pytest
All unit tests are under /tests.

## 🗂 Project Structure
``` bash
.
├── tag_commit_hook.py           # Main tagging logic
├── install_pre_commit_hook.py   # Installer utility
├── requirements.txt             # Optional: dev dependencies
├── tests/
│   └── test_tag_commit_hook.py  # Unit tests
└── .git/hooks/pre-commit        # Installed hook (auto-generated)
```

## 👥 Contributing

Have improvements or fixes? Please do!

Fork the repo @ ...

Create your branch: git checkout -b feature/improve-hook

Commit your changes

Push and open a PR. 

## 💡 Ideas for Future Enhancements

Automatic updates for copyrigth headers.
Automatic updates for Revision History block.