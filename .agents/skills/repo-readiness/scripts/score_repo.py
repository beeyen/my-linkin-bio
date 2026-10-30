#!/usr/bin/env python3
"""Deterministically score repository signals that support AI-assisted work."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "vendor",
}

BAND_MEANINGS = {
    "Ready": "The repository has the core context and development signals an AI agent needs to work with relatively little setup friction.",
    "Mostly ready": "The repository is workable, but one or more important context, validation, or workflow signals are missing.",
    "Needs work": "An AI agent can inspect the repository, but missing context or validation artifacts will make development unreliable.",
    "Not ready": "The repository lacks several foundational signals required for dependable AI-assisted development.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Repository root to score.")
    parser.add_argument("--pretty", action="store_true", help="Indent the JSON output.")
    return parser.parse_args()


def file_exists(root: Path, *relative_paths: str) -> bool:
    return any((root / path).is_file() for path in relative_paths)


def directory_exists(root: Path, *relative_paths: str) -> bool:
    return any((root / path).is_dir() for path in relative_paths)


def contains_source_files(root: Path) -> bool:
    source_suffixes = {".c", ".cpp", ".cs", ".go", ".java", ".js", ".jsx", ".php", ".py", ".rb", ".rs", ".swift", ".ts", ".tsx"}
    for current_root, directories, files in os.walk(root):
        directories[:] = sorted(directory for directory in directories if directory not in EXCLUDED_DIRECTORIES and not directory.startswith("."))
        for filename in sorted(files):
            if Path(filename).suffix.lower() in source_suffixes:
                return True
    return False


def has_test_files(root: Path) -> bool:
    test_directories = {"test", "tests", "spec", "specs"}
    for current_root, directories, files in os.walk(root):
        directories[:] = sorted(directory for directory in directories if directory not in EXCLUDED_DIRECTORIES and not directory.startswith("."))
        current_path = Path(current_root)
        if current_path.name.lower() in test_directories:
            return True
        if any(filename.startswith("test_") or filename.endswith("_test.py") or filename.endswith(".spec.js") for filename in sorted(files)):
            return True
    return False


def check(readiness_id: str, name: str, weight: int, passed: bool, evidence: str, improvement: str) -> dict:
    return {
        "id": readiness_id,
        "name": name,
        "weight": weight,
        "passed": passed,
        "evidence": evidence,
        "improvement": improvement,
    }


def evaluate(root: Path) -> list[dict]:
    return [
        check(
            "readme",
            "Project overview documentation",
            12,
            file_exists(root, "README", "README.md", "README.rst", "README.txt"),
            "A README file is present." if file_exists(root, "README", "README.md", "README.rst", "README.txt") else "No README file found.",
            "Add a README with purpose, setup, common commands, and a short architecture or file map.",
        ),
        check(
            "agent-guidance",
            "Agent and contributor guidance",
            12,
            file_exists(root, "AGENTS.md", "CONTRIBUTING.md", ".github/CONTRIBUTING.md", "CLAUDE.md"),
            "Repository guidance is present." if file_exists(root, "AGENTS.md", "CONTRIBUTING.md", ".github/CONTRIBUTING.md", "CLAUDE.md") else "No AGENTS.md, CONTRIBUTING.md, or equivalent guidance file found.",
            "Add AGENTS.md or CONTRIBUTING.md with conventions, validation commands, boundaries, and project-specific context.",
        ),
        check(
            "dependency-manifest",
            "Dependency and tool manifest",
            10,
            file_exists(root, "requirements.txt", "pyproject.toml", "package.json", "go.mod", "Cargo.toml", "pom.xml", "Gemfile", "composer.json"),
            "A dependency manifest is present." if file_exists(root, "requirements.txt", "pyproject.toml", "package.json", "go.mod", "Cargo.toml", "pom.xml", "Gemfile", "composer.json") else "No recognized dependency manifest found.",
            "Add the dependency manifest and keep runtime, development, and tool versions reproducible.",
        ),
        check(
            "entrypoint",
            "Recognizable application entrypoint",
            10,
            file_exists(root, "app.py", "main.py", "manage.py", "package.json", "src/main.py", "src/index.ts", "src/index.js", "cmd/main.go") or file_exists(root, "Dockerfile", "docker-compose.yml", "compose.yml"),
            "A conventional entrypoint or container definition is present." if (file_exists(root, "app.py", "main.py", "manage.py", "package.json", "src/main.py", "src/index.ts", "src/index.js", "cmd/main.go") or file_exists(root, "Dockerfile", "docker-compose.yml", "compose.yml")) else "No conventional entrypoint or container definition found.",
            "Document or add the command that starts the application or its primary workflow.",
        ),
        check(
            "tests",
            "Automated test coverage entrypoint",
            15,
            has_test_files(root),
            "A test directory or recognizable test file is present." if has_test_files(root) else "No test directory or recognizable test file found.",
            "Add a small automated test suite covering the critical user flows and document how to run it.",
        ),
        check(
            "ci",
            "Continuous integration or verification workflow",
            10,
            directory_exists(root, ".github/workflows", ".circleci") or file_exists(root, ".gitlab-ci.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml", ".travis.yml"),
            "A CI configuration is present." if (directory_exists(root, ".github/workflows", ".circleci") or file_exists(root, ".gitlab-ci.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml", ".travis.yml")) else "No recognized CI configuration found.",
            "Add a CI workflow that installs dependencies and runs the project's tests or validation commands.",
        ),
        check(
            "environment-example",
            "Documented environment configuration",
            8,
            file_exists(root, ".env.example", ".env.sample", "config.example.json", "config.example.yaml", "config.example.yml"),
            "An environment or configuration example is present." if file_exists(root, ".env.example", ".env.sample", "config.example.json", "config.example.yaml", "config.example.yml") else "No environment or configuration example found.",
            "Add a sanitized example configuration and explain required environment variables without committing secrets.",
        ),
        check(
            "gitignore",
            "Generated-file and secret protection",
            8,
            file_exists(root, ".gitignore", ".git/info/exclude"),
            "A gitignore or repository exclude file is present." if file_exists(root, ".gitignore", ".git/info/exclude") else "No .gitignore or repository exclude file found.",
            "Add .gitignore entries for dependencies, caches, build output, local settings, and secrets.",
        ),
        check(
            "license",
            "License or reuse terms",
            5,
            file_exists(root, "LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING"),
            "A license file is present." if file_exists(root, "LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING") else "No license or reuse terms file found.",
            "Add a license or clearly document the repository's reuse terms.",
        ),
        check(
            "quality-config",
            "Formatting, linting, or static-analysis configuration",
            5,
            file_exists(root, "pyproject.toml", "setup.cfg", "tox.ini", ".pre-commit-config.yaml", ".eslintrc", ".eslintrc.json", ".eslintrc.js", "biome.json", "rustfmt.toml") or directory_exists(root, ".github/linters"),
            "A recognized quality-tool configuration is present." if (file_exists(root, "pyproject.toml", "setup.cfg", "tox.ini", ".pre-commit-config.yaml", ".eslintrc", ".eslintrc.json", ".eslintrc.js", "biome.json", "rustfmt.toml") or directory_exists(root, ".github/linters")) else "No recognized formatter, linter, or static-analysis configuration found.",
            "Configure the formatter or linter used by the project and document its command.",
        ),
        check(
            "source-layout",
            "Recognizable source layout",
            5,
            contains_source_files(root),
            "Recognizable source files are present." if contains_source_files(root) else "No recognizable source files found.",
            "Organize application source in a discoverable layout and describe the important directories.",
        ),
    ]


def readiness_band(score: int) -> str:
    if score >= 90:
        return "Ready"
    if score >= 75:
        return "Mostly ready"
    if score >= 50:
        return "Needs work"
    return "Not ready"


def main() -> None:
    args = parse_args()
    root = args.repo.expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Repository path is not a directory: {root}")

    checks = evaluate(root)
    score = sum(item["weight"] for item in checks if item["passed"])
    band = readiness_band(score)
    failed_checks = [item for item in checks if not item["passed"]]
    result = {
        "repo": str(root),
        "score": score,
        "max_score": sum(item["weight"] for item in checks),
        "band": band,
        "band_meaning": BAND_MEANINGS[band],
        "checks": checks,
        "recommendations": failed_checks,
    }
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=False))


if __name__ == "__main__":
    main()
