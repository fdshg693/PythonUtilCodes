#!/usr/bin/env python3
"""
Prints a directory tree and summarizes each file's contents using the OpenAI API,
ignoring files and directories listed in a root-level IGNORE file.
"""
import os
import sys
import argparse
import textwrap
import fnmatch
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI

load_dotenv(find_dotenv())
client = OpenAI()

def load_ignore_patterns(root):
    """
    Load ignore patterns from an ignore.txt file in the root directory.
    Lines starting with '#' or empty lines are skipped.
    Returns a list of glob patterns.
    """
    patterns = []
    ignore_file = os.path.join(root, 'ignore.txt')
    if os.path.isfile(ignore_file):
        try:
            with open(ignore_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    patterns.append(line)
        except Exception as e:
            print(f"[IGNORE 読み取りエラー: {e}]")
    return patterns


def summarize_file(path, max_chars=5000):
    """
    Reads up to max_chars from the file at `path` and returns a brief summary.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(max_chars)
    except Exception as e:
        return f"[読み取りエラー: {e}]"

    prompt = (
        "次のファイルの内容を短く要約してください（日本語で、1〜2文程度）:\n"
        f"```\n{content}\n```"
    )
    try:
        response = client.responses.create(
            model="gpt-4.1",
            input=prompt,
        )        
        return response.output_text.strip()
    except Exception as e:
        return f"[要約エラー: {e}]"


def print_tree(path, prefix="", ignore_patterns=None):
    """
    Recursively prints a tree of `path`, appending an AI-generated summary for each file.
    Skips entries matching any ignore pattern.
    """
    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        print(f"{prefix}[アクセス権限なし: {path}]")
        return

    # filter ignored patterns
    if ignore_patterns:
        filtered = []
        for name in entries:
            if any(fnmatch.fnmatch(name, pat) for pat in ignore_patterns):
                continue
            filtered.append(name)
        entries = filtered

    for index, name in enumerate(entries):
        full = os.path.join(path, name)
        is_last = index == len(entries) - 1
        branch = "└── " if is_last else "├── "

        if os.path.isdir(full):
            print(f"{prefix}{branch}{name}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(full, new_prefix, ignore_patterns)
        else:
            summary = summarize_file(full)
            wrapped = textwrap.fill(summary, width=60)
            lines = wrapped.split("\n")
            print(f"{prefix}{branch}{name} - {lines[0]}")
            for line in lines[1:]:
                print(f"{prefix}{' ' * len(branch)}  {line}")


def main():
    parser = argparse.ArgumentParser(
        description="ディレクトリツリーを表示し、各ファイルをAIで要約します。"
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="処理対象のルートディレクトリ（デフォルト: カレントディレクトリ）"
    )
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    ignore_patterns = load_ignore_patterns(root)

    print(f"# Tree summary of: {root}")
    if ignore_patterns:
        print(f"# Ignoring patterns from {os.path.join(root, 'ignore.txt')}: {ignore_patterns}")
    print_tree(root, ignore_patterns=ignore_patterns)


if __name__ == "__main__":
    main()
