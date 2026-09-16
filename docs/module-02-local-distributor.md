# Module 2 - Local distributor

**15 min**

## Run it

Fetch this module's script into `scripts/`, next to the data you generated
in Module 1. This is the same `vine-cms-analysis-stack` directory, and the
same `curl` pattern that every module from here on reuses:

```bash
curl -sL -o scripts/vr_trijet_iterative.py \
  https://raw.githubusercontent.com/cooperative-computing-lab/vine-cms-analysis-stack-tutorials/main/scripts/vr_trijet_iterative.py
```

=== "Option A: conda"

    ```bash
    conda activate vine-cms-analysis-stack
    python scripts/vr_trijet_iterative.py
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/vr_trijet_iterative.py
    ```

You will first see some warnings, such as `RuntimeWarning: Missing
cross-reference index for ...` and a `DeprecationWarning` from inside
`awkward`, all of which are harmless. `NanoAODSchema` expects every
cross-reference branch that a real NanoAOD file carries (electrons pointing
back at jets, and so on); however, the synthetic files only fill the branches
that `trijet_processor` reads, thus the schema warns about the rest and moves
on.

After that, `vine_reduce`'s own live console takes over, with one line per
finished call plus four progress bars that update in place. About 15 seconds
later it ends like this (the colors are what your own terminal shows):

<div class="term">
<span class="t-green">success             </span> processor trijet/ttbar_like ...bar_like/file_0.root[25000:50000] (id=2b324ea0) cores=1(1) memory_mb=255 wall_time_s=1
<span class="t-green">success             </span> processor trijet/ttbar_like ...bar_like/file_0.root[0:25000] (id=a48b84b1) cores=1(1) memory_mb=252 wall_time_s=1
<span class="t-green">success             </span> processor trijet/ttbar_like ...bar_like/file_0.root[50000:75000] (id=f8aeceb7) cores=1(1) memory_mb=256 wall_time_s=1
...
<span class="t-green">success             </span> processor trijet/ttbar_like ...bar_like/file_9.root[225000:249282] (id=aad6e742) cores=1(1) memory_mb=329 wall_time_s=1
<span class="t-green">success             </span> reducer   trijet/ttbar_like reduction of 10 partials (id=1bdc4983) cores=1(1) memory_mb=316 wall_time_s=1
<span class="t-green">success             </span> final     trijet/ttbar_like reduction of 5 partials (final) (id=5a73826f) cores=1(1) memory_mb=329 wall_time_s=1
trijet     [ <span class="t-green">██████████████████████████████</span> ]                  <span class="t-yellow">104</span>/<span class="t-red">0</span>/<span class="t-blue">104</span>
reductions [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">12</span>/<span class="t-red">0</span>/<span class="t-blue">12</span>
events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">2523470</span>(<span class="t-green">2523470</span>)/<span class="t-red">0</span>/<span class="t-blue">2523470</span>
datasets   [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">1</span>/<span class="t-cyan">1</span>
trijet pT histogram: 2367108 entries
max b-tag histogram: 2367108 entries
</div>

Ten files were cut into 104 chunks of up to 25,000 events each (for example,
`file_0.root[0:25000]` is the first chunk of the first file), which gave 104
`processor` calls and 12 reductions folding their outputs together, with the
last one marked `(final)`, and all `2523470/2523470` events accounted for.
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
    opposed to only computed in memory. Above, all `2523470(2523470)` are
    safe, because the run finished and its result was written to `results/`.
    [Module 6](module-06-checkpoints-restart.md) covers *checkpoints*, which
    make events safe *before* the whole run finishes. The takeaway for now is
    that if `vine_reduce` (or this machine) died partway through, only the
    events **not** counted as <span class="clr-green">safe</span> would have
    to be processed again on restart.

!!! info "Also produced"
    `results/ttbar_like/trijet/*.pkl.zst` is the final result, a dict of two
    `hist.Hist` objects, written by `vine_reduce.serialization`.
    `results/vine_reduce.db` is the sqlite state that `vine_reduce` uses to
    know what has already been computed (covered in
    [Module 6](module-06-checkpoints-restart.md)), and `results/size.jsonl`
    gets one summary line (result size, peak resources) per finished
    pipeline. The script deletes `results/` and `checkpoints/` at the start
    of every run.

## The three moving pieces

Open `scripts/vr_trijet_iterative.py`. Every later module's script is a
variation on exactly these three pieces; therefore, once you can name them
here, you should be able to read any of the later ones.

**1. A dataset**, which is a name plus a list of files, from Module 1:

```python
datasets_path = os.path.join(REPO_ROOT, "data", "datasets_synthetic.json")
```

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

## What actually ran it

```python
distributor = LocalDistributor(max_workers=2)

vr = VineReduceCoffea(
    processors={"trijet": trijet_processor},
    input=datasets_path,
    distributor=distributor,
    results_dir=results_dir,
    checkpoint_dir=checkpoint_dir,
    chunksize=25_000,
)

with distributor:
    vr.compute()
```

`LocalDistributor` runs every processor/reducer call in a local
`ProcessPoolExecutor`. Its "workers" are subprocesses that already share this
process's filesystem and Python environment, thus there is no environment
packaging, no `vine_factory`, and no `vine_worker`. This is why it is step
one: it is a fast way to check that an analysis works before paying for
a real cluster.

`chunksize=25_000` is the most events that any one `processor` call gets.
Without it, each *file* would be one chunk.

!!! example "Exercise: cap it at one worker"
    `LocalDistributor(max_workers=2)` lets two calls run at once. Change
    the script so only **one** call ever runs at a time, rerun it, and
    compare how long it takes.

    ??? note "Solution"
        ```python
        distributor = LocalDistributor(max_workers=1)
        ```

        The run takes roughly twice as long, and the `success` lines now
        arrive strictly one at a time. The totals, however, don't change:
        `2523470` events, and `2367108` entries in each histogram. In other
        words, `max_workers` controls how much runs in parallel, rather than
        what gets computed.

[Module 3](module-03-local-factory.md) runs this *exact same*
`trijet_processor` over the same `datasets_synthetic.json`, but through a real
TaskVine manager and worker instead. Only the distributor changes.
