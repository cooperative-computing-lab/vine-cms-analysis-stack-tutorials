"""Module 6's script - Module 3's scripts/vr_trijet_taskvine.py, set up so
you can interrupt it and pick up where it left off.

Three things change from Module 3; the processor, the dataset, and result
loading do not:

1. checkpoint_time=10: a non-final reduction is written to disk as a
   checkpoint once the processor/reducer wall time it is about to fold in
   - summed over the group, since that lineage's last checkpoint - reaches
   10 seconds. It is not a timer that fires every 10 seconds.
2. results/ and checkpoints/ are NOT deleted at start. That's what lets a
   rerun of the identical command resume instead of starting over. Delete
   them yourself (rm -rf results checkpoints) for a genuinely fresh run.
3. One worker with one core, so the run is slow enough to Ctrl-C partway.
"""

from __future__ import annotations

import glob
import os

import awkward as ak
import hist
import ndcctools.taskvine as vine
import numpy as np

from vine_reduce import serialization
from vine_reduce.coffea import VineReduceCoffea
from vine_reduce.taskvine_distributor import TaskVineDistributor

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def trijet_processor(events):
    """Unchanged from Modules 2 and 3."""
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
    """Unchanged from Modules 2 and 3."""
    pattern = os.path.join(results_dir, dataset_name, processor_name, "*.pkl.zst")
    (result_file,) = glob.glob(pattern)
    return serialization.load(result_file)


def main():
    datasets_path = os.path.join(REPO_ROOT, "data", "datasets_synthetic.json")
    results_dir = os.path.join(REPO_ROOT, "results")
    checkpoint_dir = os.path.join(REPO_ROOT, "checkpoints")

    # no shutil.rmtree here - see the module docstring

    distributor = TaskVineDistributor(
        port=0,
        resources_processor={"cores": 1},
        resources_reducer={"cores": 1},
    )
    print(f"TaskVine manager listening on port {distributor.port}")

    vr = VineReduceCoffea(
        processors={"trijet": trijet_processor},
        input=datasets_path,
        distributor=distributor,
        results_dir=results_dir,
        checkpoint_dir=checkpoint_dir,
        chunksize=25_000,
        checkpoint_time=10,
    )

    workers = vine.Factory(manager_host_port=f"localhost:{distributor.port}")
    workers.ssl = True
    workers.cores = 1
    workers.min_workers = 1
    workers.max_workers = 1
    workers.extra_options = "--single-shot"

    with distributor, workers:
        vr.compute()

    result = load_result(results_dir, "ttbar_like", "trijet")
    trijetpt_entries = result["trijetpt"].sum(flow=True)
    maxbtag_entries = result["maxbtag"].sum(flow=True)
    print(f"trijet pT histogram: {trijetpt_entries:.0f} entries")
    print(f"max b-tag histogram: {maxbtag_entries:.0f} entries")


if __name__ == "__main__":
    main()
