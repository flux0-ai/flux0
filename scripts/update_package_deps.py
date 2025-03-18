#!/usr/bin/env python
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

# Get package name from command-line argument
PACKAGE_NAME = sys.argv[1]

# Define paths dynamically
ROOT_DIR = Path(__file__).parent.parent
if PACKAGE_NAME == "root":
    PACKAGE_DIR = ROOT_DIR  # `root` package is in the repo root
    PACKAGE_PYPROJECT = ROOT_DIR / "pyproject.toml"
else:
    PACKAGE_DIR = ROOT_DIR / "packages" / PACKAGE_NAME
    PACKAGE_PYPROJECT = PACKAGE_DIR / "pyproject.toml"


def get_workspace_dependencies() -> Any:
    """Extract dependencies from `[tool.uv.sources]` in the package's `pyproject.toml`."""
    with open(PACKAGE_PYPROJECT, "rb") as f:
        pyproject = tomllib.load(f)

    sources = pyproject.get("tool", {}).get("uv", {}).get("sources", {})
    # Keep only dependencies that have `{ workspace = true }`
    return {key: value for key, value in sources.items() if value == {"workspace": True}}


def get_package_version(package_name: str) -> Any:
    """Read the package version from `packages/{package}/pyproject.toml`, or root if needed."""
    if package_name == "root":
        package_pyproject = ROOT_DIR / "pyproject.toml"
    else:
        # Strip 'flux0-' prefix if it exists to get the actual package directory name
        package_dir_name = package_name.removeprefix("flux0-")
        package_pyproject = ROOT_DIR / "packages" / package_dir_name / "pyproject.toml"

    if not package_pyproject.exists():
        raise FileNotFoundError(f"Missing pyproject.toml for {package_name}")

    with open(package_pyproject, "rb") as f:
        pyproject = tomllib.load(f)

    return pyproject["project"]["version"]


def update_dependencies() -> bool:
    """Update only the `dependencies` field in `pyproject.toml` while preserving formatting."""
    with open(PACKAGE_PYPROJECT, "r", encoding="utf-8") as f:
        pyproject_text = f.read()

    # Extract the dependencies block using regex
    dependencies_match = re.search(r"dependencies\s*=\s*\[(.*?)\]", pyproject_text, re.DOTALL)
    if not dependencies_match:
        print("No dependencies found in pyproject.toml.")
        return False

    # Parse current dependencies as a list
    dependencies_text = dependencies_match.group(1).strip()
    dependencies = [
        d.strip().strip('"').strip("'") for d in dependencies_text.split(",") if d.strip()
    ]

    # Get workspace dependencies
    workspace_deps = get_workspace_dependencies()

    updated_deps = []
    updated = False

    for dep in dependencies:
        dep_name = dep.split("==")[0]  # Extract dependency name
        if dep_name in workspace_deps:
            new_version = get_package_version(dep_name)
            current_version = dep.split("==")[1] if "==" in dep else None
            if current_version != new_version:
                print(f"Updating {dep_name} from {current_version} to {new_version}")
                updated_deps.append(f'"{dep_name}=={new_version}"')
                updated = True
            else:
                updated_deps.append(f'"{dep}"')
        else:
            updated_deps.append(f'"{dep}"')

    if updated:
        # Replace dependencies block in the original text
        new_dependencies_text = ",\n    ".join(updated_deps)
        new_pyproject_text = re.sub(
            r"dependencies\s*=\s*\[(.*?)\]",
            f"dependencies = [\n    {new_dependencies_text}\n]",
            pyproject_text,
            flags=re.DOTALL,
        )

        # Write back the updated file with preserved formatting
        with open(PACKAGE_PYPROJECT, "w", encoding="utf-8") as f:
            f.write(new_pyproject_text)

        print("Updated dependencies:", updated_deps)
        return True
    else:
        print("No dependency updates needed.")
        return False


def git_commit_and_push() -> None:
    """Commit and push changes to GitHub"""
    subprocess.run(["git", "config", "--global", "user.name", "github-actions"], check=True)
    subprocess.run(
        ["git", "config", "--global", "user.email", "actions@users.noreply.github.com"],
        check=True,
    )
    subprocess.run(["git", "add", str(PACKAGE_PYPROJECT)], check=True)
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"chore({PACKAGE_NAME}): update workspace dependencies [skip ci]",
        ],
        check=True,
    )
    subprocess.run(["git", "push"], check=True)
    print("Committed and pushed updated dependencies.")


if __name__ == "__main__":
    updated = update_dependencies()
    if updated:
        git_commit_and_push()
