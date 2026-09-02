import fnmatch
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

import yaml


SENSITIVE_PATTERNS = (
    "*.sqlite",
    "*.sqlite3",
    "*.db",
    "*.sqlite-*",
    "*.sqlite3-*",
    "*.db-*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_rsa.*",
    "id_ed25519",
    "id_ed25519.*",
    ".env",
    ".env.*",
)
ACTION_COMMIT = re.compile(r"[\w.-]+/[\w./-]+@[0-9a-fA-F]{40}")


def find_sensitive_files(paths):
    return [
        path
        for path in paths
        if PurePosixPath(path).name.lower() != ".env.example"
        and any(
            fnmatch.fnmatchcase(PurePosixPath(path).name.lower(), pattern)
            for pattern in SENSITIVE_PATTERNS
        )
    ]


def find_unpinned_actions(value):
    references = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "uses":
                if not isinstance(item, str) or not (
                    item.startswith("./") or ACTION_COMMIT.fullmatch(item)
                ):
                    references.append(str(item))
            else:
                references.extend(find_unpinned_actions(item))
    elif isinstance(value, list):
        for item in value:
            references.extend(find_unpinned_actions(item))
    return references


def main():
    root = Path(__file__).resolve().parents[1]
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            capture_output=True,
            encoding="utf-8",
        )
    except (OSError, subprocess.CalledProcessError):
        print("Unable to inspect Git tracked files.", file=sys.stderr)
        return 1

    errors = [
        f"Sensitive file tracked by Git: {path}"
        for path in find_sensitive_files(result.stdout.split("\0"))
    ]
    for path in sorted((root / ".github/workflows").iterdir()):
        if path.suffix not in (".yml", ".yaml"):
            continue
        try:
            workflow = yaml.load(
                path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
            )
        except (OSError, UnicodeError, yaml.YAMLError):
            errors.append(f"Invalid workflow YAML: {path.name}")
            continue
        for reference in find_unpinned_actions(workflow):
            errors.append(f"Unpinned Action in {path.name}: {reference}")

    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Repository safety checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
