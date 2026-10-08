# Module 5 - Resources & chunk/reduction size

**15 min**

Three numbers decide how your run uses the pool. The first is
**`chunksize`**, which is how many events go into one processor call. The
second is the pair **`resources_processor` / `resources_reducer`**, which
says how much of a worker one call may use. The third is
**`reduction_size`**, which is how many partial results one reducer call
folds together.

This module sets the first two wrong on purpose so that you can watch
what VineReduce does about it, and then changes the third to see what it does (and,
perhaps more importantly, what it doesn't do).

## What changed in the script

This module's script (`scripts/vr_trijet_resources.py`,
or `scripts/vr_trijet_resources_rdf.py`) is Module 4's
(`vr_trijet_condor.py`, or `vr_trijet_condor_rdf.py`), with the three knobs
exposed as command-line arguments, so that you can try different values by
retyping the command rather than by editing a file (run it as always, with
`python` after `conda activate`, or through `pixi run python`):

```text
scripts/vr_trijet_resources.py CHUNKSIZE MEMORY_MB [REDUCTION_SIZE]
```

In the RDataFrame script, the file name is `vr_trijet_resources_rdf.py`.
The diff against Module 4 is the same for both flavors:

```diff
+import sys
 ...
+DATASET = "SingleMu_Run2012B_194790-195398"
+
 ...
 def main():
-    datasets_path = os.path.join(REPO_ROOT, "data", "datasets_xrootd.json")
+    chunksize = int(sys.argv[1])
+    memory_mb = int(sys.argv[2])
+    reduction_size = int(sys.argv[3]) if len(sys.argv) > 3 else 10
+    print(f"chunksize={chunksize} memory_mb={memory_mb} reduction_size={reduction_size}")
+
+    # Just one file of the real data: the first of dataset DATASET
+    with open(os.path.join(REPO_ROOT, "data", "datasets_xrootd.json")) as f:
+        all_datasets = json.load(f)
+    files = all_datasets[DATASET]["files"]
+    first_file = next(iter(files))
+    datasets = {
+        DATASET: {
+            "metadata": all_datasets[DATASET]["metadata"],
+            "files": {first_file: files[first_file]},
+        }
+    }
 ...
-        resources_processor={"cores": 1, "memory_mb": 2000},
+        resources_processor={"memory_mb": memory_mb},
         resources_reducer={"cores": 1, "memory_mb": 2000},
 ...
-        input=datasets_path,
+        input=datasets,
 ...
-        chunksize=100_000,
+        chunksize=chunksize,
+        reduction_size=reduction_size,
 ...
-    (the loop over all five datasets and the total)
+    result = load_result(results_dir, DATASET, "trijet")
+    trijetpt_entries = result["trijetpt"].sum(flow=True)
+    maxbtag_entries = result["maxbtag"].sum(flow=True)
+    print(f"trijet pT histogram: {trijetpt_entries:.0f} entries")
+    print(f"max b-tag histogram: {maxbtag_entries:.0f} entries")
```

The script reads just one of the 15 files, the first file of
`SingleMu_Run2012B_194790-195398` (430,713 events), so that one chunk can hold
all of it.

Keep your factory from Module 4 running in terminal 2; if it has exited,
restart it with the same command.

## How much memory does a chunk need?

=== "coffea"

    Measured with a generous limit, for that one file:

    | `chunksize` | peak memory of one processor call |
    |---|---|
    | 430,713 (the whole file) | 1,837 MB |
    | 215,357 | 991 MB |
    | 107,678 | 615 MB |

    Memory grows with the number of events in the chunk. Thus, the number is
    decided by your processor, your data, and your chunk size, rather than by
    VineReduce.

=== "RDataFrame"

    Measured with a generous limit, for that one file:

    | `chunksize` | peak memory of one processor call |
    |---|---|
    | 430,713 (the whole file) | 1,050 MB |
    | 215,357 | 1,049 MB |
    | 107,678 | 1,047 MB |

    Memory does **not** grow with the number of events in the chunk: RDataFrame
    streams through the entries, a few at a time. What costs memory is ROOT
    itself, which takes about 750 MB to start up and compile `BestTrijet`
    before the first event is read. Thus, the number is decided by ROOT and
    your C++, rather than by your chunk size, and a smaller chunk saves no
    memory at all.

    *The RDataFrame output in this module was captured with a local worker of the same size as the pool's (4 cores, 8064 MB), rather than on the pool itself, so your hosts and timings will differ.*

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
    worker's memory, which on today's 4-core, ~8 GB workers is 2GB.
    Any smaller `memory_mb` is therefore never the real limit. Declaring
    memory alone makes `memory_mb` the number that counts.

For a reference pair from a real analysis, `vine-cms-analysis-stack`'s
`examples/scale-cortado/vr_cortado.py` uses `resources_processor={"memory_mb":
1000}` and `resources_reducer={"memory_mb": 8000}`. Skims are cheap per
chunk but expensive to merge, so the reducer gets far more. This is a good
reminder that the two limits need not look alike.

## Break it: a limit that is too small

