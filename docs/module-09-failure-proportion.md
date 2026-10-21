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
2. If all of its attempts fail, that chunk's events are given up on. The
   chunk is written to `failed_files.log` in the current directory, and the
   rest of the dataset, including the other chunks of the same file, carries
   on without it, leaving a hole.
3. After each chunk given up on, VineReduce checks, per dataset:

    ```
    events given up on / events in the dataset  >  failure_proportion  ->  abort
    ```

    "Events in the dataset" is the fixed total from your dataset file, not
    how many have finished so far.

`failure_proportion` must be in `[0, 1)`. The default, `0`, aborts on the
very first chunk given up on.

A chunk given up on is not recorded as done, so a later run that resumes
from the same `results/` (as in [Module 6](module-06-checkpoints-restart.md))
tries it again.

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
4 files in each dataset, 1 of them bad. The bad file claims 100,000 events,
so with `chunksize=50_000` it is cut into two chunks, both of which fail. A
dataset thus loses 100,000 of its events, which is between 0.083 and 0.154 of
it (100,000 of 1,202,938 for the largest dataset, and of 649,171 for the
smallest), as the rule counts per dataset. The script takes
`failure_proportion` as its only argument, so you never edit it: you rerun it
with a different number.

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

Given that the first chunk given up on already puts its dataset above 0,
the run stops right there:

