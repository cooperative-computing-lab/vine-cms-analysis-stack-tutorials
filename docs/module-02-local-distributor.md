# Module 2 - Local distributor

**15 min**

## Run it

From `~/vine-cms-analysis-stack/examples/tutorial_nd` (see [Module 1](module-01-setup.md)):

=== "coffea"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_iterative.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_iterative.py
        ```

=== "RDataFrame"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_iterative_rdf.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_iterative_rdf.py
        ```

What you see first depends on the flavor:

=== "coffea"

    You will first see some warnings, such as `RuntimeWarning: Missing
    cross-reference index for ...` and a `DeprecationWarning` from inside
    `awkward`, all of which are harmless. `NanoAODSchema` expects every
    cross-reference branch that a real NanoAOD file carries (electrons pointing
    back at jets, and so on); however, this 2012 open-data file predates some of them, thus the schema
    warns about the missing ones and moves on.

=== "RDataFrame"

    There are no warnings this time, since RDataFrame only looks at the
    branches that the analysis names, and nothing about the rest of the file
    matters to it.

After that, `vine_reduce`'s own live console takes over, with one line per
finished call plus four progress bars that update in place (the colors
below are what your own terminal shows):

=== "coffea"

    About 15 seconds in, it ends like this:

    <div class="term">
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_0.root[50000:53733] (id=1cab5cac) cores=1(1) memory_mb=149 wall_time_s=1
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_0.root[0:50000] (id=dd532c85) cores=1(1) memory_mb=180 wall_time_s=1
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_1.root[0:50000] (id=b6a0617f) cores=1(1) memory_mb=292 wall_time_s=1
    ...
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_195842-196531 ...2-196531/file_2.root[50000:99449] (id=c43eb9b7) cores=1(1) memory_mb=554 wall_time_s=1
    <span class="t-green">success             </span> reducer   trijet/SingleMu_Run2012B_195842-196531 reduction of 10 partials (id=4db6c3e8) cores=1(1) memory_mb=554 wall_time_s=1
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=381003a8) cores=1(1) memory_mb=554 wall_time_s=1
    trijet     [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">83</span>/<span class="t-red">0</span>/<span class="t-blue">83</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">11</span>/<span class="t-red">0</span>/<span class="t-blue">11</span>
    events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>
    SingleMu_Run2012B_193834-194270: 289270 entries (trijet pT), 289270 entries (max b-tag)
    SingleMu_Run2012B_194271-194789: 497298 entries (trijet pT), 497298 entries (max b-tag)
    SingleMu_Run2012B_194790-195398: 276498 entries (trijet pT), 276498 entries (max b-tag)
    SingleMu_Run2012B_195399-195841: 247576 entries (trijet pT), 247576 entries (max b-tag)
    SingleMu_Run2012B_195842-196531: 387297 entries (trijet pT), 387297 entries (max b-tag)
    trijet pT histogram, all datasets: 1697939 entries
    max b-tag histogram, all datasets: 1697939 entries
    </div>

=== "RDataFrame"

    About 50 seconds in, it ends like this. The first call that each worker
    process handles takes a few seconds (here, 4), because ROOT compiles the
    C++ in `BestTrijet` then; the later ones take 1 or 2 seconds:

    <div class="term">
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_0.root[50000:53733] (id=fd603f14) cores=1(1) memory_mb=875 wall_time_s=4
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_0.root[0:50000] (id=56011973) cores=1(1) memory_mb=875 wall_time_s=4
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_1.root[50000:100000] (id=e552d1a9) cores=1(1) memory_mb=920 wall_time_s=1
    ...
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_195842-196531 ...2-196531/file_2.root[50000:99449] (id=13656446) cores=1(1) memory_mb=986 wall_time_s=1
    <span class="t-green">success             </span> reducer   trijet/SingleMu_Run2012B_195842-196531 reduction of 10 partials (id=654a1bf1) cores=1(1) memory_mb=984 wall_time_s=1
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=59704670) cores=1(1) memory_mb=984 wall_time_s=1
    trijet     [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">83</span>/<span class="t-red">0</span>/<span class="t-blue">83</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">11</span>/<span class="t-red">0</span>/<span class="t-blue">11</span>
    events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>
    SingleMu_Run2012B_193834-194270: 289270 entries (trijet pT), 289270 entries (max b-tag)
    SingleMu_Run2012B_194271-194789: 497298 entries (trijet pT), 497298 entries (max b-tag)
    SingleMu_Run2012B_194790-195398: 276498 entries (trijet pT), 276498 entries (max b-tag)
    SingleMu_Run2012B_195399-195841: 247576 entries (trijet pT), 247576 entries (max b-tag)
    SingleMu_Run2012B_195842-196531: 387297 entries (trijet pT), 387297 entries (max b-tag)
    trijet pT histogram, all datasets: 1697939 entries
    max b-tag histogram, all datasets: 1697939 entries
    </div>

Fifteen files were cut into 83 chunks of up to 50,000 events each (for example,
`file_0.root[0:50000]` is the first chunk of the first file of a dataset),
which gave 83 `processor` calls and 11 reductions folding their outputs
together, with the last one of each dataset marked `(final)`, and all
`3736416/3736416` events accounted for. Each of the five datasets is its own
pipeline (the **datasets** bar counts them, `5/5`), with its own result, and the
last lines show the entries of each, then the totals.
There was no cluster, no `vine_factory`/`vine_worker`, and nothing on the
network; every call above ran in a local subprocess on this machine.

### Reading a task line

Each `success` line ends with something like `cores=1(1) memory_mb=255
wall_time_s=1`, which reads as `measured(allocated)` per resource. For
example, `cores=1(1)` means that the task was *measured* using 1 core and was
*allocated* 1 core. `memory_mb=255`, however, has no parentheses, because there
was no allocation to compare against: `LocalDistributor` doesn't cap memory
per task, and thus only the measurement is shown. Once there *is* an
allocation to under- or overshoot, this is where you will see it, as in
[Module 5](module-05-resources.md).

### Reading the four bars

Each bar is `[ bar ] numbers`. The bar is
<span class="clr-green">**green**</span> for done,
<span class="clr-red">**red**</span> for permanently failed, and
<span class="clr-gray">**gray**</span> for whatever is left; there is no gray
above, since the run is over. The numbers spell out the same counts, although
not every row has all three:

- **trijet** and **reductions**:
  <span class="clr-yellow">done</span>/<span class="clr-red">failed</span>/<span class="clr-blue">total</span>
  task counts, that is, `processor` calls for **trijet** (the row is named
  after the processor), and `reducer`/`final` calls for **reductions**.
  These two totals are *estimates*, extrapolated from the work done so
  far — chunks are cut as the run goes, and after failures they can even
  briefly disagree with done + failed (you'll see this in
  [Module 5](module-05-resources.md)). The **events** total, by contrast,
  is exact, summed from the dataset file.
- **datasets**:
  <span class="clr-green">done</span>/<span class="clr-cyan">total</span>,
  with no failed column, as a dataset is either still running or finished.
- **events**:
  <span class="clr-yellow">done</span>(<span class="clr-green">safe</span>)/<span class="clr-red">failed</span>/<span class="clr-blue">total</span>,
  the one row with an extra number in parentheses.

!!! info "What does (safe) mean?"
    The <span class="clr-green">green</span> number in parentheses on the
    **events** row is how many of the
    <span class="clr-yellow">done</span> events are *durably* done, that is,
    written to disk in a way that survives this process dying right now, as
    opposed to only computed in memory. Above, all `3736416(3736416)` are
    safe, because the run finished and its result was written to `results/`.
    [Module 6](module-06-checkpoints-restart.md) covers *checkpoints*, which
    make events safe *before* the whole run finishes. The takeaway for now is
    that if `vine_reduce` (or this machine) died partway through, only the
    events **not** counted as <span class="clr-green">safe</span> would have
    to be processed again on restart.

!!! info "Also produced"
    `results/<dataset name>/trijet/*.pkl.zst` is the final result of each dataset,
    a dict of two `hist.Hist` objects, written by `vine_reduce.serialization`.
    `results/vine_reduce.db` is the sqlite state that `vine_reduce` uses to
    know what has already been computed (covered in
    [Module 6](module-06-checkpoints-restart.md)), and `results/size.jsonl`
    gets one summary line (result size, peak resources) per finished
    pipeline. The script deletes `results/` and `checkpoints/` at the start
    of every run.

## The three components of the script

Open the script (`scripts/vr_trijet_iterative.py`, or
`scripts/vr_trijet_iterative_rdf.py` for RDataFrame). Every later module's
script is a variation on exactly these three pieces; therefore, once you can
name them here, you should be able to read any of the later ones.

**1. The datasets**, each a name plus a list of files, from Module 1 (five
datasets, read from `/project01`):

```python
datasets_path = os.path.join(REPO_ROOT, "data", "datasets_vast.json")
```

=== "coffea"

    **2. A processor**, with one call per chunk, `events` in, and anything
    picklable out:

    ```python
    def trijet_processor(events):
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
            "trijetpt": hist.Hist.new.Reg(100, 0, 200, name="pt3j").Double().fill(trijet.p4.pt),
            "maxbtag": hist.Hist.new.Reg(100, 0, 1, name="btag").Double().fill(maxBtag),
        }
    ```

    This is ADL benchmark Q6, unmodified. (The file also passes a `label=` to
    each histogram axis, trimmed here for width.) For every event with at
    least three jets, it builds every 3-jet combination, keeps the one whose invariant mass
    is closest to 172.5 GeV, and fills two histograms with that trijet's $p_T$
    and its highest jet b-tag score. If you have written a `coffea`
    `ProcessorABC.process(self, events)`, this is that method's body; the
    difference is that `vine_reduce` processors are plain functions rather than
    classes.

    **3. The reducer**, which is not written anywhere in this script, because the
    default one already does the right thing. Two results are folded together by
    `a[key] += b[key]` for every key, and `hist.Hist` objects already know how to
    add. Thus, a dict of two Hists goes in, and a dict of two Hists (covering more
    events) comes out. [Module 7](module-07-result-postprocess.md) is where a
    processor's output stops being "a Hist or a dict of Hists" and a custom
    reducer becomes necessary.

=== "RDataFrame"

    **2. A processor**, with one call per chunk, an `RDataFrame` in, and anything
    picklable out:

    ```python
    def trijet_processor(df):
        ROOT.gInterpreter.Declare(TRIJET_CPP)  # compile BestTrijet, once per process

        best = (
            df.Filter("nJet >= 3")
            .Define("best", "BestTrijet(Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_btag)")
            .Define("trijet_pt", "best[0]")
            .Define("max_btag", "best[1]")
        )
        trijetpt = best.Histo1D(("trijetpt", "...", 100, 0, 200), "trijet_pt")
        maxbtag = best.Histo1D(("maxbtag", "...", 100, 0, 1), "max_btag")
        return {
            "trijetpt": to_hist(trijetpt.GetValue()),
            "maxbtag": to_hist(maxbtag.GetValue()),
        }
    ```

    The per-event work is in `TRIJET_CPP`, a short C++ function that sits at the
    top of the script:

    ```cpp
    ROOT::RVecD BestTrijet(const ROOT::RVecF &pt, const ROOT::RVecF &eta,
                           const ROOT::RVecF &phi, const ROOT::RVecF &mass,
                           const ROOT::RVecF &btag) {
      ...  // try every 3-jet combination, keep the one closest to 172.5 GeV
      return best;  // {its pT, its highest b-tag score, its mass}
    }
    ```

    This is ADL benchmark Q6 again. For every event with at least three jets
    (`Filter`), `BestTrijet` builds every 3-jet combination and keeps the one
    whose invariant mass is closest to 172.5 GeV, and two histograms (`Histo1D`)
    are filled with that trijet's $p_T$ and its highest jet b-tag score.
    RDataFrame is lazy, so nothing has been read yet when the histograms are
    booked; the first `GetValue()` makes one pass over the chunk's events that
    fills both. ROOT's histograms are then copied into `hist.Hist` objects
    (`to_hist`), so that what comes back is the same dict of two Hists that the
    coffea flavor returns.

    Where does the `RDataFrame` come from? `VineReduceCoffea` would hand a
    coffea processor its `events`; with plain `VineReduce`, you say how a chunk
    (a file and an entry range) becomes the processor's input, in a small
    function that also runs once per chunk:

    ```python
    def chunk_to_args(chunk, dataset_metadata, distributor_metadata=None):
        return ROOT.RDataFrame("Events", chunk.url).Range(chunk.start, chunk.stop)
    ```

    **3. The reducer**, which is not written anywhere in this script, because
    `coffea_reducer` (from `vine_reduce.coffea`) already does the right thing,
    and the script passes it as `reducer=`. Two results are folded together by
    `a[key] += b[key]` for every key, and `hist.Hist` objects already know how to
    add. Thus, a dict of two Hists goes in, and a dict of two Hists (covering more
    events) comes out. [Module 7](module-07-result-postprocess.md) is where a
    processor's output stops being "a Hist or a dict of Hists" and a custom
    reducer becomes necessary.

## What actually ran it

=== "coffea"

    ```python
    distributor = LocalDistributor(max_workers=2)

    vr = VineReduceCoffea(
        processors={"trijet": trijet_processor},
        input=datasets_path,
        distributor=distributor,
        results_dir=results_dir,
        checkpoint_dir=checkpoint_dir,
        chunksize=50_000,
    )

    with distributor:
        vr.compute()
    ```

=== "RDataFrame"

    ```python
    distributor = LocalDistributor(max_workers=2)

    vr = VineReduce(
        processors={"trijet": trijet_processor},
        input=datasets_path,
        distributor=distributor,
        results_dir=results_dir,
        checkpoint_dir=checkpoint_dir,
        chunksize=50_000,
        chunk_to_args=chunk_to_args,
    )

    with distributor:
        vr.compute()
    ```

    The last tell VineReduce how to to turn a chunk into the
    processor's input.

`LocalDistributor` runs every processor/reducer call in a local
`ProcessPoolExecutor`. Its "workers" are subprocesses that already share this
process's filesystem and Python environment, thus there is no need
to specify environments, execution sites, etc.

`chunksize=50_000` is the most events that any one `processor` call gets.
Without it, each *file* would be one chunk.

!!! note "What `max_workers` controls"
    `LocalDistributor(max_workers=2)` lets two calls run at once. With
    `max_workers=1` instead, only **one** call would ever run at a time, and
    the run would take longer, with the `success` lines arriving strictly one
    at a time. The totals, however, would not change: `3736416` events, and
    `1697939` entries in each histogram. In other words, `max_workers`
    controls how much runs in parallel, rather than what gets computed.

[Module 3](module-03-local-factory.md) runs this *exact same*
`trijet_processor` over the same five datasets, but through a real
TaskVine manager and worker instead. Only the distributor changes.
