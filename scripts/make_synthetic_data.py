"""Module 1's data generator - writes today's synthetic NanoAOD-like dataset
(one dataset, "ttbar_like": 10 files, 200k-300k events each, ~2.5M events,
~500 MB) under data/synthetic/, plus its manifest at
data/datasets_synthetic.json.

A thin wrapper around vine-cms-analysis-stack's own
examples/write_test_data.py (already in your clone): this file only pins
the arguments, including a fixed --seed, so every student generates
byte-for-byte the same events and gets the same histogram counts as the
tutorial pages show.

The manifest's file paths are absolute on purpose: from Module 3 on,
processor calls run inside a TaskVine worker's own sandbox directory, not
in this directory, so a relative path like data/synthetic/... would not
resolve there.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEED = 42


def main():
    write_test_data = os.path.join(REPO_ROOT, "examples", "write_test_data.py")
    data_dir = os.path.join(REPO_ROOT, "data", "synthetic")
    manifest_path = os.path.join(REPO_ROOT, "data", "datasets_synthetic.json")

    # Fresh data every time, so rerunning this never mixes old and new files.
    shutil.rmtree(data_dir, ignore_errors=True)

    subprocess.run(
        [
            sys.executable,
            write_test_data,
            "--data-dir", data_dir,
            "--dataset-names", "ttbar_like",
            "--num-files", "10",
            "--min-events", "200000",
            "--max-events", "300000",
            "--jet-mean", "6.0",
            "--seed", str(SEED),
        ],
        check=True,
    )

    # write_test_data.py writes its manifest next to the data; move it to
    # where every later script looks for it.
    os.replace(os.path.join(data_dir, "datasets.json"), manifest_path)
    print(f"wrote {manifest_path}")


if __name__ == "__main__":
    main()
