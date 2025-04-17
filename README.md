# LazyTag

**LazyTag** is a CLI tool and Git pre-commit hook that automatically appends Jira-style issue tags to modified lines of source code. It supports multiple languages, aligns tags to column 80 where possible, and helps keep traceability in your codebase.

---

## 🚀 Features

- ✅ Append issue tags to modified lines of staged files.
- ✅ Extract tag from branch name (e.g., `SMR-1010-description` → `SMR-1010`).
- ✅ Manually override tag with `--tag` argument.
- ✅ Smart alignment: tags are appended and aligned to column 80.
- ✅ Preserves existing comments and tags.
- ✅ Special support for `# deleted` or `// deleted` comment lines.
- ✅ Dry-run support for safe previewing.
- ✅ Installable as a Git pre-commit hook.

---

## 🛠 Upcoming Features

- 📝 Auto-update copyright headers across source files
- 🧾 Auto-update structured revision history blocks in supported formats

---

## 📦 Installation

### 🔧 Prerequisites
- Python 3.7+
- Git (used internally to get branch and diff info)

### 🔁 Install from source
```bash
git clone https://github.com/semarova/LazyTag.git
cd lazytag
pip install .
# or with dev extras:
pip install .[dev]
```

### 📜 Install as a Git Hook
```bash
lazytag install
```
This installs a pre-commit hook at `.git/hooks/pre-commit` that automatically runs `lazytag tag` before every commit.

---

## 🧑‍💻 Usage

### Append tags based on current branch:
```bash
lazytag tag
```

### Manually specify a tag:
```bash
lazytag tag --tag ABC-123
```

### Preview (no file changes):
```bash
lazytag tag --dry-run
```

### Help & Version
```bash
lazytag --help
lazytag --version
```

---

## 🧠 How It Works
- Parses staged files.
- Identifies modified lines (excluding whitespace-only changes).
- Adds or appends issue tags inline as comments.
- Preserves existing comments and tags.
- Aligns tags to column 80 if possible, or places them after code.
- Specially handles `// deleted` or `# deleted` comment markers.

---

## 💡 Supported Languages
| Language | Extensions            | Comment Style |
|----------|------------------------|----------------|
| C/C++    | `.c`, `.cpp`, `.h`     | `//`           |
| Rust     | `.rs`                  | `//`           |
| Python   | `.py`                  | `#`            |
| Ada      | `.adb`, `.ads`, `.ada` | `--`           |

Case-insensitive extensions are fully supported (e.g., `.CPP`, `.PY`).

---

## 📁 Project Structure

```
lazytag/
├── lazytag.py           # CLI entrypoint (tag, install)
├── core.py              # Core tagging logic
├── installer.py         # Hook installer
├── setup.py             # Package definition
├── tests/
│   └── test_core.py     # Unit tests for tag logic
├── README.md
└── requirements.txt     # Dev dependencies (pytest, etc.)
```

---

## 🧪 Testing

Run the test suite using `pytest`:
```bash
pip install -r requirements.txt
pytest
```

---

## 🛠 Contributing

Feel free to fork, improve, and submit a PR! Contributions are welcome and appreciated.

---

## 📄 License
MIT License. Use it, modify it, make it yours.

---

## ✨ Example

Before:
```c
int height = 10; // units: feet
```
After:
```c
int height = 10; // units: feet                         // SMR-1010
```

Deleted lines:
```python
# deleted print("Done")                                  # SMR-1010
```

---

Made with 🧠 and ⚙️ by developers who hate forgetting to tag their commits.

