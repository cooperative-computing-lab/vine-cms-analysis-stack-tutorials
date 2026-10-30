# Module 1 - Setup & verify

**15 min**

!!! warning "Do these before the session"
    Creating the environment and packing it for remote workers each take
    up to 15 minutes on glados, where your home directory is on a network
    file system. Thus, do every step on this page *before* the session; in
    the room, only the checks are run.

## Pick your analysis implementation

Today's analysis is written two ways. They compute the
same thing, and everything around the analysis (the distributors, TaskVine,
the factory, checkpoints, `failure_proportion`) is identical:

- **coffea**: awkward arrays through coffea's `NanoEvents`, run by
  `VineReduceCoffea`.
- **RDataFrame**: ROOT's `RDataFrame`, with the per-event logic written as
  a short piece of C++ that ROOT compiles on the fly, run by plain
  `VineReduce`.

Wherever the two differ, a page shows a pair of tabs labelled `coffea` and
`RDataFrame`. Pick the same one on every page, and the site will switch the
rest of the tabs for you. Both are installed by the environment below, so
you can change your mind later by clicking the other tab.

## Clone

Clone the analysis stack `vine-cms-analysis-stack` to build today's environment:

```bash
cd ~
git clone https://github.com/cooperative-computing-lab/vine-cms-analysis-stack.git
cd ~/vine-cms-analysis-stack
```

The tutorial's scripts and data manifests are already in the clone, under
`examples/tutorial_nd/`, so there is nothing else to download.

## Create the environment

Pick **one** of the two options. Both give you the same packages
(`ndcctools` for TaskVine, `vine-reduce`, `coffea`, `awkward`, `uproot`,
`xrootd`, `matplotlib`, and `root` for RDataFrame); the differences
between them are in the
[Appendix](appendix.md#conda-vs-pixi-differences), and you don't need them
today.

Conda is the more tested path, but more and more applications are moving to use pixi.
Environments made by pixi are essentially the same as the ones done with conda.

=== "Option A: conda"

    ```bash
    conda env create -f environment.yml
    conda activate vine-cms-analysis-stack
    ```

=== "Option B: pixi"

    ```bash
    pixi install
    ```

    Run everything through `pixi run` (e.g. `pixi run python
    scripts/vr_trijet_iterative.py`).

## Go to the tutorial directory

Once the environment exists, move into the tutorial directory and stay there
for the rest of today:

```bash
cd ~/vine-cms-analysis-stack/examples/tutorial_nd
ls
```

```
data  README.md  scripts
```

`scripts/` has one script per module, and `data/` has the dataset manifests
described [below](#data-descriptions). Everything else you create today
(`results/`, `checkpoints/`, `vine-run-info/`, `factory.json`, `plots/`)
appears next to them. These are ignored by git.

## Verify

=== "Option A: conda"

    ```bash
    python -c "import ndcctools.taskvine, vine_reduce, coffea, ROOT; print('ok')"
    ```

=== "Option B: pixi"

    ```bash
    pixi run python -c "import ndcctools.taskvine, vine_reduce, coffea, ROOT; print('ok')"
    ```

You should see:

```
ok
```

Both flavors are checked, whichever one you picked. If this fails, fix it
now, since every later module depends on this import. A common issue is
that the wrong environment is active.

## Pack the environment for remote workers

From [Module 4](module-04-scale-out.md) on, your code runs on HTCondor
pool nodes that don't have any of this installed. Therefore, VineReduce
ships a packed copy of your environment along with every task, and
`get_environment()` builds that tarball. Build it now: it takes 5 to 15
minutes and comes to ~1.5 GB, and later calls reuse the cached copy
in a few seconds:

=== "Option A: conda"

    ```bash
    python -c "from vine_reduce import get_environment; print(get_environment())"
    ```

=== "Option B: pixi"

    ```bash
    pixi run python -c "from vine_reduce import get_environment; print(get_environment())"
    ```

It prints the path of the tarball it built. Module 4 explains what's in it.

## Data descriptions

Today's data is real CMS Open Data taken from the `Run2012B_SingleMu`.

You need to be logged in `glados` or any `crc` frontend to see the data.

- `data/datasets_vast.json` points at `/project01/ndcms/btovar/tutorial/tutorial/SingleMu_Run2012B/...`,
  on the VAST filesystem that your login node mounts. Modules
  [2](module-02-local-distributor.md), [3](module-03-local-factory.md),
  [6](module-06-checkpoints-restart.md), and
  [9](module-09-failure-proportion.md) run on the login node and read these.
- `data/datasets_xrootd.json` points at
  `root://cmsxrootd.crc.nd.edu//store/user/btovar/tutorial/SingleMu_Run2012B/...`,
  the same files over xrootd, with no grid proxy needed. Modules
  [4](module-04-scale-out.md), [5](module-05-resources.md),
  [7](module-07-result-postprocess.md), and
  [8](module-08-multiple-processors.md) run on HTCondor pool nodes, and read
  these.

Look at the first dataset:

```bash
head -22 data/datasets_vast.json
```

```json
{
  "SingleMu_Run2012B_193834-194270": {
    "metadata": {
      "dataset": "SingleMu_Run2012B_193834-194270",
      "source": "Run2012B_SingleMu, CMS Open Data (IRIS-HEP ADL benchmark input), eospublic.cern.ch; first 3 files of this dataset's split; dataset name is an illustrative run-range label, not derived from these files' actual run numbers"
    },
    "files": {
      "/project01/ndcms/btovar/tutorial/tutorial/SingleMu_Run2012B/SingleMu_Run2012B_193834-194270/file_0.root": {
        "object_path": "Events",
        "num_entries": 53733
      },
      "/project01/ndcms/btovar/tutorial/tutorial/SingleMu_Run2012B/SingleMu_Run2012B_193834-194270/file_1.root": {
        "object_path": "Events",
        "num_entries": 222177
      },
      "/project01/ndcms/btovar/tutorial/tutorial/SingleMu_Run2012B/SingleMu_Run2012B_193834-194270/file_2.root": {
        "object_path": "Events",
        "num_entries": 395172
      }
    }
  },
```

The paths are absolute on purpose: from Module 3 on, tasks run inside a
TaskVine worker's own sandbox directory, where a relative path wouldn't
resolve.