=== "coffea"

    This takes about 10 seconds:

    <div class="term">
    failure_proportion=0.0, 5 datasets of 4 files, 1 file in each of them missing
    ...
    <span class="t-red">failure             </span> processor trijet/SingleMu_Run2012B_193834-194270 .../DOES_NOT_EXIST.root[0:50000] ...
    ...
    trijet     [ <span class="t-green">█████</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                 <span class="t-yellow">15</span>/<span class="t-red">1</span>/<span class="t-blue">88</span>
    reductions [ <span class="t-green">███</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">9</span>
    events     [ <span class="t-green">█████</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░</span> ] <span class="t-yellow">671082</span>(<span class="t-green">0</span>)/<span class="t-red">50000</span>/<span class="t-blue">4236416</span>
    datasets   [ <span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                     <span class="t-green">0</span>/<span class="t-cyan">5</span>
    Traceback (most recent call last):
    ...
    vine_reduce.pipeline.VineReduceError: processor 'trijet' failed on /project01/ndcms/btovar/store/user/btovar/tutorial/SingleMu_Run2012B/SingleMu_Run2012B_193834-194270/DOES_NOT_EXIST.root[0:50000] after 3 attempts (attempts=3):
    ...
    FileNotFoundError: [Errno 2] No such file or directory: '/project01/ndcms/btovar/store/user/btovar/tutorial/SingleMu_Run2012B/SingleMu_Run2012B_193834-194270/DOES_NOT_EXIST.root'
    </div>

    The run ended with no result, as `datasets 0/5` shows, and
    `results/SingleMu_Run2012B_193834-194270/trijet/` is empty. It stopped early, at the first bad
    chunk given up on, so most of the good chunks were never processed (`15` of
    an estimated `88` here). The task totals on the `trijet` and `reductions` bars are
    estimates, as Module 2 noted, and the bad files' chunks throw them off. The
    **events** row's total is exact: `4236416` counts the 15 real files plus the
    five bad entries' claimed 100,000 events each. This is a bit harsh for one
    missing file out of 20, but it is also the behavior you want by default.

=== "RDataFrame"

    This takes about 20 seconds:

    <div class="term">
    failure_proportion=0.0, 5 datasets of 4 files, 1 file in each of them missing
    ...
    <span class="t-red">failure             </span> processor trijet/SingleMu_Run2012B_193834-194270 .../DOES_NOT_EXIST.root[0:50000] ...
    ...
    trijet     [ <span class="t-green">█████</span><span class="t-red">█</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                  <span class="t-yellow">15</span>/<span class="t-red">2</span>/<span class="t-blue">83</span>
    reductions [ <span class="t-green">███</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                    <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">9</span>
    events     [ <span class="t-green">█████</span><span class="t-red">█</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░</span> ] <span class="t-yellow">671082</span>(<span class="t-green">0</span>)/<span class="t-red">100000</span>/<span class="t-blue">4236416</span>
    datasets   [ <span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                      <span class="t-green">0</span>/<span class="t-cyan">5</span>
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
    stopped early, at the first bad chunk given up on, so most of the good chunks
    were never processed (`15` of an estimated `83` here). The task totals on the
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
[2026-10-21T18:14:24.674855+00:00] permanent failure
  dataset:    SingleMu_Run2012B_193834-194270
  file:       /project01/ndcms/btovar/store/user/btovar/tutorial/SingleMu_Run2012B/SingleMu_Run2012B_193834-194270/DOES_NOT_EXIST.root
  events:     [0:50000]
  stage:      processor
  attempts:   3
  resources allocated: {'cores': 1}
  resources measured:  ResourceUsage(cores=1, memory_mb=0, wall_time_s=0, disk_mb=None)
  last traceback:
    Traceback (most recent call last):
    ...
```

There is one entry per chunk given up on, with the dataset, the file, the
chunk's event range in it, how many attempts were made, and the last
traceback. After a long run, this is where you look first. Each run appends
to `failed_files.log` rather than replacing it, so delete it first if you
want to see only the next run's entries.

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

Given that no dataset loses more than 0.154 of its events, which is below
0.3, the run carries on without those chunks and finishes:

=== "coffea"

    This takes about 35 seconds:

    <div class="term">
    failure_proportion=0.3, 5 datasets of 4 files, 1 file in each of them missing
    ...
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=8c6af99e) cores=1(1) memory_mb=524 wall_time_s=1
    <span class="t-red">WARNING: 10 chunk(s) (500000 event(s)) were permanently skipped and left unprocessed; see /users/&lt;you&gt;/vine-cms-analysis-stack/examples/tutorial_nd/failed_files.log</span>
    trijet     [ <span class="t-green">██████████████████████</span><span class="t-red">████████</span> ]                         <span class="t-yellow">83</span>/<span class="t-red">30</span>/<span class="t-blue">68</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                          <span class="t-yellow">11</span>/<span class="t-red">0</span>/<span class="t-blue">11</span>
    events     [ <span class="t-green">█████████████████████</span><span class="t-red">█████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">1500000</span>/<span class="t-blue">4236416</span>
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

    This takes about 70 seconds:

    <div class="term">
    failure_proportion=0.3, 5 datasets of 4 files, 1 file in each of them missing
    ...
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=36e14c0e) cores=1(1) memory_mb=981 wall_time_s=1
    <span class="t-red">WARNING: 10 chunk(s) (500000 event(s)) were permanently skipped and left unprocessed; see /users/&lt;you&gt;/vine-cms-analysis-stack/examples/tutorial_nd/failed_files.log</span>
    trijet     [ <span class="t-green">██████████████████████</span><span class="t-red">████████</span> ]                         <span class="t-yellow">83</span>/<span class="t-red">30</span>/<span class="t-blue">68</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                          <span class="t-yellow">11</span>/<span class="t-red">0</span>/<span class="t-blue">11</span>
    events     [ <span class="t-green">█████████████████████</span><span class="t-red">█████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">1500000</span>/<span class="t-blue">4236416</span>
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
because the missing files never contributed any events. The red counts on
the `trijet` and `events` rows count every failed attempt: 10 chunks (two per
bad file) times 3 attempts make 30 failed calls, and thus 1,500,000 events.
The red `WARNING` line counts each chunk given up on once instead: 10 chunks,
500,000 events, which is the five bad files' claimed 100,000 events each.
This line, in particular, is the part you must not scroll past. The result is
complete for the files that exist; however, it is **not** the whole dataset
you asked for.

!!! question "Pick your number"
    `failure_proportion=0` is the safe default, as any events lost are an
    error you'll notice. Raise it only when losing that fraction of a
    dataset's events is acceptable for what you're measuring, and always check
    `failed_files.log` afterwards.

*The output on this page was captured reading the same files over xrootd
(`root://cmsxrootd.crc.nd.edu`) rather than from `/project01` itself; the
paths shown are the `/project01` ones.*
