#!/usr/bin/env python3

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, NoReturn, Optional


@dataclass(frozen=True)
class Package:
    name: str
    path: Path

    def run_command(self, command: str, env: Optional[dict[str, str]] = None) -> int:
        """
        Execute a shell command in the package's directory.
        Returns the exit code.
        """
        print(f"⏳ Running: {command} (in {self.path})")
        result = subprocess.run(
            command,
            shell=True,
            cwd=self.path,
            capture_output=True,
            text=True,
            env=env,
        )
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
        return result.returncode


def die(message: str) -> NoReturn:
    """
    Print an error message and exit.
    """
    print(message, file=sys.stderr)
    sys.exit(1)


def get_repo_root() -> Path:
    """
    Determine the repository root using Git.
    Exits with an error if the repo root cannot be determined.
    """
    try:
        output = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            universal_newlines=True,
        )
        return Path(output.strip())
    except subprocess.CalledProcessError as err:
        print("Error: Unable to determine repository root.", file=sys.stderr)
        print(err, file=sys.stderr)
        sys.exit(1)


def discover_packages() -> List[Package]:
    """
    Automatically discover all workspace packages under the 'packages/' directory.
    Each immediate subdirectory is treated as a package.
    """
    repo_root = get_repo_root()
    packages_dir = repo_root / "packages"

    if not packages_dir.exists() or not packages_dir.is_dir():
        die(f"Error: The 'packages' directory does not exist at {packages_dir}")

    pkgs: List[Package] = []
    for item in packages_dir.iterdir():
        if item.is_dir():
            pkgs.append(Package(name=item.name, path=item.resolve()))
    return pkgs


def for_each_package(action: Callable[[Package], None]) -> None:
    """
    Iterate over each discovered package and run the given action.
    """
    for pkg in discover_packages():
        print(f"\n📦 Processing package: {pkg.name}")
        action(pkg)
