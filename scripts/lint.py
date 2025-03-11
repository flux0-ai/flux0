import os

from utils import Package, die, for_each_package

excluded_packages = ["client"]


def lint_package(pkg: Package) -> None:
    """
    Run linting commands (Mypy, Ruff check, Ruff format check) on the package.
    For packages that contain a 'src' directory, Mypy is run on that directory
    with MYPYPATH set accordingly.
    """
    # Determine if the package uses a "src" layout.
    src_dir = pkg.path / "src"
    if src_dir.exists() and src_dir.is_dir():
        mypy_target = str(src_dir)
        mypy_env = os.environ.copy()
        mypy_env["MYPYPATH"] = mypy_target
    else:
        mypy_target = "."
        mypy_env = None

    # Build our commands.
    commands = [
        # Run mypy using uv run with the explicit package base pointing to our target.
        (
            f"uv run mypy --explicit-package-bases {mypy_target}",
            f"Mypy check failed in package '{pkg.name}'",
            mypy_env,
        ),
        # Run Ruff lint check.
        ("uv run ruff check .", f"Ruff lint check failed in package '{pkg.name}'", None),
        # Run Ruff format check.
        ("uv run ruff format --check .", f"Ruff format check failed in package '{pkg.name}'", None),
    ]

    if pkg.name in excluded_packages:
        print(f"Skipping linting for excluded package '{pkg.name}'")
        return

    for cmd, err_msg, env in commands:
        exit_code = pkg.run_command(cmd, env=env)
        if exit_code != 0:
            die(f"Error: {err_msg}. Fix issues and try again.")


def main() -> None:
    """
    Discover all workspace packages and run lint checks on each.
    """
    print("🚀 Starting linting across workspace packages...\n")
    for_each_package(lint_package)
    print("\n✅ All workspace packages passed linting!")


if __name__ == "__main__":
    main()
