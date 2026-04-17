import os
from pathlib import Path
from urllib.parse import quote

from frankenmsa.runtime import get_upload_dir
from frankenmsa.runtime import is_colab_runtime

ON_COLAB = is_colab_runtime()

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


UPLOAD_DIR = get_upload_dir()
print(f"[UPLOAD_DIR] using: {UPLOAD_DIR}")