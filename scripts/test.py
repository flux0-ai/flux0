from utils import Package, die, for_each_package


def test_package(pkg: Package) -> None:
    """
    Run pytest on the package.
    """
    command = "uv run -m pytest ."
    error_message = f"Pytest failed in package '{pkg.name}'"

    exit_code = pkg.run_command(command)
    if exit_code == 5:
        print(f"⚠️ Warning: No tests found in package '{pkg.name}'. Skipping...")
        return  # Don't treat this as an error

    if exit_code != 0:
        die(f"Error: {error_message}. Fix issues and try again.")


def main() -> None:
    """
    Discover all workspace packages and run tests on each.
    """
    print("🚀 Starting tests across workspace packages...\n")
    for_each_package(test_package)
    print("\n✅ All workspace packages passed tests!")


if __name__ == "__main__":
    main()
