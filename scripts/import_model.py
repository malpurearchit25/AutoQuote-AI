"""Copy the project's existing checkpoint from its original archive."""
import argparse
from pathlib import Path
import shutil
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("archive", type=Path, help="Path to your original Complete ASEP.zip")
args = parser.parse_args()
target = Path(__file__).resolve().parents[1] / "models" / "damage.pt"
target.parent.mkdir(parents=True, exist_ok=True)
if target.exists():
    parser.error(f"{target} already exists; move it aside before importing another checkpoint.")
with zipfile.ZipFile(args.archive) as archive:
    info = archive.getinfo("Complete ASEP/asep/last.pt")
    if info.file_size > 100 * 1024 * 1024:
        parser.error("Unexpected checkpoint size (over 100 MB).")
    with archive.open(info) as source, target.open("xb") as destination:
        shutil.copyfileobj(source, destination)
print(f"Imported checkpoint to {target}")
