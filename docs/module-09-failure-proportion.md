# Module 9 - `failure_proportion`

**15 min**

Real datasets have bad files, such as a replica that's gone, a site that's
down, or a file that's truncated. This module shows what VineReduce does
when one file can't be read at all, and the one number that decides whether
that kills your run.

## The rule

`failure_proportion` only looks at **processor** calls that failed for
good:

1. A chunk is tried up to `attempts` times (default 3).
2. If all of its attempts fail, the **whole file** that chunk came from is
   given up on. It's written to `failed_files.log` in the current
   directory and never retried.
3. After each file given up on, VineReduce checks, per dataset:

    ```
    files given up on / files in the dataset  >  failure_proportion  ->  abort
    ```

    "Files in the dataset" is the fixed count from your dataset file, not
    how many have finished so far.

`failure_proportion` must be in `[0, 1)`. The default, `0`, aborts on the
very first file given up on.

A **reducer** that fails for good, however, always aborts the run,
whatever `failure_proportion` says, given that a half-merged result can't
be trusted.

## What changed in the script

This module's script (`scripts/vr_trijet_failures.py`,
or `scripts/vr_trijet_failures_rdf.py`) is Module 2's
(`vr_trijet_iterative.py`, or `vr_trijet_iterative_rdf.py`; local, no workers
needed), over the same five datasets, plus one entry added in the script itself
to each dataset, namely a file that doesn't exist. The processor and
`load_result` are untouched; the diff against Module 2 is:

```diff
+import sys
 ...
+BAD_FILE_NAME = "DOES_NOT_EXIST.root"
+
 ...
 def main():
-    datasets_path = os.path.join(REPO_ROOT, "data", "datasets_vast.json")
+    failure_proportion = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
 ...
+    # Module 2's datasets, plus one bad file in each
+    with open(os.path.join(REPO_ROOT, "data", "datasets_vast.json")) as f:
+        datasets = json.load(f)
+    for dataset in datasets.values():
+        first_file = next(iter(dataset["files"]))
+        bad_file = first_file.rsplit("/", 1)[0] + "/" + BAD_FILE_NAME
+        dataset["files"][bad_file] = {"object_path": "Events", "num_entries": 100_000}
 ...
-        input=datasets_path,
+        input=datasets,
 ...
         chunksize=50_000,
+        failure_proportion=failure_proportion,
     )
```

(The rest of `main()` only swaps `dataset_names` for `datasets`, which
iterates over the same names, and prints a line about the setup.) That makes
4 files in each dataset, 1 of them bad, thus 1 / 4 = 0.25 for every dataset,
as the rule counts per dataset. The script takes `failure_proportion` as its
only argument, so you never edit it: you rerun it with a different number.

## Run 1: `failure_proportion=0`

=== "coffea"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_failures.py 0
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_failures.py 0
        ```

=== "RDataFrame"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_failures_rdf.py 0
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_failures_rdf.py 0
        ```

Given that 0.25 > 0, the run stops once the first bad file is given up on:

