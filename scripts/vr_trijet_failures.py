"""Module 9's script - Module 2's scripts/vr_trijet_iterative.py over the
same data/datasets_synthetic.json, plus one file that doesn't exist, to
show failure_proportion.

The bad entry is a path on CERN's public EOS that isn't there. Every chunk
of it fails to open; once one chunk has used up its `attempts` (3), the
whole file is given up on for good and logged to failed_files.log in the
current directory. What happens next is failure_proportion's call:

    permanently failed files / files in the dataset > failure_proportion
        -> the run aborts

Here that's 1 / 11 = 0.09, so:

    python scripts/vr_trijet_failures.py 0      # aborts
    python scripts/vr_trijet_failures.py 0.1    # finishes, with a warning
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import sys

import awkward as ak
import hist
import numpy as np

from vine_reduce import serialization
from vine_reduce.coffea import VineReduceCoffea
from vine_reduce.local_distributor import LocalDistributor

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BAD_FILE = "root://eospublic.cern.ch//eos/root-eos/benchmark/DOES_NOT_EXIST.root"


def trijet_processor(events):
    """Unchanged from Module 2."""
    jets = ak.zip(
        {k: getattr(events.Jet, k) for k in ["x", "y", "z", "t", "btag"]},
        with_name="LorentzVector",
        behavior=events.Jet.behavior,
    )
    trijet = ak.combinations(jets, 3, fields=["j1", "j2", "j3"])
    trijet["p4"] = trijet.j1 + trijet.j2 + trijet.j3
    trijet = ak.flatten(
        trijet[ak.singletons(ak.argmin(abs(trijet.p4.mass - 172.5), axis=1))]
    )
    maxBtag = np.maximum(
        trijet.j1.btag,
        np.maximum(trijet.j2.btag, trijet.j3.btag),
    )
    return {
        "trijetpt": hist.Hist.new.Reg(
            100, 0, 200, name="pt3j", label="Trijet $p_{T}$ [GeV]"
        )
        .Double()
        .fill(trijet.p4.pt),
        "maxbtag": hist.Hist.new.Reg(
            100, 0, 1, name="btag", label="Max jet b-tag score"
        )
        .Double()
        .fill(maxBtag),
    }


def load_result(results_dir, dataset_name, processor_name):
    """Unchanged from Module 2."""
    pattern = os.path.join(results_dir, dataset_name, processor_name, "*.pkl.zst")
    (result_file,) = glob.glob(pattern)
    return serialization.load(result_file)


def main():
    failure_proportion = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0

    results_dir = os.path.join(REPO_ROOT, "results")
    checkpoint_dir = os.path.join(REPO_ROOT, "checkpoints")

    shutil.rmtree(results_dir, ignore_errors=True)
    shutil.rmtree(checkpoint_dir, ignore_errors=True)

    # Module 2's dataset, plus the one bad file. num_entries is made up:
    # chunks are cut from it without opening the file, so nothing notices
    # the file is missing until a processor call tries to read it.
    with open(os.path.join(REPO_ROOT, "data", "datasets_synthetic.json")) as f:
        datasets = json.load(f)
    datasets["ttbar_like"]["files"][BAD_FILE] = {
        "object_path": "Events",
        "num_entries": 100_000,
    }
    n_files = len(datasets["ttbar_like"]["files"])
    print(f"failure_proportion={failure_proportion}, {n_files} files, 1 of them missing")

    distributor = LocalDistributor(max_workers=2)

    vr = VineReduceCoffea(
        processors={"trijet": trijet_processor},
        input=datasets,
        distributor=distributor,
        results_dir=results_dir,
        checkpoint_dir=checkpoint_dir,
        chunksize=25_000,
        failure_proportion=failure_proportion,
    )

    with distributor:
        vr.compute()

    result = load_result(results_dir, "ttbar_like", "trijet")
    trijetpt_entries = result["trijetpt"].sum(flow=True)
    maxbtag_entries = result["maxbtag"].sum(flow=True)
    print(f"trijet pT histogram: {trijetpt_entries:.0f} entries")
    print(f"max b-tag histogram: {maxbtag_entries:.0f} entries")


if __name__ == "__main__":
    main()
