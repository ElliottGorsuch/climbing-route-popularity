"""Package verified analytical assets for team review; never imply submission readiness."""

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
VERSION = "v0.3.0"


def write_zip(path, files):
    with ZipFile(path, "w", ZIP_DEFLATED, compresslevel=6) as archive:
        for source, target in files:
            if not source.is_file():
                raise FileNotFoundError(source)
            archive.write(source, target)
    with ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError(f"Invalid ZIP: {path}")
    print(f"{path.name}: {path.stat().st_size:,} bytes")


def main():
    DIST.mkdir(exist_ok=True)
    report = ROOT / "output/pdf/John Elliott Gorsuch and Victor Lee.pdf"
    base = [
        ROOT / n
        for n in [
            "README.md",
            "LICENSE",
            "requirements.txt",
            "requirements-lock.txt",
            "requirements-report.txt",
        ]
    ]
    shared = (
        base
        + sorted((ROOT / "docs").glob("*.md"))
        + sorted((ROOT / "reports").glob("main*"))
    )
    shared += [ROOT / "reports/source_manifest.json", ROOT / "reports/validation.md"]
    review = (
        shared
        + sorted((ROOT / "scripts").glob("*.py"))
        + sorted((ROOT / "tests").glob("*.py"))
    )
    review += sorted((ROOT / "reports/eda").glob("*"))
    review += [ROOT / "notebooks/02_popularity_eda.ipynb"]
    review += [
        ROOT / "data/processed/climbing_routes_main.parquet",
        ROOT / "data/processed/climbing_routes_eda.parquet",
        ROOT / "data/processed/pca_route_scores.parquet",
    ]
    review += sorted((ROOT / "data/processed").glob("regression_*_diagnostics.parquet"))
    write_zip(
        DIST / f"climbing_eda_review_{VERSION}.zip",
        [(report, report.name)] + [(p, p.relative_to(ROOT).as_posix()) for p in review],
    )
    site = sorted(p for p in (ROOT / "web").rglob("*") if p.is_file())
    site += [
        ROOT / "docs/base44_handoff.md",
        ROOT / "docs/sources.md",
        ROOT / "LICENSE",
    ]
    write_zip(
        DIST / f"climbing_atlas_{VERSION}.zip",
        [(p, p.relative_to(ROOT).as_posix()) for p in site],
    )
    dataset = shared + [ROOT / "data/processed/climbing_routes_main.csv"]
    write_zip(
        DIST / f"climbing_routes_main_csv_{VERSION}.zip",
        [(p, p.relative_to(ROOT).as_posix()) for p in dataset],
    )
    assets = [
        DIST / f"climbing_eda_review_{VERSION}.zip",
        DIST / f"climbing_atlas_{VERSION}.zip",
        DIST / f"climbing_routes_main_csv_{VERSION}.zip",
        ROOT / "data/processed/climbing_routes_main.parquet",
    ]
    (DIST / f"SHA256SUMS-{VERSION}.txt").write_text(
        "".join(
            f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in assets
        )
    )


if __name__ == "__main__":
    main()
