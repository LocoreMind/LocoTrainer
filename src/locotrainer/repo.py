"""Auto-clone ms-swift repo on first run."""

import subprocess
from pathlib import Path

DEFAULT_REPO_URL = "https://github.com/modelscope/ms-swift.git"
DEFAULT_REPO_DIR = Path.home() / ".locotrainer" / "repos" / "ms-swift"


def ensure_repo(repo_dir: Path | None = None) -> Path:
    """Ensure ms-swift repo exists locally. Clone if missing.

    Returns the path to the repo.
    """
    if repo_dir is None:
        repo_dir = DEFAULT_REPO_DIR

    if (repo_dir / ".git").exists():
        return repo_dir

    print(f"ms-swift repo not found at {repo_dir}")
    print(f"Cloning from {DEFAULT_REPO_URL} (shallow, this may take a moment)...")

    repo_dir.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ["git", "clone", "--depth", "1", DEFAULT_REPO_URL, str(repo_dir)],
        check=True,
    )

    print(f"Cloned to {repo_dir}\n")
    return repo_dir
