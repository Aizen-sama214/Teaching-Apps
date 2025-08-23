import sys
from pathlib import Path

# Ensure repository root is on sys.path so tests can `import LLD.*` regardless
# of whether the project has been installed into the current environment.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
