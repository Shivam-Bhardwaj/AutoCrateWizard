import re
import datetime

def bump_readme(version):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    if not re.search(r"version `v?(\d+\.\d+\.\d+)`", content):
        print("❌ Version string not found in README.")
        return

    updated = re.sub(r"version `v?(\d+\.\d+\.\d+)`",
                     f"version `v{version}`", content)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"✅ README updated to v{version}")

def bump_changelog(version, summary):
    date_str = datetime.date.today().isoformat()
    entry = f"## [{version}] - {date_str}\n### Updated\n- {summary}\n\n"

    with open("CHANGELOG.md", "r", encoding="utf-8") as file:
        content = file.read()

    with open("CHANGELOG.md", "w", encoding="utf-8") as file:
        file.write(entry + content)

    print(f"✅ CHANGELOG prepended with v{version} entry")

def main():
    print("📦 AutoCrate Version + Changelog Bumper")
    version = input("Enter new version (e.g., 0.1.1): ").strip()
    summary = input("Short summary of updates: ").strip()

    if not version or not summary:
        print("❌ Both version and summary are required.")
        return

    bump_readme(version)
    bump_changelog(version, summary)

if __name__ == "__main__":
    main()
