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

## Get the script

```bash
curl -sL -o scripts/vr_trijet_failures.py \
  https://raw.githubusercontent.com/cooperative-computing-lab/vine-cms-analysis-stack-tutorials/main/scripts/vr_trijet_failures.py
```

This is Module 2's script (local, no workers needed) over the same 10
synthetic files, plus one entry added in the script itself, namely a path
on CERN's public EOS that doesn't exist.

```python
BAD_FILE = "root://eospublic.cern.ch//eos/root-eos/benchmark/DOES_NOT_EXIST.root"
```

That makes 11 files, 1 of them bad, thus 1 / 11 = 0.09. The script takes
`failure_proportion` as its only argument.

## Run 1: `failure_proportion=0`

=== "Option A: conda"

    ```bash
    conda activate vine-cms-analysis-stack
    python scripts/vr_trijet_failures.py 0
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/vr_trijet_failures.py 0
    ```

Given that 0.09 > 0, the run stops once the bad file is given up on (after
about 20 seconds):

<div class="term">
failure_proportion=0.0, 11 files, 1 of them missing
...
<span class="t-red">failure             </span> processor trijet/ttbar_like .../DOES_NOT_EXIST.root[0:25000] ...
...
trijet     [ <span class="t-green">██████████████████████████████</span> ]                 <span class="t-yellow">104</span>/<span class="t-red">4</span>/<span class="t-blue">105</span>
reductions [ <span class="t-green">████████████████████████████</span><span class="t-gray">░░</span> ]                   <span class="t-yellow">11</span>/<span class="t-red">0</span>/<span class="t-blue">12</span>
events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">2523470</span>(<span class="t-green">0</span>)/<span class="t-red">100000</span>/<span class="t-blue">2623470</span>
datasets   [ <span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                       <span class="t-green">0</span>/<span class="t-cyan">1</span>
Traceback (most recent call last):
...
vine_reduce.pipeline.VineReduceError: processor 'trijet' failed on root://eospublic.cern.ch//eos/root-eos/benchmark/DOES_NOT_EXIST.root[0:25000] after 3 attempts (attempts=3):
...
OSError: Failed to open file: [ERROR] Server responded with an error: [3011] Unable to open file /eos/root-eos/benchmark/DOES_NOT_EXIST.root; No such file or directory
</div>

All 104 good chunks were processed. However, the run still ended with no
result, as `datasets 0/1` shows, and `results/ttbar_like/trijet/` is
empty. (The task totals on the `trijet` and `reductions` bars are
estimates, as Module 2 noted, and the bad file's failed chunks throw
them off — hence `104/4/105`. The **events** row is exact: `2623470`
counts the 10 real files plus the bad entry's claimed 100,000.) This is a bit harsh for one missing file out of 11, but it is also
the behavior you want by default.

## What got logged

```bash
cat failed_files.log
```

```
[2026-09-14T15:15:03.486885+00:00] permanent failure
  dataset:    ttbar_like
  file:       root://eospublic.cern.ch//eos/root-eos/benchmark/DOES_NOT_EXIST.root
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

## Run 2: `failure_proportion=0.1`

The code is the same, with one number changed:

=== "Option A: conda"

    ```bash
    python scripts/vr_trijet_failures.py 0.1
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/vr_trijet_failures.py 0.1
    ```

Given that 0.09 is not > 0.1, the run carries on without that file and
finishes (again in about 20 seconds):

<div class="term">
failure_proportion=0.1, 11 files, 1 of them missing
...
<span class="t-green">success             </span> final     trijet/ttbar_like reduction of 5 partials (final) (id=c3b4bb0a) cores=1(1) memory_mb=269 wall_time_s=1
<span class="t-red">WARNING: 1 file(s) were permanently skipped and left unprocessed; see /users/&lt;you&gt;/vine-cms-analysis-stack/failed_files.log</span>
trijet     [ <span class="t-green">██████████████████████████████</span> ]                       <span class="t-yellow">104</span>/<span class="t-red">7</span>/<span class="t-blue">102</span>
reductions [ <span class="t-green">██████████████████████████████</span> ]                         <span class="t-yellow">12</span>/<span class="t-red">0</span>/<span class="t-blue">12</span>
events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">2523470</span>(<span class="t-green">2523470</span>)/<span class="t-red">175000</span>/<span class="t-blue">2623470</span>
datasets   [ <span class="t-green">██████████████████████████████</span> ]                             <span class="t-green">1</span>/<span class="t-cyan">1</span>
trijet pT histogram: 2367108 entries
max b-tag histogram: 2367108 entries
</div>

The 2,367,108 entries are exactly Module 2's answer, because the missing
file never contributed any events. The red `WARNING` line, in particular,
is the part you must not scroll past. The result is complete for the files
that exist; however, it is **not** the whole dataset you asked for.

!!! question "Pick your number"
    `failure_proportion=0` is the safe default, as any file lost is an
    error you'll notice. Raise it only when losing a few files is
    acceptable for what you're measuring, and always check
    `failed_files.log` afterwards.
