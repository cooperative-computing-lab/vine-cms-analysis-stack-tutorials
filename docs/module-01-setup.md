# Module 1 - Setup & verify

**15 min**

!!! warning "Do these before the session"
    Creating the environment and packing it for remote workers each take a
    few minutes. Thus, do every step on this page *before* the session; in
    the room, only the checks are run.

## Clone

Given that you're reading this on the web, there is nothing to clone *for
the tutorial itself*. The one thing you do need is the software stack,
`vine-cms-analysis-stack`, which carries the `environment.yml`/
`pyproject.toml` that build today's environment:

```bash
cd ~
git clone https://github.com/cooperative-computing-lab/vine-cms-analysis-stack.git
cd ~/vine-cms-analysis-stack
```

Stay in `~/vine-cms-analysis-stack/` for the rest of today.

## Create the environment

Pick **one** of the two options. Both give you the same packages
(`ndcctools` for TaskVine, `vine-reduce`, `coffea`, `awkward`, `uproot`,
`xrootd`, `matplotlib`); the differences between them are in the
[Appendix](appendix.md#conda-vs-pixi-differences), and you don't need them
today.

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
    scripts/vr_trijet_iterative.py`) rather than activating an environment;
    every command in this tutorial shows both options side by side.

## Verify

=== "Option A: conda"

    ```bash
    python -c "import ndcctools.taskvine, vine_reduce, coffea; print('ok')"
    ```

=== "Option B: pixi"

    ```bash
    pixi run python -c "import ndcctools.taskvine, vine_reduce, coffea; print('ok')"
    ```

You should see:

```
ok
```

If this fails, fix it now, since every later module depends on this
import. A common issue is that the wrong environment is active
(`conda env list` to check).

## Pack the environment for remote workers

From [Module 4](module-04-scale-out.md) on, your code runs on HTCondor
pool nodes that don't have any of this installed. Therefore, VineReduce
ships a packed copy of your environment along with every task, and
`get_environment()` builds that tarball. Build it now: it takes a few
minutes (2 min 17 s when this page was tested) and ~750 MB, and later
calls reuse the cached copy instantly:

=== "Option A: conda"

    ```bash
    python -c "from vine_reduce import get_environment; print(get_environment())"
    ```

=== "Option B: pixi"

    ```bash
    pixi run python -c "from vine_reduce import get_environment; print(get_environment())"
    ```

It prints the path of the tarball it built. Module 4 explains what's in it.

## Get today's data

There are two datasets today, both in the shape coffea's own preprocessing
produces (`{dataset_name: {"metadata": {...}, "files": {path: {"object_path":
"Events", "num_entries": N}}}}`). Thus, switching a script between them is
a one-line change, rather than a processor-code change.

Fetch the real-data manifest and the synthetic-data generator:

```bash
TUT=https://raw.githubusercontent.com/cooperative-computing-lab/vine-cms-analysis-stack-tutorials/main
mkdir -p data scripts
curl -sL -o data/datasets_small_real.json     "$TUT/data/datasets_small_real.json"
curl -sL -o scripts/make_synthetic_data.py    "$TUT/scripts/make_synthetic_data.py"
```

Generate the synthetic data (about 20 seconds):

=== "Option A: conda"

    ```bash
    python scripts/make_synthetic_data.py
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/make_synthetic_data.py
    ```

```
wrote /users/<you>/vine-cms-analysis-stack/data/datasets_synthetic.json
```

### `datasets_synthetic.json`

This is one dataset, `ttbar_like`, with 10 ROOT files under
`data/synthetic/`, 2,523,470 events, and ~490 MB. `make_synthetic_data.py`
calls this repo's own `examples/write_test_data.py` with a fixed random
seed, so everyone gets exactly the same events, and thus the same histogram
counts as these pages show.

```bash
head -12 data/datasets_synthetic.json
```

```json
{
  "ttbar_like": {
    "metadata": {
      "dataset": "ttbar_like"
    },
    "files": {
      "/users/<you>/vine-cms-analysis-stack/data/synthetic/ttbar_like/file_0.root": {
        "object_path": "Events",
        "num_entries": 208925
      },
      "/users/<you>/vine-cms-analysis-stack/data/synthetic/ttbar_like/file_1.root": {
        "object_path": "Events",
```

The paths are absolute on purpose: from Module 3 on, tasks run inside a
TaskVine worker's own sandbox directory, where a relative path wouldn't
resolve. Modules [2](module-02-local-distributor.md),
[3](module-03-local-factory.md), [6](module-06-checkpoints-restart.md), and
[9](module-09-failure-proportion.md) run over this dataset.

### `datasets_small_real.json`

This is real CMS Open Data: one NanoAOD file read over `xrootd` from
CERN's public EOS, with no grid proxy needed:

```bash
cat data/datasets_small_real.json
```

```json
{
  "SingleMu": {
    "metadata": {
      "dataset": "SingleMu",
      "source": "Run2012B_SingleMu, CMS Open Data (IRIS-HEP ADL benchmark input), eospublic.cern.ch"
    },
    "files": {
      "root://eospublic.cern.ch//eos/root-eos/benchmark/Run2012B_SingleMu.root": {
        "object_path": "Events",
        "num_entries": 500000
      }
    }
  }
}
```

`num_entries` is capped at 500,000 of the file's ~53.4M events, so that a
live run finishes in minutes. This is the exact file the ADL benchmarks,
where `trijet_processor` comes from, were written against. Modules
[4](module-04-scale-out.md), [5](module-05-resources.md),
[7](module-07-result-postprocess.md), and
[8](module-08-multiple-processors.md) run over it, on the HTCondor pool.

### `datasets_real.json` - not used today

The same `Run2012B_SingleMu` open-data file as `datasets_small_real.json`
above, but split into 205 local files across 5 datasets - built once,
ahead of time, by `scripts/make_real_scale_data.py`, not fetched or
generated live today. See [Module 10](module-10-wrapup.md)'s closing
discussion.
