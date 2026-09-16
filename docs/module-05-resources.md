# Module 5 - Resources & chunk/reduction size

**15 min**

Three numbers decide how your run uses the pool. The first is
**`chunksize`**, which is how many events go into one processor call. The
second is the pair **`resources_processor` / `resources_reducer`**, which
says how much of a worker one call may use. The third is
**`reduction_size`**, which is how many partial results one reducer call
folds together.

This module sets the first two wrong on purpose so that you can watch
VineReduce recover, and then changes the third to see what it does (and,
perhaps more importantly, what it doesn't do).

## Get the script

```bash
curl -sL -o scripts/vr_trijet_resources.py \
  https://raw.githubusercontent.com/cooperative-computing-lab/vine-cms-analysis-stack-tutorials/main/scripts/vr_trijet_resources.py
```

This is Module 4's `vr_trijet_condor.py`, with the three knobs exposed as
command-line arguments (run it as always, with `python` after `conda
activate`, or through `pixi run python`):

```text
scripts/vr_trijet_resources.py CHUNKSIZE MEMORY_MB [REDUCTION_SIZE]
```

Keep your factory from Module 4 running in terminal 2; if it has exited,
restart it with the same command.

## How much memory does a chunk need?

Measured on the pool with a generous limit, for the one real-data file:

| `chunksize` | peak memory of one processor call |
|---|---|
| 500,000 (the whole file) | 1,872 MB |
| 250,000 | 1,091 MB |
| 125,000 | 539 MB |

Memory grows with the number of events in the chunk. Thus, the number is
decided by your processor, your data, and your chunk size, rather than by
VineReduce.

## Declaring resources

```python
distributor = TaskVineDistributor(
    ...
    resources_processor={"memory_mb": memory_mb},
    resources_reducer={"cores": 1, "memory_mb": 2000},
)
```

These are **limits per call**. TaskVine uses them to decide how many calls
fit on a worker at once, and its resource monitor kills a call that grows
well past its limit. VineReduce reports such a kill as
`resource_exhaustion`, as opposed to a bug in your code.

!!! note "Why only `memory_mb` for the processor here"
    In Module 4 the processor declared `{"cores": 1, "memory_mb": 2000}`.
    A call that declares 1 core is given at least that core's share of the
    worker's memory, which on today's 4-core, ~8 GB workers is 2016 MB.
    Any smaller `memory_mb` is therefore never the real limit. Declaring
    memory alone makes `memory_mb` the number that counts.

For a reference pair from a real analysis, `vine-cms-analysis-stack`'s
`examples/scale-cortado/vr_cortado.py` uses `resources_processor={"memory_mb":
1000}` and `resources_reducer={"memory_mb": 8000}`. Skims are cheap per
chunk but expensive to merge, so the reducer gets far more. This is a good
reminder that the two limits need not look alike.

## Break it: a chunk too big for its limit

Ask for the whole file in one chunk, which needs 1,872 MB, but allow only
700 MB:

=== "Option A: conda"

    ```bash
    conda activate vine-cms-analysis-stack
    python scripts/vr_trijet_resources.py 500000 700
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/vr_trijet_resources.py 500000 700
    ```

<div class="term">
chunksize=500000 memory_mb=700 reduction_size=10
...
<span class="t-red">resource_exhaustion </span> processor trijet/SingleMu ...n2012B_SingleMu.root[0:500000] (id=16087434) cores=0(1) memory_mb=1176(700) wall_time_s=1(0)
<span class="t-red">resource_exhaustion </span> processor trijet/SingleMu ...n2012B_SingleMu.root[0:250000] (id=ce54dd71) cores=0(1) memory_mb=1056(700) wall_time_s=1(0)
<span class="t-green">success             </span> processor trijet/SingleMu ...n2012B_SingleMu.root[250000:500000] (id=a20d90e6) cores=1(1) memory_mb=990(700) wall_time_s=5(0)
<span class="t-green">success             </span> processor trijet/SingleMu ...n2012B_SingleMu.root[0:125000] (id=40c90aa6) cores=1(1) memory_mb=530(700) wall_time_s=4(0)
<span class="t-green">success             </span> processor trijet/SingleMu ...n2012B_SingleMu.root[125000:250000] (id=8556c735) cores=1(1) memory_mb=758(700) wall_time_s=7(0)
<span class="t-green">success             </span> final     trijet/SingleMu reduction of 3 partials (final)  (id=99029db5) cores=1(1) memory_mb=190(2016) wall_time_s=1(0)
trijet     [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-yellow">3</span>/<span class="t-red">2</span>/<span class="t-blue">2</span>
reductions [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">500000</span>(<span class="t-green">500000</span>)/<span class="t-red">750000</span>/<span class="t-blue">500000</span>
datasets   [ <span class="t-green">██████████████████████████████</span> ]                          <span class="t-green">1</span>/<span class="t-cyan">1</span>
trijet pT histogram: 217890 entries
max b-tag histogram: 217890 entries
</div>

Read it top to bottom:

1. `[0:500000]`, the whole file, was killed at 1,176 MB, which is over its
   700 MB limit. That is a `resource_exhaustion`, and thus the `trijet`
   bar's red count goes up.
2. VineReduce **halved the chunksize** and cut the file again, into
   `[0:250000]` and `[250000:500000]`.
3. `[0:250000]` was still too big and was killed at 1,056 MB, so it was
   halved again, into `[0:125000]` and `[125000:250000]`.
4. The smaller pieces finished, one final reduction folded the 3 partial
   results, and the answer is the same **217,890** entries as Module 4.

The red `750000` on the events bar counts events in calls that were
killed (500,000 + 250,000), rather than events lost. All 500,000 made it
into the result, as `500000(500000)` shows. Don't be thrown by the
`trijet` bar's `3/2/2` either: as Module 2 noted, the task totals are
estimates extrapolated from work done so far, and halving chunks mid-run
throws the extrapolation off. The **events** row is the exact one.

The rules behind this are fairly simple. On `resource_exhaustion`,
`chunksize` is halved, and the halved size applies to chunks not yet cut.
Halving stops at `minimum_chunksize` (default 1000), and a chunk that is
still too big at that size is given up on. Further, a chunk gets `attempts`
tries (default 3), counting crashes and exhaustions together; however,
halving gives the new, smaller chunks a fresh budget. In other words, a
chunk that is simply too big is treated as a sizing problem rather than as
a failure.

!!! warning "Your run may not break at all"
    The resource monitor checks memory by sampling, so an over-limit call
    isn't always caught. For example, above `[250000:500000]` finished at
    990 MB and `[125000:250000]` at 758 MB, both over 700. When the
    identical command was run a second time, the whole-file chunk sailed
    past its 700 MB limit uncaught and finished at **1,879 MB**, with no
    `resource_exhaustion` at all. It printed `trijet 1/0/1` and the same 217,890 entries.

    If that happens to you, run it again. Either way, the answer is
    correct; the only thing that changes is how much work is thrown away
    and redone.

## Fix it: a limit that fits

Same whole-file chunk (1,872 MB needed), this time with room to spare:

=== "Option A: conda"

    ```bash
    python scripts/vr_trijet_resources.py 500000 2500
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/vr_trijet_resources.py 500000 2500
    ```

<div class="term">
chunksize=500000 memory_mb=2500 reduction_size=10
...
<span class="t-green">success             </span> processor trijet/SingleMu ...n2012B_SingleMu.root[0:500000] (id=814c483a) cores=1(1) memory_mb=1876(2500) wall_time_s=10(0)
<span class="t-green">success             </span> final     trijet/SingleMu reduction of 1 partial (final)  (id=906b8247) cores=1(1) memory_mb=190(2016) wall_time_s=1(0)
trijet     [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
reductions [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">500000</span>(<span class="t-green">500000</span>)/<span class="t-red">0</span>/<span class="t-blue">500000</span>
datasets   [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>
trijet pT histogram: 217890 entries
max b-tag histogram: 217890 entries
</div>

This time there is one processor call for the whole file, using 1,876 MB
of the 2,500 allowed, with no retries, and the same 217,890 entries as
Module 4.

Both runs give the right answer; the difference is cost. A limit that is
too small wastes whole attempts, whereas one that is far too large means
fewer calls fit on each worker. Therefore, perhaps the best habit is to
measure first, and then set the limit a bit above what you saw.

## `reduction_size`: a fan-in, not a resource

`reduction_size` (default 10) is how many partial results one reducer call
folds together. In Module 4, all 5 chunks fit in one reduction, as in
`final ... reduction of 5 partials`. Now force pairs:

=== "Option A: conda"

    ```bash
    python scripts/vr_trijet_resources.py 100000 2500 2
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/vr_trijet_resources.py 100000 2500 2
    ```

<div class="term">
chunksize=100000 memory_mb=2500 reduction_size=2
...
<span class="t-green">success             </span> reducer   trijet/SingleMu reduction of 2 partials  (id=e636bf83) cores=1(1) memory_mb=190(2016) wall_time_s=1(0)
<span class="t-green">success             </span> reducer   trijet/SingleMu reduction of 2 partials  (id=6f8fe14b) cores=1(1) memory_mb=190(2016) wall_time_s=1(0)
<span class="t-green">success             </span> reducer   trijet/SingleMu reduction of 2 partials  (id=873f236e) cores=1(1) memory_mb=190(2016) wall_time_s=1(0)
<span class="t-green">success             </span> result    trijet/SingleMu reduction of 2 partials (final)  (id=2ca268bf) cores=1(1) memory_mb=190(2016) wall_time_s=1(0)
trijet     [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">5</span>/<span class="t-red">0</span>/<span class="t-blue">5</span>
reductions [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">4</span>/<span class="t-red">0</span>/<span class="t-blue">4</span>
events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">500000</span>(<span class="t-green">500000</span>)/<span class="t-red">0</span>/<span class="t-blue">500000</span>
datasets   [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>
trijet pT histogram: 217890 entries
max b-tag histogram: 217890 entries
</div>

The run has the same 5 chunks and the same 217,890 entries; however, the
`reductions` bar went from `1/0/1` to `4/0/4`, since five partial results
folded two at a time need four reducer calls instead of one.

The last line's label also changed, from `final` to `result`. `final`
marks the reduction VineReduce *forces* at the end of a dataset, to fold
whatever partial results remain; `result` marks a reduction that
qualified as a final result *on its own* — here, the last pairwise fold
happened to cover every event by itself, so nothing had to be forced.
Both carry the `(final)` tag. [Module 7](module-07-result-postprocess.md)
makes this distinction do real work, with several `result` reductions per
run.

A larger `reduction_size` means fewer, bigger reducer calls, each holding
more partial results in memory at once. A smaller one, on the other hand,
means more, smaller calls, and thus more tasks to schedule. For histograms
like the ones here, every partial result is tiny, so the default of 10 is
fine. For skims ([Module 7](module-07-result-postprocess.md)), however,
partial results are large, and `reduction_size` together with
`resources_reducer` is what keeps a merge from running out of memory. Such
a case is where this knob becomes important, even though here it
barely seems to matter.
