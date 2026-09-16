# Module 3 - Local TaskVine factory

**20 min**

This is the same analysis over the same data; however, now a real TaskVine
*manager* places every call on a real TaskVine *worker*. Both still run on
this machine, and Module 4 then moves the worker to the HTCondor pool.

## Make the change

Start from Module 2's script:

```bash
cp scripts/vr_trijet_iterative.py scripts/vr_trijet_taskvine.py
```

Open `scripts/vr_trijet_taskvine.py` and make three edits.

**1. Imports**: swap the distributor, and import TaskVine itself:

```diff
+import ndcctools.taskvine as vine
 import numpy as np

 from vine_reduce import serialization
 from vine_reduce.coffea import VineReduceCoffea
-from vine_reduce.local_distributor import LocalDistributor
+from vine_reduce.taskvine_distributor import TaskVineDistributor
```

**2. The distributor**: a TaskVine manager listening on a free port:

```diff
-    distributor = LocalDistributor(max_workers=2)
+    distributor = TaskVineDistributor(
+        port=0,
+        resources_processor={"cores": 1},
+        resources_reducer={"cores": 1},
+    )
+    print(f"TaskVine manager listening on port {distributor.port}")
```

**3. A worker**, since a manager with no workers never runs anything.
`vine.Factory` starts and stops
`vine_worker` processes for you; in this case, one local worker with 2 cores:

```diff
-    with distributor:
+    workers = vine.Factory(manager_host_port=f"localhost:{distributor.port}")
+    workers.ssl = True
+    workers.cores = 2
+    workers.min_workers = 1
+    workers.max_workers = 1
+    workers.extra_options = "--single-shot"
+
+    with distributor, workers:
         vr.compute()
```

`trijet_processor`, `load_result`, the dataset, and the whole
`VineReduceCoffea(...)` call are untouched.

`extra_options` is passed straight to `vine_worker`. In particular,
`--single-shot` makes the worker exit the moment it disconnects from its
manager, rather than hanging around looking for more work. It barely matters
for one local worker; on a shared pool, however, it is how you avoid leaving
idle workers holding other people's slots, and
[Module 4](module-04-scale-out.md) makes that a habit.

!!! tip "Fell behind?"
    Grab the finished version:

    ```bash
    curl -sL -o scripts/vr_trijet_taskvine.py \
      https://raw.githubusercontent.com/cooperative-computing-lab/vine-cms-analysis-stack-tutorials/main/scripts/vr_trijet_taskvine.py
    ```

## Run it

=== "Option A: conda"

    ```bash
    conda activate vine-cms-analysis-stack
    python scripts/vr_trijet_taskvine.py
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/vr_trijet_taskvine.py
    ```

The first line tells you where the manager is listening (your port will
differ):

```
TaskVine manager listening on port 33217
```

This run takes about 3 minutes, which is much longer than Module 2's 15
seconds. Every call is now a TaskVine task: the manager sends it to the
worker, the worker runs it in its own sandbox, and the result is sent back.
Given only 104 small chunks, such per-task overhead dominates. Such a price
is likely worth paying once the worker is a different machine; for now,
perhaps use the time to watch it.

## Watch it: two views

### (a) `vine_reduce`'s console

These are the same bars as in Module 2, with the same answer at the end:

