# Module 6 - Checkpoints & restart

**20 min**

A long run will likely get interrupted at some point: you log out, the
login node reboots, or you hit Ctrl-C by accident. This module shows what VineReduce keeps on disk while it runs, and
how rerunning the same command picks up from there rather than starting
over.

This module goes back to the synthetic data, on the login node, so no pool
is needed.

## Get the script

```bash
curl -sL -o scripts/vr_trijet_checkpoint.py \
  https://raw.githubusercontent.com/cooperative-computing-lab/vine-cms-analysis-stack-tutorials/main/scripts/vr_trijet_checkpoint.py
```

This is Module 3's `vr_trijet_taskvine.py` with three changes:

**1. `checkpoint_time=10`** in the `VineReduceCoffea(...)` call.

**2. No `shutil.rmtree`** of `results/` and `checkpoints/` at the start.
Modules 2 and 3 wiped both on every run; keeping them, however, is exactly
what lets a rerun resume. For a genuinely fresh run, delete them yourself
with `rm -rf results checkpoints`.

**3. One worker with one core** (`workers.cores = 1`), so that the run is
slow enough to interrupt partway.

## When a checkpoint is taken

Reductions fold partial results together, and most of them are
intermediate, in the sense that they are not the final answer yet.
Normally an intermediate result exists only on the worker that produced
it, or in TaskVine's temporary storage, and thus if the run dies, it is
gone.

A **checkpoint** is an intermediate result that is also copied back to
`checkpoints/` and recorded in `results/vine_reduce.db`, so that it
survives.

With `checkpoint_time=10`, when VineReduce is about to submit a reduction,
it adds up the wall time of all the processor and reducer work in that
group since its last checkpoint. If that total is at least 10 seconds, the
result of this reduction is checkpointed.

This is **not** a timer that fires every 10 seconds of runtime. For
example, here each processor call takes about a second, so a reduction of
10 partial results carries roughly 10 seconds of work, and therefore it
gets checkpointed. In other words, the checkpoint is tied to how much work
would be lost, rather than to the clock.

## Run it, and interrupt it

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

Let it run until you have seen at least one line starting with
`checkpoint` — a minute or two, depending on your login node:

<div class="term">
<span class="t-green">success             </span> checkpoint trijet/ttbar_like reduction of 10 partials ...
</div>

Then press **Ctrl-C**. The run below was interrupted after 90
seconds; how far yours gets in that time will differ:

<div class="term">
trijet     [ <span class="t-green">████████████████</span><span class="t-gray">░░░░░░░░░░░░░░</span> ]             <span class="t-yellow">54</span>/<span class="t-red">0</span>/<span class="t-blue">104</span>
reductions [ <span class="t-green">██████████████</span><span class="t-gray">░░░░░░░░░░░░░░░░</span> ]               <span class="t-yellow">5</span>/<span class="t-red">0</span>/<span class="t-blue">11</span>
events     [ <span class="t-green">███████████████</span><span class="t-gray">░░░░░░░░░░░░░░░</span> ] <span class="t-yellow">1301861</span>(<span class="t-green">0</span>)/<span class="t-red">0</span>/<span class="t-blue">2523470</span>
datasets   [ <span class="t-gray">░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░</span> ]                  <span class="t-green">0</span>/<span class="t-cyan">1</span>
Traceback (most recent call last):
...
KeyboardInterrupt
</div>

At that point 54 of 104 chunks were done, with 1,301,861 events processed.
The number in parentheses on the events bar, `(0)`, counts events whose
results are in a **final** result, and since there is no final result yet,
it stays at zero.

## What survived

```bash
ls results checkpoints
```

```
checkpoints:
f631b265aa4e4bd3b1400da8e5f5a2c0.p

results:
ttbar_like  vine_reduce.db
```

There is one checkpoint file. Further, `results/vine_reduce.db` is a small
SQLite database recording what each checkpoint covers:

=== "Option A: conda"

    ```bash
    python -c "import sqlite3; print(*sqlite3.connect('results/vine_reduce.db').execute('select processor, dataset, num_events, is_final from checkpoints'), sep='\n')"
    ```