=== "coffea"

    This takes a few seconds:

    <div class="term">
    failure_proportion=0.0, 5 datasets of 4 files, 1 file in each of them missing
    ...
    <span class="t-red">failure             </span> processor trijet/SingleMu_Run2012B_193834-194270 .../DOES_NOT_EXIST.root[0:50000] ...
    ...
    trijet     [ <span class="t-green">████</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]             <span class="t-yellow">13</span>/<span class="t-red">0</span>/<span class="t-blue">95</span>
    reductions [ <span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]               <span class="t-yellow">0</span>/<span class="t-red">0</span>/<span class="t-blue">9</span>
    events     [ <span class="t-green">████</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ] <span class="t-yellow">575910</span>(<span class="t-green">0</span>)/<span class="t-red">0</span>/<span class="t-blue">4236416</span>
    datasets   [ <span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                 <span class="t-green">0</span>/<span class="t-cyan">5</span>
    Traceback (most recent call last):
    ...
    vine_reduce.pipeline.VineReduceError: processor 'trijet' failed on /project01/ndcms/btovar/store/user/btovar/tutorial/SingleMu_Run2012B/SingleMu_Run2012B_193834-194270/DOES_NOT_EXIST.root[0:50000] after 3 attempts (attempts=3):
    ...
    FileNotFoundError: [Errno 2] No such file or directory: '/project01/ndcms/btovar/store/user/btovar/tutorial/SingleMu_Run2012B/SingleMu_Run2012B_193834-194270/DOES_NOT_EXIST.root'
    </div>

    The run ended with no result, as `datasets 0/5` shows, and
    `results/SingleMu_Run2012B_193834-194270/trijet/` is empty. It stopped early, at the first of the five
    bad files, so most of the good chunks were never processed (`13` of an
    estimated `95` here). The task totals on the `trijet` and `reductions` bars are
    estimates, as Module 2 noted, and the bad files' chunks throw them off. The
    **events** row's total is exact: `4236416` counts the 15 real files plus the
    five bad entries' claimed 100,000 events each. This is a bit harsh for one
    missing file out of 20, but it is also the behavior you want by default.

=== "RDataFrame"

    This takes about 10 seconds:

    <div class="term">
    failure_proportion=0.0, 5 datasets of 4 files, 1 file in each of them missing
    ...
    <span class="t-red">failure             </span> processor trijet/SingleMu_Run2012B_193834-194270 .../DOES_NOT_EXIST.root[0:50000] ...
    ...
    trijet     [ <span class="t-green">████</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]             <span class="t-yellow">13</span>/<span class="t-red">0</span>/<span class="t-blue">95</span>
    reductions [ <span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]               <span class="t-yellow">0</span>/<span class="t-red">0</span>/<span class="t-blue">9</span>
    events     [ <span class="t-green">████</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ] <span class="t-yellow">575910</span>(<span class="t-green">0</span>)/<span class="t-red">0</span>/<span class="t-blue">4236416</span>
    datasets   [ <span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                 <span class="t-green">0</span>/<span class="t-cyan">5</span>
    Traceback (most recent call last):
    ...
    vine_reduce.pipeline.VineReduceError: processor 'trijet' failed on /project01/ndcms/btovar/store/user/btovar/tutorial/SingleMu_Run2012B/SingleMu_Run2012B_193834-194270/DOES_NOT_EXIST.root[0:50000] after 3 attempts (attempts=3):
    ...
    TypeError: none of the 10 overloaded methods succeeded. Full details:
    ...
        invalid_argument: RDataFrame: could not open file "/project01/ndcms/btovar/store/user/btovar/tutorial/SingleMu_Run2012B/SingleMu_Run2012B_193834-194270/DOES_NOT_EXIST.root".
    ...
    </div>

    The run ended with no result, as `datasets 0/5` shows, and
    `results/SingleMu_Run2012B_193834-194270/trijet/` is empty. The cause is in the exception, although you
    have to read down to it: PyROOT lists every `RDataFrame` constructor it tried,
    and only then says why the one that fits failed (`could not open file`). The run
    stopped early, at the first of the five bad files, so most of the good chunks
    were never processed (`13` of an estimated `95` here). The task totals on the
    `trijet` and `reductions` bars are estimates, as Module 2 noted, and the bad
    files' chunks throw them off. The **events** row's total is exact: `4236416`
    counts the 15 real files plus the five bad entries' claimed 100,000 events
    each. This is a bit harsh for one missing file out of 20, but it is also the
    behavior you want by default.

## Logs

```bash
cat failed_files.log
```

```
[2026-10-02T20:56:16.888673+00:00] permanent failure
  dataset:    SingleMu_Run2012B_193834-194270
  file:       /project01/ndcms/btovar/store/user/btovar/tutorial/SingleMu_Run2012B/SingleMu_Run2012B_193834-194270/DOES_NOT_EXIST.root
  stage:      processor
  attempts:   3
  resources allocated: {'cores': 1}
  resources measured:  ResourceUsage(cores=1, memory_mb=0, wall_time_s=0, disk_mb=None)
  last traceback:
    Traceback (most recent call last):
    ...
```

There is one entry per file given up on, with the dataset, the file, how
many attempts were made, and the last traceback. After a long run, this is
where you look first.

## Run 2: `failure_proportion=0.3`

The script is the same, with a different number on the command line:

=== "coffea"

    === "Option A: conda"

        ```bash
        python scripts/vr_trijet_failures.py 0.3
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_failures.py 0.3
        ```

=== "RDataFrame"

    === "Option A: conda"

        ```bash
        python scripts/vr_trijet_failures_rdf.py 0.3
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_failures_rdf.py 0.3
        ```

Given that 0.25 is not > 0.3, the run carries on without those files and
finishes:

=== "coffea"

    This takes about 12 seconds:

    <div class="term">
    failure_proportion=0.3, 5 datasets of 4 files, 1 file in each of them missing
    ...
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=cb55a6f0) cores=1(1) memory_mb=496 wall_time_s=1
    <span class="t-red">WARNING: 5 file(s) were permanently skipped and left unprocessed; see /users/&lt;you&gt;/vine-cms-analysis-stack/examples/tutorial_nd/failed_files.log</span>
    trijet     [ <span class="t-green">██████████████████████████████</span> ]                         <span class="t-yellow">83</span>/<span class="t-red">25</span>/<span class="t-blue">72</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                          <span class="t-yellow">11</span>/<span class="t-red">0</span>/<span class="t-blue">11</span>
    events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">1250000</span>/<span class="t-blue">4236416</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                              <span class="t-green">5</span>/<span class="t-cyan">5</span>
    SingleMu_Run2012B_193834-194270: 289270 entries (trijet pT), 289270 entries (max b-tag)
    SingleMu_Run2012B_194271-194789: 497298 entries (trijet pT), 497298 entries (max b-tag)
    SingleMu_Run2012B_194790-195398: 276498 entries (trijet pT), 276498 entries (max b-tag)
    SingleMu_Run2012B_195399-195841: 247576 entries (trijet pT), 247576 entries (max b-tag)
    SingleMu_Run2012B_195842-196531: 387297 entries (trijet pT), 387297 entries (max b-tag)
    trijet pT histogram, all datasets: 1697939 entries
    max b-tag histogram, all datasets: 1697939 entries
    </div>

=== "RDataFrame"

    This takes about 50 seconds:

    <div class="term">
    failure_proportion=0.3, 5 datasets of 4 files, 1 file in each of them missing
    ...
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=8e08254b) cores=1(1) memory_mb=975 wall_time_s=1
    <span class="t-red">WARNING: 5 file(s) were permanently skipped and left unprocessed; see /users/&lt;you&gt;/vine-cms-analysis-stack/examples/tutorial_nd/failed_files.log</span>
    trijet     [ <span class="t-green">██████████████████████████████</span> ]                         <span class="t-yellow">83</span>/<span class="t-red">25</span>/<span class="t-blue">72</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                          <span class="t-yellow">11</span>/<span class="t-red">0</span>/<span class="t-blue">11</span>
    events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">1250000</span>/<span class="t-blue">4236416</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                              <span class="t-green">5</span>/<span class="t-cyan">5</span>
    SingleMu_Run2012B_193834-194270: 289270 entries (trijet pT), 289270 entries (max b-tag)
    SingleMu_Run2012B_194271-194789: 497298 entries (trijet pT), 497298 entries (max b-tag)
    SingleMu_Run2012B_194790-195398: 276498 entries (trijet pT), 276498 entries (max b-tag)
    SingleMu_Run2012B_195399-195841: 247576 entries (trijet pT), 247576 entries (max b-tag)
    SingleMu_Run2012B_195842-196531: 387297 entries (trijet pT), 387297 entries (max b-tag)
    trijet pT histogram, all datasets: 1697939 entries
    max b-tag histogram, all datasets: 1697939 entries
    </div>

The entries are exactly Module 2's answer, in every dataset and in total,
because the missing files never contributed any events. The red `WARNING`
line, in particular, is the part you must not scroll past. The result is
complete for the files that exist; however, it is **not** the whole dataset
you asked for.

!!! question "Pick your number"
    `failure_proportion=0` is the safe default, as any file lost is an
    error you'll notice. Raise it only when losing a few files is
    acceptable for what you're measuring, and always check
    `failed_files.log` afterwards.

*The output on this page was captured from a local copy of the files with
the same directory layout, rather than from `/project01` itself, so the paths
shown are the `/project01` ones.*
