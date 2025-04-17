#!/usr/bin/env python
"""
lazytag.py — Main CLI for LazyTag

Supports subcommands:
- tag       → Append tags to modified lines
- install   → Install lazytag as a Git pre-commit hook
"""

import argparse
from core import process_files_with_tag
from installer import install_hook

__version__ = "0.1.0"

def main():
    parser = argparse.ArgumentParser(
        description="LazyTag: Automatically append Jira-style tags to modified code lines."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"lazytag v{__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcommand: tag
    tag_parser = subparsers.add_parser("tag", help="Tag modified staged lines")
    tag_parser.add_argument(
        "--tag",
        help="Manually specify the tag (e.g., ABC-1234). Overrides branch name tag."
    )
    tag_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )

    # Subcommand: install
    install_parser = subparsers.add_parser("install", help="Install lazytag as a pre-commit hook")

    args = parser.parse_args()

    if args.command == "tag":
        process_files_with_tag(preferred_tag=args.tag, dry_run=args.dry_run)

    elif args.command == "install":
        install_hook()

if __name__ == "__main__":
    main()