<div class="term">
<span class="t-green">success             </span> processor trijet/ttbar_like ...bar_like/file_0.root[25000:50000] (id=4bb5dd77) cores=1(1) memory_mb=360(31763) wall_time_s=1(0)
<span class="t-green">success             </span> processor trijet/ttbar_like ...bar_like/file_0.root[0:25000] (id=9d4224e9) cores=1(1) memory_mb=357(31763) wall_time_s=1(0)
...
<span class="t-green">success             </span> reducer   trijet/ttbar_like reduction of 10 partials (id=b3d47d04) cores=1(1) memory_mb=281(31763) wall_time_s=1(0)
<span class="t-green">success             </span> final     trijet/ttbar_like reduction of 5 partials (final) (id=21534643) cores=1(1) memory_mb=281(31763) wall_time_s=1(0)
trijet     [ <span class="t-green">██████████████████████████████</span> ]                  <span class="t-yellow">104</span>/<span class="t-red">0</span>/<span class="t-blue">104</span>
reductions [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">12</span>/<span class="t-red">0</span>/<span class="t-blue">12</span>
events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">2523470</span>(<span class="t-green">2523470</span>)/<span class="t-red">0</span>/<span class="t-blue">2523470</span>
datasets   [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">1</span>/<span class="t-cyan">1</span>
trijet pT histogram: 2367108 entries
max b-tag histogram: 2367108 entries
</div>

One thing is new: `memory_mb=360(31763)` now has an allocation in
parentheses. TaskVine gives every task an allocation, and given that you only
declared `cores`, it gave the task a share of the worker's memory proportional
to its cores. For example, 1 of the worker's 2 cores means half the machine's
memory. Thus, the task *used* 360 MB of the 31,763 MB it was *allowed*, which
is a bit generous. Such a gap is what [Module 5](module-05-resources.md)
tunes.

### (b) `vine_status`, while it runs

Open a **second terminal**, `cd ~/vine-cms-analysis-stack`, and ask the
manager directly, using your port:

=== "Option A: conda"

    ```bash
    conda activate vine-cms-analysis-stack
    vine_status --ssl localhost 33217
    ```

=== "Option B: pixi"

    ```bash
    pixi run vine_status --ssl localhost 33217
    ```

```
PROJECT            HOST                   PORT WAITING RUNNING COMPLETE WORKERS
???                ???                   33217      94       2        8       1
```

This shows 94 tasks waiting, 2 running (the worker's 2 cores), 8 done, and 1
worker. `--ssl` is needed because the manager encrypts its connections, which
is `TaskVineDistributor`'s default. `PROJECT` is `???` because this manager
has no name yet; Module 4 gives it one, and then the catalog can find it
without a host and port.

There are two more views of the same manager:

=== "Option A: conda"

    ```bash
    vine_status --ssl -W localhost 33217   # workers: cores/memory/disk used vs. available
    vine_status --ssl -T localhost 33217   # tasks: state, and resources each one asked for
    ```

=== "Option B: pixi"

    ```bash
    pixi run vine_status --ssl -W localhost 33217   # workers: cores/memory/disk used vs. available
    pixi run vine_status --ssl -T localhost 33217   # tasks: state, and resources each one asked for
    ```

```
HOST       ADDRESS         COMPLETED RUNNING CORE_U CORE_A MEM_U MEM_A DISK_U DISK_A GPUS_U GPUS_A
disc-head- ???                     8 2       2      2      63526 63526 140997 188000 0      0
```

(The `HOST` column shows the machine these pages were captured on; yours
will show your own login node instead, with its own core/memory/disk
numbers.)

Rerun any of them while the run goes, and watch `WAITING` drain into
`COMPLETE`.

## After it finishes: the logs

Every manager writes its logs under `vine-run-info/`, with one timestamped
directory per run, and `most-recent` pointing at the latest:

```bash
ls vine-run-info/most-recent/vine-logs/
```

```
debug  performance  taskgraph  transactions  workflow.json
```

In particular, `debug` has everything the manager did, in order, and it is
the first stop when something goes wrong. `transactions` has one line per
task/worker state change, `performance` has periodic snapshots of queue and
worker counts, and `taskgraph` records which task produced which file, and
which task consumed it.

Raw logs are a bit hard to read; therefore, turn two of them into plots:

=== "Option A: conda"

    ```bash
    mkdir -p plots
    vine_plot_performance -u s -s 5 -o plots/perf vine-run-info/most-recent/vine-logs/performance
    vine_plot_taskgraph --output plots/taskgraph.pdf vine-run-info/most-recent/vine-logs/taskgraph
    ls plots/
    ```

=== "Option B: pixi"

    ```bash
    mkdir -p plots
    pixi run vine_plot_performance -u s -s 5 -o plots/perf vine-run-info/most-recent/vine-logs/performance
    pixi run vine_plot_taskgraph --output plots/taskgraph.pdf vine-run-info/most-recent/vine-logs/taskgraph
    ls plots/
    ```

```
perf.tasks-accum.svg       perf.tasks.svg         perf.time-workers.svg  perf.workers-accum.svg  perf.workers.svg
perf.tasks-capacities.svg  perf.time-manager.svg  perf.times-stacked.svg perf.transfer.svg       taskgraph.pdf
```

(`vine_plot_taskgraph` also leaves a `taskgraph.dot` in the current directory,
which is the graphviz source for the PDF.) `-u s` puts time in seconds, and
`-s 5` samples the log every 5 seconds rather than the default 30, because
this run was short.

These are image files on glados. Copy them to your laptop by running this **on
your laptop**, not on glados:

```bash
scp '<netid>@glados.crc.nd.edu:vine-cms-analysis-stack/plots/*' .
```

Open `perf.tasks-accum.svg` in a browser, which shows tasks submitted
vs. completed over time for all 116 of them (104 processor calls plus 12
reductions). Then open `taskgraph.pdf`, which shows processor tasks feeding
reductions, and reductions feeding the final one. This is a reduction tree
that `vine_reduce` built as results arrived, as opposed to one planned up
front.

## Distributor vs. executor, now for real

Given that there is a real manager and a real worker now, the split from
Module 0 is something you can actually point at.

The **distributor**, `TaskVineDistributor` (i.e., the TaskVine manager inside
your script), decided *where and when* each call ran: it queued 104 tasks,
sent them to the worker as cores freed up, and fetched the results. The
**executor**, in this case a plain in-process call inside each task's sandbox
on the worker, ran `trijet_processor(events)` once the task arrived.

Swapping `LocalDistributor` for `TaskVineDistributor` changed only the first.
Module 4 changes where the worker lives; the executor, and your processor,
stay put.
