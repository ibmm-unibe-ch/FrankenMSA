import os
from pathlib import Path
from urllib.parse import quote
import tempfile

ON_COLAB = os.environ.get("ON_COLAB", False) == "1"

if not ON_COLAB and (Path(__file__).parents[2] / ".git").exists():
    import git

    try:
        repo_root = Path(__file__).parents[2]
        repo = git.Repo(repo_root)
        try:
            CURRENT_BRANCH = repo.active_branch.name
        except TypeError:
            # Detached HEAD -> fall back to short commit SHA
            CURRENT_BRANCH = repo.git.rev_parse("--short", "HEAD")
        del repo
    except Exception:
        CURRENT_BRANCH = "main"
else:
    CURRENT_BRANCH = "main"
SAFE_BRANCH = quote(CURRENT_BRANCH, safe="")
COLAB_LINK = f"https://colab.research.google.com/github/ibmm-unibe-ch/FrankenMSA/blob/{SAFE_BRANCH}/FrankenMSA_app_colab.ipynb"


# Robust, cross-environment upload directory selection
def _pick_upload_dir():
    # 1) Colab: prefer /content
    if os.path.isdir("/content"):
        base = Path("/content/ProteinMPNN/uploads")
    else:
        # 2) Allow override via env var
        env = os.environ.get("FRANKENMSA_UPLOAD_DIR")
        if env:
            base = Path(env)
        else:
            # 3) Default to user's home (~/.frankenmsa/uploads)
            base = Path.home() / ".frankenmsa" / "uploads"
    try:
        base.mkdir(parents=True, exist_ok=True)
    except Exception:
        # Fallback to system temp if anything goes wrong
        base = Path(tempfile.gettempdir()) / "frankenmsa_uploads"
        base.mkdir(parents=True, exist_ok=True)
    return str(base)


UPLOAD_DIR = _pick_upload_dir()
print(f"[UPLOAD_DIR] using: {UPLOAD_DIR}")