=== "Option B: pixi"

    ```bash
    pixi run python -c "import sqlite3; print(*sqlite3.connect('results/vine_reduce.db').execute('select processor, dataset, num_events, is_final from checkpoints'), sep='\n')"
    ```

```
('trijet', 'ttbar_like', 678973, 0)
```

This is one intermediate (`is_final` = 0) checkpoint for `trijet` over
`ttbar_like`, covering 678,973 events, which is 3 complete files' worth.
The other processed events, about 620,000, lived only in intermediate
results that were never checkpointed, and thus they are lost.

## Rerun the identical command

=== "Option A: conda"

    ```bash
    python scripts/vr_trijet_checkpoint.py
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/vr_trijet_checkpoint.py
    ```

Note that there is no `rm -rf` this time. On startup, VineReduce reads
`results/vine_reduce.db` and uses each row according to its kind. A
**final** row would be taken as that pipeline's answer, with nothing
rerun. An **intermediate** row, like ours, goes straight back into the
pool of partial results, ready to be folded into the next reduction. In
both cases, the files a checkpoint covers are skipped when chunks are cut.

<div class="term">
<span class="t-green">success             </span> checkpoint trijet/ttbar_like reduction of 10 partials ...
<span class="t-green">success             </span> checkpoint trijet/ttbar_like reduction of 10 partials ...
...
trijet     [ <span class="t-green">██████████████████████</span><span class="t-gray">░░░░░░░░</span> ]                   <span class="t-yellow">76</span>/<span class="t-red">0</span>/<span class="t-blue">104</span>
reductions [ <span class="t-green">███████████████████████</span><span class="t-gray">░░░░░░░</span> ]                     <span class="t-yellow">9</span>/<span class="t-red">0</span>/<span class="t-blue">12</span>
events     [ <span class="t-green">██████████████████████</span><span class="t-gray">░░░░░░░░</span> ] <span class="t-yellow">1844497</span>(<span class="t-green">2523470</span>)/<span class="t-red">0</span>/<span class="t-blue">2523470</span>
datasets   [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">1</span>/<span class="t-cyan">1</span>
trijet pT histogram: 2367108 entries
max b-tag histogram: 2367108 entries
</div>

The bars never fill all the way, and that is precisely the point. Only
**76 of 104** chunks ran this time, since the other 28 are the 3 files the
checkpoint already covered. Further, this run processed **1,844,497**
events itself, but `(2523470)` are in the final result, because the
checkpoint's 678,973 were folded in rather than redone. The histograms
have **2,367,108** entries, exactly as in Modules 2 and 3. Such partially
filled bars are thus a sign that the restart worked, as opposed to a sign
that something was skipped by mistake.

Look again:

```bash
ls results checkpoints results/ttbar_like/trijet
```

```
checkpoints:

results:
size.jsonl  ttbar_like  vine_reduce.db

results/ttbar_like/trijet:
trijet__946d1b1ea3644456ad237d833fa950ef.pkl.zst
```

```
('trijet', 'ttbar_like', 2523470, 1)
```

The second block comes from the same `sqlite3` one-liner as before.
`checkpoints/` is now empty, because once the final result exists, the
intermediate checkpoints it replaced are deleted. The database now has one
**final** row covering all 2,523,470 events. `results/size.jsonl` is new
too: VineReduce appends one line per **finished** pipeline, recording its
result size and peak resource use, which is why it wasn't there after the
interrupted run.

!!! warning "Don't rerun a finished run without `rm -rf results checkpoints`"
    With vine-reduce 2026.9.8, rerunning after the run has completed
    doesn't exit. The final row is picked up (`datasets 1/1`, events
    `0(2523470)`); however, the script then sits waiting indefinitely.
    Clear `results/` and `checkpoints/` before starting over.

!!! question "Try it"
    - Interrupt the rerun too, and then run it again. Each resume picks up
      from the latest checkpoints.
    - Change `checkpoint_time=10` to `checkpoint_time=60`, `rm -rf results
      checkpoints`, and interrupt at the same point. Fewer (or no)
      checkpoints means more work redone.
