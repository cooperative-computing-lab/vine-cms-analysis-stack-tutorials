# Module 6 - Checkpoints & restart

**20 min**

A long run will likely get interrupted at some point: you log out, the
login node reboots, or you hit Ctrl-C by accident. This module shows what VineReduce keeps on disk while it runs, and
how rerunning the same command picks up from there rather than starting
over.

This module runs on the login node, reading from `/project01`, so no pool
is needed.

## What changed in the script

This module's script (`scripts/vr_trijet_checkpoint.py`,
or `scripts/vr_trijet_checkpoint_rdf.py`) is Module 3's
(`vr_trijet_taskvine.py`, or `vr_trijet_taskvine_rdf.py`), with four changes,
shown below as diffs. The processor, `load_result`, and the manager (name
included) are untouched.

**1. `checkpoint_time=2` and `reduction_size=2`**, in the
`VineReduceCoffea(...)` call (`VineReduce(...)`, for RDataFrame):

```diff
         checkpoint_dir=checkpoint_dir,
         chunksize=...,
+        reduction_size=2,
+        checkpoint_time=2,
     )
```

**2. No `shutil.rmtree`** of `results/` and `checkpoints/` at the start.
Modules 2 and 3 wiped both on every run; keeping them, however, is exactly
what lets a rerun resume. For a genuinely fresh run, delete them yourself
with `rm -rf results checkpoints`:

```diff
-import shutil
 ...
-    shutil.rmtree(results_dir, ignore_errors=True)
-    shutil.rmtree(checkpoint_dir, ignore_errors=True)
```

**3. One worker with one core**, so that the run is slow enough to
interrupt partway:

```diff
-    workers.cores = 2
+    workers.cores = 1
```

**4. `chunksize=None`**: every file is one chunk (to make reasoning easier).

```diff
-        chunksize=50_000,
+        chunksize=None,
```

## When a checkpoint is taken

Reductions fold partial results together, and most of them are
intermediate, in the sense that they are not the final answer yet.
Normally an intermediate result exists only on the worker that produced
it, or in TaskVine's temporary storage, and thus if the run dies, it is
gone.

A **checkpoint** is an intermediate result that is also copied back to
`checkpoints/` and recorded in `results/vine_reduce.db`, so that it
survives.

With `checkpoint_time=2`, when VineReduce is about to submit a reduction,
it adds up the wall time of all the processor and reducer work in that
group since its last checkpoint. If that total is at least 2 seconds, the
result of this reduction is checkpointed. (`reduction_size=2` makes every
reduction fold just two files' results, so that the first checkpoint comes
early.)

=== "coffea"

    This is **not** a timer that fires every 2 seconds of runtime. For
    example, here each processor call (one file) takes 1 or 2 seconds, so a
    reduction of 2 partial results carries 2 to 4 seconds of work, and
    therefore it gets checkpointed. In other words, the checkpoint is tied to
    how much work would be lost, rather than to the clock.

=== "RDataFrame"

    This is **not** a timer that fires every 2 seconds of runtime. For
    example, here each processor call (one file) takes from 5 to 14 seconds
    (ROOT compiles `BestTrijet` in every task, and then reads the file), so a
    reduction of 2 partial results carries 10 seconds or more of work, and
    therefore it gets checkpointed. In other words, the checkpoint is tied to
    how much work would be lost, rather than to the clock.

## Run it, and interrupt it

=== "coffea"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        rm -rf results checkpoints
        python scripts/vr_trijet_checkpoint.py
        ```

    === "Option B: pixi"

        ```bash
        rm -rf results checkpoints
        pixi run python scripts/vr_trijet_checkpoint.py
        ```

=== "RDataFrame"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        rm -rf results checkpoints
        python scripts/vr_trijet_checkpoint_rdf.py
        ```

    === "Option B: pixi"

        ```bash
        rm -rf results checkpoints
        pixi run python scripts/vr_trijet_checkpoint_rdf.py
        ```

Let it run until you have seen a line starting with `checkpoint`, which
comes after about 20 seconds with coffea, or about 30 seconds with
RDataFrame:

