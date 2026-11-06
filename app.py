"""Full saved-progress beta on Vercel. Local databases are never deployed."""
import sys
import os
os.environ.setdefault("TUTOR_VAR_DIR", "/tmp/socrates-runtime")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from socrates_beta.vercel_app import vercel_app
app = vercel_app()
