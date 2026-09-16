"""Module 2's script - the ADL benchmark Q6 trijet analysis
(https://github.com/CoffeaTeam/coffea-benchmarks/blob/master/coffea-adl-benchmarks.py:
for events with at least three jets, plot the pT of the trijet four-momentum
whose invariant mass is closest to 172.5 GeV, the top quark mass, and the
maximum b-tag discriminant among that trijet's three jets) run through
vine_reduce's LocalDistributor: a plain ProcessPoolExecutor-backed
distributor that needs no cluster, no vine_factory/vine_worker, and no
environment packaging, since worker subprocesses already share this
process's filesystem and Python env. Module 3 runs the exact same
trijet_processor through a real TaskVine factory/worker instead - only the
`distributor=` argument changes.

Adapted from vine-cms-analysis-stack/examples/trijet/vr_trijet_iterative.py:
that version also generates its own synthetic data via write_test_data.py;
this one just points at data/datasets_synthetic.json, fetched straight into
this directory in Module 1 (no second clone - script and data both live
next to the vine-cms-analysis-stack environment they run against).
"""

from __future__ import annotations

import glob
import os
import shutil

import awkward as ak
import hist
import numpy as np

from vine_reduce import serialization
from vine_reduce.coffea import VineReduceCoffea
from vine_reduce.local_distributor import LocalDistributor

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def trijet_processor(events):
    """Runs in a local worker subprocess, once per chunk of NanoEvents - one
    `events` NanoEvents array in, any picklable object out (here, a dict of
    two Hists). VineReduceCoffea's default reducer already knows how to sum
    plain Hists and dicts of them across chunks, so no custom reducer is
    needed here (contrast with Module 7's result_postprocess)."""
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
    """Final results land under results_dir/<dataset_name>/<processor_name>/
    as a single compressed, pickled file (name includes a random uuid, hence
    the glob). serialization.load reverses what the reducer wrote."""
    pattern = os.path.join(results_dir, dataset_name, processor_name, "*.pkl.zst")
    (result_file,) = glob.glob(pattern)
    return serialization.load(result_file)


def main():
    datasets_path = os.path.join(REPO_ROOT, "data", "datasets_synthetic.json")
    results_dir = os.path.join(REPO_ROOT, "results")
    checkpoint_dir = os.path.join(REPO_ROOT, "checkpoints")

    # Fresh run every time, so stale results/checkpoints don't linger.
    shutil.rmtree(results_dir, ignore_errors=True)
    shutil.rmtree(checkpoint_dir, ignore_errors=True)

    # The dataset: a name ("ttbar_like") plus its file list, already coffea's
    # own preprocessed shape - VineReduceCoffea accepts a path to a json file
    # holding it directly, no need to load it into a dict first.
    distributor = LocalDistributor(max_workers=2)

    vr = VineReduceCoffea(
        # one Pipeline per (processor, dataset) pair - just one of each here
        processors={"trijet": trijet_processor},
        input=datasets_path,
        # where processor/reducer calls actually run
        distributor=distributor,
        results_dir=results_dir,
        checkpoint_dir=checkpoint_dir,
        # events per processor call - ~100 chunks over today's ~2.5M events
        chunksize=25_000,
    )

    with distributor:
        vr.compute()

    result = load_result(results_dir, "ttbar_like", "trijet")
    # flow=True: our uncorrelated, random-direction synthetic jets often give
    # the trijet system a pT above the [0, 200) GeV plotted above, so plain
    # .sum() (which excludes the overflow bin) would undercount how many
    # events actually got a trijet - flow=True counts every fill, in-range
    # or not.
    trijetpt_entries = result["trijetpt"].sum(flow=True)
    maxbtag_entries = result["maxbtag"].sum(flow=True)
    print(f"trijet pT histogram: {trijetpt_entries:.0f} entries")
    print(f"max b-tag histogram: {maxbtag_entries:.0f} entries")


if __name__ == "__main__":
    main()
