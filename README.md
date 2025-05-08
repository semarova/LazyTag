# LazyTag

**LazyTag** is a CLI tool that automatically appends Jira-style tags to modified lines of source code. It’s ideal for pre-commit tagging workflows and integrates cleanly with Git. It supports multiple languages, aligns tags to column 80 where possible, and helps keep traceability in your codebase.

---

## ✨ Features

- ✅ Append JIRA issue tags to modified lines of staged files.
- ✅ Extract tag from branch name (e.g., `SMR-1010-description` → `SMR-1010`).
- ✅ Manually override tag with `--tag` argument.
- ✅ Smart alignment: tags are appended and aligned to column 80.
- ✅ Preserves existing comments and tags.
- ✅ Special support for `# deleted` or `// moved` comment lines.
- ✅ Dry-run support for safe previewing.
- ✅ Installable as a Git pre-commit hook.
- ✅ Compare against a base branch with `--scope base`
- ✅ Auto fallback from `origin/development` → `main` if base branch not found
- ✅ Clean test suite in `tests/` with `pytest`

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

This installs a pre-commit hook at .git/hooks/pre-commit that automatically runs lazytag tag before every commit. **Not recommended for everyone. Use with caution!**

``` bash
lazytag install
```


## 🧑‍💻 Usage
Append tags based on currently staged lines:
``` bash
lazytag tag
```

Compare against base branch (e.g., origin/development → HEAD):
``` bash
lazytag tag --scope base
```

Specify custom base branch:
```bash
lazytag tag --scope base --base-branch origin/feature-branch
``` 

Manually specify a tag:
``` bash
lazytag tag --tag ABC-123
``` 

Preview changes only (dry run):
``` bash
lazytag tag --dry-run
```

Preview changes only (dry run) with manually specified tag:
``` bash
lazytag tag --dry-run --tag ABC-123
```

Help & Version
``` bash
lazytag --help
lazytag --version
```

## 🧠 How It Works
- Parses either staged or diffed files from a base commit.
- Identifies modified lines (excluding whitespace-only changes).
- Adds or appends Jira-style tags inline as comments.
- Preserves existing comment spacing and tags.
- Aligns tags to column 80 if feasible.
- Fallbacks to main if base branch like origin/development is missing.

## 💡 Supported Languages
| Language | Extensions            | Comment Style |
|----------|------------------------|----------------|
| C/C++    | `.c`, `.cpp`, `.h`     | `//`           |
| Rust     | `.rs`                  | `//`           |
| Python   | `.py`                  | `#`            |
| Ada      | `.adb`, `.ads`, `.ada` | `--`           |

Case-insensitive extensions are fully supported (e.g., .CPP, .PY).

## 📁 Project Structure
```bash
lazytag/
├── lazytag.py           # CLI entrypoint (tag, install)
├── core.py              # Core tagging logic
├── installer.py         # Hook installer
├── setup.py             # Package definition
├── pyproject.toml       # PEP 621 metadata
├── README.md
├── requirements.txt     # Dev dependencies (pytest, etc.)
├── MANIFEST.in
└── tests/
    ├── __init__.py
    └── test_core.py     # Unit tests for tag logic
```

## 🧪 Testing
Run the test suite using pytest:

``` bash
pip install -r requirements.txt
pytest -v --ignore=legacy
```

## 🛠 Contributing
Feel free to fork, improve, and submit a PR! Contributions are welcome and appreciated.

## 📄 License
MIT License. Use it, modify it, make it yours.

## ✨ Example
Before:

``` c
int height = 10; // units: feet
```

After:

``` c
int height = 10; // units: feet                         // SMR-1010
```

Deleted lines:

``` python
# deleted print("Done")                                  # SMR-1010
```

Made with 🧠 and ⚙️ by developers who hate forgetting to tag their commits.