<div class="term">
<span class="t-green">success             </span> checkpoint trijet/SingleMu_Run2012B_194271-194789 reduction of 2 partials ...
</div>

Then press **Ctrl-C** straight away. A checkpoint is only a survivor while
its dataset is still running: once a dataset finishes, its checkpoints are
replaced by its final result. Coffea runs through a dataset in a few seconds,
so you have little time; if you miss it, delete `results` and `checkpoints` and
start again. The interrupted runs below looked like this (how far yours gets
will differ):

=== "coffea"

    <div class="term">
    trijet     [ <span class="t-green">██████████████</span><span class="t-gray">░░░░░░░░░░░░░░░░</span> ]                    <span class="t-yellow">7</span>/<span class="t-red">0</span>/<span class="t-blue">15</span>
    reductions [ <span class="t-green">█████</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                    <span class="t-yellow">2</span>/<span class="t-red">0</span>/<span class="t-blue">11</span>
    events     [ <span class="t-green">██████████████████</span><span class="t-gray">░░░░░░░░░░░░</span> ] <span class="t-yellow">2204733</span>(<span class="t-green">671082</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets   [ <span class="t-green">██████</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                       <span class="t-green">1</span>/<span class="t-cyan">5</span>
    Traceback (most recent call last):
    ...
    KeyboardInterrupt
    </div>

    At that point 7 of 15 files were done, with 2,204,733 events processed, and
    the first dataset had already finished. The number in parentheses on the
    events bar, `(671082)`, counts the events that are *safe*, that is, durably
    recorded: here, the first dataset's final result. The second dataset's
    checkpoint, recorded moments before the run was stopped, was not counted
    yet.

=== "RDataFrame"

    <div class="term">
    trijet     [ <span class="t-green">██████</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                    <span class="t-yellow">3</span>/<span class="t-red">0</span>/<span class="t-blue">15</span>
    reductions [ <span class="t-green">██</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                    <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">14</span>
    events     [ <span class="t-green">█████</span><span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░</span> ] <span class="t-yellow">671082</span>(<span class="t-green">0</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets   [ <span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                       <span class="t-green">0</span>/<span class="t-cyan">5</span>
    Traceback (most recent call last):
    ...
    KeyboardInterrupt
    </div>

    At that point 3 of 15 files were done, with 671,082 events processed. The
    number in parentheses on the events bar, `(0)`, counts the events that are
    *safe*, that is, durably recorded. It still reads zero here, because the
    checkpoint (below) was recorded moments before the run was stopped and was
    not counted yet.

## What survived

```bash
ls results checkpoints
```

=== "coffea"

    ```
    checkpoints:
    13fa9c70e76c414db0742c15e4d87896.p
    7510956ae1ef4a97b6581becda314508.p

    results:
    SingleMu_Run2012B_193834-194270
    SingleMu_Run2012B_194271-194789
    SingleMu_Run2012B_194790-195398
    SingleMu_Run2012B_195399-195841
    SingleMu_Run2012B_195842-196531
    size.jsonl
    vine_reduce.db
    ```

    There are two checkpoint files. Further, `results/vine_reduce.db` is a
    small SQLite database recording what each checkpoint and each final result
    covers; only one of the two files is referenced by an intermediate row (the
    other is a stale leftover):

=== "RDataFrame"

    ```
    checkpoints:
    ed3e483cf8844e9ea9f9b44e19dbc89e.p

    results:
    SingleMu_Run2012B_193834-194270
    SingleMu_Run2012B_194271-194789
    SingleMu_Run2012B_194790-195398
    SingleMu_Run2012B_195399-195841
    SingleMu_Run2012B_195842-196531
    vine_reduce.db
    ```

    There is one checkpoint file. Further, `results/vine_reduce.db` is a small
    SQLite database recording what each checkpoint covers:

Look inside the database:

=== "Option A: conda"

    ```bash
    python -c "import sqlite3; print(*sqlite3.connect('results/vine_reduce.db').execute('select processor, dataset, num_events, is_final from checkpoints'), sep='\n')"
    ```

=== "Option B: pixi"

    ```bash
    pixi run python -c "import sqlite3; print(*sqlite3.connect('results/vine_reduce.db').execute('select processor, dataset, num_events, is_final from checkpoints'), sep='\n')"
    ```

It lists:

=== "coffea"

    ```
    ('trijet', 'SingleMu_Run2012B_193834-194270', 671082, 1)
    ('trijet', 'SingleMu_Run2012B_194271-194789', 719979, 0)
    ```

    The first row is a **final** result (`is_final` = 1): the whole first
    dataset. The second is an intermediate (`is_final` = 0) checkpoint for the
    second dataset, covering 719,979 events, which is its first two files
    (389,239 + 330,740). The third file of that dataset, and the first file of the
    third dataset, had been processed, but only lived in intermediate results
    that were never checkpointed, and thus they are lost.

=== "RDataFrame"

    ```
    ('trijet', 'SingleMu_Run2012B_193834-194270', 275910, 0)
    ```

    This is one intermediate (`is_final` = 0) checkpoint for the first dataset,
    covering 275,910 events, which is its first two files (53,733 + 222,177).
    The third file's 395,172 events had been processed, but only lived in an
    intermediate result that was never checkpointed, and thus they are lost.

## Rerun the identical command

=== "coffea"

    === "Option A: conda"

        ```bash
        python scripts/vr_trijet_checkpoint.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_checkpoint.py
        ```

=== "RDataFrame"

    === "Option A: conda"

        ```bash
        python scripts/vr_trijet_checkpoint_rdf.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_checkpoint_rdf.py
        ```

Note that there is no `rm -rf` this time. On startup, VineReduce reads
`results/vine_reduce.db` and uses each row according to its kind. A
**final** row is taken as that pipeline's answer, with nothing
rerun. An **intermediate** row, like ours, goes straight back into the
pool of partial results, ready to be folded into the next reduction. In
both cases, the events a checkpoint covers are not cut into chunks again;
with one chunk per file, as here, that means whole files are skipped.

=== "coffea"

    <div class="term">
    trijet     [ <span class="t-green">███████████████████</span><span class="t-gray">░░░░░░░░░░░</span> ]                    <span class="t-yellow">10</span>/<span class="t-red">0</span>/<span class="t-blue">16</span>
    reductions [ <span class="t-green">██████████████████</span><span class="t-gray">░░░░░░░░░░░░</span> ]                     <span class="t-yellow">7</span>/<span class="t-red">0</span>/<span class="t-blue">12</span>
    events     [ <span class="t-green">███████████████████</span><span class="t-gray">░░░░░░░░░░░</span> ] <span class="t-yellow">2345355</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>
    SingleMu_Run2012B_193834-194270: 289270 entries (trijet pT), 289270 entries (max b-tag)
    SingleMu_Run2012B_194271-194789: 497298 entries (trijet pT), 497298 entries (max b-tag)
    SingleMu_Run2012B_194790-195398: 276498 entries (trijet pT), 276498 entries (max b-tag)
    SingleMu_Run2012B_195399-195841: 247576 entries (trijet pT), 247576 entries (max b-tag)
    SingleMu_Run2012B_195842-196531: 387297 entries (trijet pT), 387297 entries (max b-tag)
    trijet pT histogram, all datasets: 1697939 entries
    max b-tag histogram, all datasets: 1697939 entries
    </div>

    Only **10 of 15** files ran this time: the other 5 are the three files of
    the first dataset, which was already final, and the two files that the
    checkpoint of the second dataset covers. This run processed **2,345,355**
    events itself, but `(3736416)` are in the final results, because the earlier
    work was folded in rather than redone. The histograms have **1,697,939**
    entries, exactly as in Module 2. Such partially filled bars are thus a sign
    that the restart worked, as opposed to a sign that something was skipped by
    mistake.

=== "RDataFrame"

    <div class="term">
    trijet     [ <span class="t-green">██████████████████████████</span><span class="t-gray">░░░░</span> ]                    <span class="t-yellow">13</span>/<span class="t-red">0</span>/<span class="t-blue">15</span>
    reductions [ <span class="t-green">███████████████████████████</span><span class="t-gray">░░░</span> ]                     <span class="t-yellow">9</span>/<span class="t-red">0</span>/<span class="t-blue">10</span>
    events     [ <span class="t-green">████████████████████████████</span><span class="t-gray">░░</span> ] <span class="t-yellow">3460506</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>
    SingleMu_Run2012B_193834-194270: 289270 entries (trijet pT), 289270 entries (max b-tag)
    SingleMu_Run2012B_194271-194789: 497298 entries (trijet pT), 497298 entries (max b-tag)
    SingleMu_Run2012B_194790-195398: 276498 entries (trijet pT), 276498 entries (max b-tag)
    SingleMu_Run2012B_195399-195841: 247576 entries (trijet pT), 247576 entries (max b-tag)
    SingleMu_Run2012B_195842-196531: 387297 entries (trijet pT), 387297 entries (max b-tag)
    trijet pT histogram, all datasets: 1697939 entries
    max b-tag histogram, all datasets: 1697939 entries
    </div>

    Only **13 of 15** files ran this time: the other 2 are the ones that the
    checkpoint already covers. This run processed **3,460,506** events itself,
    but `(3736416)` are in the final results, because the checkpoint's 275,910
    were folded in rather than redone. The histograms have **1,697,939**
    entries, exactly as in Module 2. Such partially filled bars are thus a sign
    that the restart worked, as opposed to a sign that something was skipped by
    mistake.

Look again:

```bash
ls results checkpoints results/SingleMu_Run2012B_193834-194270/trijet
```

=== "coffea"

    ```
    checkpoints:
    13fa9c70e76c414db0742c15e4d87896.p

    results:
    SingleMu_Run2012B_193834-194270
    SingleMu_Run2012B_194271-194789
    SingleMu_Run2012B_194790-195398
    SingleMu_Run2012B_195399-195841
    SingleMu_Run2012B_195842-196531
    size.jsonl
    vine_reduce.db

    results/SingleMu_Run2012B_193834-194270/trijet:
    trijet__f10de99a8f7944c0b3a21cce18a48910.pkl.zst
    ```

    The stale checkpoint file from before is still in `checkpoints/`; it does
    not affect the result.

=== "RDataFrame"

    ```
    checkpoints:

    results:
    SingleMu_Run2012B_193834-194270
    SingleMu_Run2012B_194271-194789
    SingleMu_Run2012B_194790-195398
    SingleMu_Run2012B_195399-195841
    SingleMu_Run2012B_195842-196531
    size.jsonl
    vine_reduce.db

    results/SingleMu_Run2012B_193834-194270/trijet:
    trijet__7c2584566a10430c99764d73d669431a.pkl.zst
    ```

    `checkpoints/` is now empty, because once the final result exists, the
    intermediate checkpoints it replaced are deleted.

```
('trijet', 'SingleMu_Run2012B_193834-194270', 671082, 1)
('trijet', 'SingleMu_Run2012B_194271-194789', 1102938, 1)
('trijet', 'SingleMu_Run2012B_194790-195398', 591546, 1)
('trijet', 'SingleMu_Run2012B_195399-195841', 549171, 1)
('trijet', 'SingleMu_Run2012B_195842-196531', 821679, 1)
```

The second block comes from the same `sqlite3` one-liner as before. The
database now has one **final** row per dataset, each covering all of its
events (compare them with the table in [Module 1](module-01-setup.md)).
`results/size.jsonl` is new too: VineReduce appends one line per **finished**
pipeline, recording its result size and peak resource use, which is why it
wasn't there after the interrupted run.

!!! warning "Don't rerun a finished run without `rm -rf results checkpoints`"
    Rerunning after the run has completed doesn't exit. The final rows are
    picked up; however, the script then sits waiting indefinitely. Clear
    `results/` and `checkpoints/` before starting over.

!!! question "Try it"
    - Interrupt the rerun too, and then run it again. Each resume picks up
      from the latest checkpoints.
    - Start over with `rm -rf results checkpoints` and interrupt at the
      same point, then compare how much work the resume has to redo. The
      script's `checkpoint_time=2` is what makes the checkpoints come so
      early; a much larger value (say, 60) would mean fewer or no
      checkpoints, and therefore more work redone.

*The output on this page was captured with a local worker reading a local copy of the files with the same directory layout, rather than from `/project01` itself.*