=== "coffea"

    Ask for the whole file in one chunk, which needs 1,837 MB, but allow only
    700 MB:

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_resources.py 430713 700
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_resources.py 430713 700
        ```

    If TaskVine's resource monitor catches the call over its limit, this is
    what VineReduce does, and what the memory table above predicts:

    1. `[0:430713]`, the whole file, is killed at over its 700 MB limit. That is a
       `resource_exhaustion`, and thus the `trijet` bar's red count goes up.
    2. VineReduce **halves the chunksize** and cuts the file again, into
       `[0:215356]` and `[215356:430713]`.
    3. `[0:215356]` still needs about 990 MB, so it is killed and halved again,
       into `[0:107678]` and `[107678:215356]`.
    4. The smaller pieces need about 615 MB, which fits. They finish, one final
       reduction folds the partial results, and the answer is the same **206,251**
       entries that a run without a limit gives.

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
        isn't always caught, in particular when it is short. When this page was
        tested, the whole-file call took 2 seconds and finished at 1,837 MB
        under its 700 MB limit, with no `resource_exhaustion` at all, in 5 tries
        out of 5 (it printed `trijet 1/0/1` and 206,251 entries), and even with a
        limit of 300 MB. For that reason, no output of a kill is shown here for
        coffea. Either way, the answer is correct; the only thing that changes is
        how much work is thrown away and redone.

=== "RDataFrame"

    With RDataFrame there is no chunk that is too big for its limit: as the table
    above shows, a call needs about the same memory whether it holds 107,678
    events or 430,713. What can go wrong instead is a limit below ROOT's own
    floor. Allow only 700 MB for the whole-file chunk:

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_resources_rdf.py 430713 700
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_resources_rdf.py 430713 700
        ```

    <div class="term">
    chunksize=430713 memory_mb=700 reduction_size=10
    ...
    <span class="t-red">resource_exhaustion </span> processor trijet/SingleMu_Run2012B_194790-195398 ...0-195398/file_0.root[0:430713] (id=ccaae557) cores=1(1) memory_mb=939(700) wall_time_s=1(0)
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_194790-195398 ...0-195398/file_0.root[430712:430713] (id=62d0286e) cores=1(1) memory_mb=894(1973) wall_time_s=4(0)
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_194790-195398 ...0-195398/file_0.root[0:215356] (id=3004b8ad) cores=1(1) memory_mb=979(1973) wall_time_s=9(0)
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_194790-195398 ...0-195398/file_0.root[215356:430712] (id=48f127bc) cores=1(1) memory_mb=979(1973) wall_time_s=10(0)
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_194790-195398 reduction of 3 partials (final) (id=66f233ad) cores=1(1) memory_mb=202(2016) wall_time_s=1(0)
    trijet     [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">3</span>/<span class="t-red">1</span>/<span class="t-blue">2</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
    events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">430713</span>(<span class="t-green">430713</span>)/<span class="t-red">430713</span>/<span class="t-blue">430713</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>
    trijet pT histogram: 206251 entries
    max b-tag histogram: 206251 entries
    </div>

    Read it top to bottom:

    1. `[0:430713]`, the whole file, was killed at 939 MB, over its 700 MB limit,
       one second in. That is ROOT compiling `BestTrijet`, before the events were
       read, and a `resource_exhaustion`; the `trijet` bar's red count goes up.
    2. VineReduce **halved the chunksize** and cut the file again, into
       `[0:215356]`, `[215356:430712]` and a one-event `[430712:430713]` left over by
       the odd total.
    3. These retries were allocated **1,973 MB** rather than 700 (see
       `memory_mb=979(1973)`), and finished.

    The run succeeded, but the halving did not help: the halved chunks needed the
    same 979 MB, since memory does not depend on the chunk. What let it finish was
    the larger allocation that the retries got, and it cost a killed call and
    more, smaller ones. The red `430713` on the events bar counts the events in
    the killed call, rather than events lost: `430713(430713)` shows that all of
    them made it into the result. (Don't be thrown by the `3/1/2` on the `trijet`
    bar either: as Module 2 noted, the task totals are estimates, and halving
    chunks mid-run throws them off.)

    The lesson is that VineReduce's recovery is for limits that are wrong for
    the *chunk*; one that is wrong for the *task* is better fixed by a limit
    above the floor.

## Fix it: a limit that fits

=== "coffea"

    Same whole-file chunk (1,837 MB needed), this time with room to spare:

    === "Option A: conda"

        ```bash
        python scripts/vr_trijet_resources.py 430713 2500
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_resources.py 430713 2500
        ```

    <div class="term">
    chunksize=430713 memory_mb=2500 reduction_size=10
    ...
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_194790-195398 ...0-195398/file_0.root[0:430713] (id=f14b5d87) cores=1(1) memory_mb=1837(2500) wall_time_s=2(0)
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_194790-195398 reduction of 1 partial (final)  (id=04c91a6e) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    trijet     [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
    events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">430713</span>(<span class="t-green">430713</span>)/<span class="t-red">0</span>/<span class="t-blue">430713</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>
    trijet pT histogram: 206251 entries
    max b-tag histogram: 206251 entries
    </div>

    This time there is one processor call for the whole file, using 1,837 MB
    of the 2,500 allowed, with no retries, and the 206,251 entries.

    Both runs give the right answer; the difference is cost. A limit that is
    too small wastes whole attempts, whereas one that is far too large means
    fewer calls fit on each worker.

=== "RDataFrame"

    Same whole-file chunk, this time with a limit above ROOT's floor:

    === "Option A: conda"

        ```bash
        python scripts/vr_trijet_resources_rdf.py 430713 1500
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_resources_rdf.py 430713 1500
        ```

    <div class="term">
    chunksize=430713 memory_mb=1500 reduction_size=10
    ...
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_194790-195398 ...0-195398/file_0.root[0:430713] (id=85800eef) cores=1(1) memory_mb=978(1500) wall_time_s=14(0)
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_194790-195398 reduction of 1 partial (final)  (id=23bbf0d7) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    trijet     [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
    events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">430713</span>(<span class="t-green">430713</span>)/<span class="t-red">0</span>/<span class="t-blue">430713</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>
    trijet pT histogram: 206251 entries
    max b-tag histogram: 206251 entries
    </div>

    This time there is one processor call for the whole file, using 978 MB of
    the 1,500 allowed, with no retries, and the same 206,251 entries.

    The limit decides how much work is wasted. One that is too small wastes whole
    attempts, whereas one that is far too large means fewer calls fit on each
    worker. Therefore, perhaps the best habit is to measure first, and then set
    the limit a bit above what you saw: 978 MB seen here, 1,500 MB set.

## `reduction_size`: a fan-in, not a resource

`reduction_size` (default 10) is how many partial results one reducer call
folds together. In Module 4, a dataset with 8 chunks or fewer fit in one
reduction, as in `final ... reduction of 8 partials`. Now force pairs, on
five chunks of the one file:

=== "coffea"

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
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_194790-195398 ...0-195398/file_0.root[0:100000] (id=f3a50176) cores=1(1) memory_mb=591(2500) wall_time_s=1(0)
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_194790-195398 ...0-195398/file_0.root[300000:400000] (id=b01085e6) cores=1(1) memory_mb=532(2500) wall_time_s=1(0)
    <span class="t-green">success             </span> reducer   trijet/SingleMu_Run2012B_194790-195398 reduction of 2 partials  (id=0618cfdb) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> reducer   trijet/SingleMu_Run2012B_194790-195398 reduction of 2 partials  (id=5f31f80b) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> reducer   trijet/SingleMu_Run2012B_194790-195398 reduction of 2 partials  (id=aace1a3a) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> result    trijet/SingleMu_Run2012B_194790-195398 reduction of 2 partials (final)  (id=f0258ae2) cores=1(1) memory_mb=202(2016) wall_time_s=1(0)
    trijet     [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">5</span>/<span class="t-red">0</span>/<span class="t-blue">5</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">4</span>/<span class="t-red">0</span>/<span class="t-blue">4</span>
    events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">430713</span>(<span class="t-green">430713</span>)/<span class="t-red">0</span>/<span class="t-blue">430713</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>
    trijet pT histogram: 206251 entries
    max b-tag histogram: 206251 entries
    </div>

=== "RDataFrame"

    === "Option A: conda"

        ```bash
        python scripts/vr_trijet_resources_rdf.py 100000 1500 2
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_resources_rdf.py 100000 1500 2
        ```

    <div class="term">
    chunksize=100000 memory_mb=1500 reduction_size=2
    ...
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_194790-195398 ...0-195398/file_0.root[300000:400000] (id=14653ae5) cores=1(1) memory_mb=973(1500) wall_time_s=6(0)
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_194790-195398 ...0-195398/file_0.root[0:100000] (id=9959b1d9) cores=1(1) memory_mb=975(1500) wall_time_s=7(0)
    <span class="t-green">success             </span> reducer   trijet/SingleMu_Run2012B_194790-195398 reduction of 2 partials  (id=2866c5bc) cores=1(1) memory_mb=202(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> reducer   trijet/SingleMu_Run2012B_194790-195398 reduction of 2 partials  (id=be5746ab) cores=1(1) memory_mb=202(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> reducer   trijet/SingleMu_Run2012B_194790-195398 reduction of 2 partials  (id=2ca807c1) cores=1(1) memory_mb=202(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> result    trijet/SingleMu_Run2012B_194790-195398 reduction of 2 partials (final)  (id=846db819) cores=1(1) memory_mb=202(2016) wall_time_s=1(0)
    trijet     [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">5</span>/<span class="t-red">0</span>/<span class="t-blue">5</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">4</span>/<span class="t-red">0</span>/<span class="t-blue">4</span>
    events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">430713</span>(<span class="t-green">430713</span>)/<span class="t-red">0</span>/<span class="t-blue">430713</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>
    trijet pT histogram: 206251 entries
    max b-tag histogram: 206251 entries
    </div>

The run has 5 chunks and the same 206,251 entries; however, the
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
