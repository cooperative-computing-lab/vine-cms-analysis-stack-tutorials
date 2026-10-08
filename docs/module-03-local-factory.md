# Module 3 - Local TaskVine factory

**20 min**

This is the same analysis over the same data; however, now a real TaskVine
*manager* places every call on a real TaskVine *worker*. Both still run on
this machine, and Module 4 then moves the worker to the HTCondor pool.

## What changed in the script

You do not edit anything. This module's script
(`scripts/vr_trijet_taskvine.py`, or `scripts/vr_trijet_taskvine_rdf.py` for
RDataFrame) is Module 2's, with three changes, shown below as diffs against
`vr_trijet_iterative.py` (or `vr_trijet_iterative_rdf.py`). Open the new script
and find them.

**1. Imports**: swaps the distributor, and imports TaskVine itself, along
with `getpass` (explained under edit 2):

=== "coffea"

    ```diff
    +import getpass
     import glob
     ...
    +import ndcctools.taskvine as vine
     import numpy as np

     from vine_reduce import serialization
     from vine_reduce.coffea import VineReduceCoffea
    -from vine_reduce.local_distributor import LocalDistributor
    +from vine_reduce.taskvine_distributor import TaskVineDistributor
    ```

=== "RDataFrame"

    ```diff
    +import getpass
     import glob
     ...
     import hist
    +import ndcctools.taskvine as vine

     from vine_reduce import serialization
     from vine_reduce.coffea import coffea_input_to_datasets, coffea_reducer
     from vine_reduce.engine import VineReduce
    -from vine_reduce.local_distributor import LocalDistributor
    +from vine_reduce.taskvine_distributor import TaskVineDistributor
    ```

**2. The distributor**: a TaskVine manager listening on a free port, with a
name:

```diff
+MANAGER_NAME = f"{getpass.getuser()}-trijet-tutorial"
+
 ...
-    distributor = LocalDistributor(max_workers=2)
+    distributor = TaskVineDistributor(
+        name=MANAGER_NAME,
+        port=0,
+        resources_processor={"cores": 1},
+        resources_reducer={"cores": 1},
+    )
+    print(f"TaskVine manager {MANAGER_NAME!r} listening on port {distributor.port}")
```

`getpass.getuser()` returns your username, so the manager is named
`<your netid>-trijet-tutorial`. Nothing in this module needs the name (the
worker below is pointed straight at the manager's port); we will explain
what it is for in the next module.

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
`VineReduceCoffea(...)` call (`VineReduce(...)`, for RDataFrame) are
untouched.

`extra_options` is passed straight to `vine_worker`. In particular,
`--single-shot` makes the worker exit the moment it disconnects from its
manager, rather than hanging around looking for more work from other managers.

## Run it as before

=== "coffea"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_taskvine.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_taskvine.py
        ```

=== "RDataFrame"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_taskvine_rdf.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_taskvine_rdf.py
        ```

The first line tells you the manager's name and where it is listening (your
name and port will differ):

```
TaskVine manager 'btovar-trijet-tutorial' listening on port 41841
```

=== "coffea"

    This run takes about 1 minute 20 seconds, which is longer than
    Module 2's 15 seconds. Every call is now a TaskVine task: the manager sends it to the
    worker, the worker runs it in its own sandbox, and the result is sent
    back. Given only 83 small chunks, such per-task overhead dominates.

=== "RDataFrame"

    This run takes about 4 minutes, which is much longer than Module 2's 50
    seconds. Every call is now a TaskVine task: the manager sends it to the
    worker, the worker runs it in its own sandbox, and the result is sent
    back. Given only 83 small chunks, such per-task overhead dominates, and
    with RDataFrame it is a bit higher still: each task is a new process
    that has to compile the C++ in `BestTrijet` again, which is the 5
    seconds you will see on every processor line below. (In Module 2, a
    worker process compiled it once and then reused it for every later
    chunk.)



## `vine_reduce`'s console

These are the same bars as in Module 2, with the same answer at the end:

=== "coffea"

    <div class="term">
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_0.root[50000:53733] (id=a61df1be) cores=1(1) memory_mb=217(31763) wall_time_s=1(0)
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_0.root[0:50000] (id=66709993) cores=1(1) memory_mb=248(31763) wall_time_s=1(0)
    ...
    <span class="t-green">success             </span> reducer   trijet/SingleMu_Run2012B_195842-196531 reduction of 10 partials (id=394b1484) cores=1(1) memory_mb=203(31763) wall_time_s=1(0)
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=2b4a4893) cores=1(1) memory_mb=202(31763) wall_time_s=1(0)
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

    <div class="term">
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_0.root[50000:53733] (id=eaf26c12) cores=1(1) memory_mb=867(31763) wall_time_s=4(0)
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_0.root[0:50000] (id=d87c5283) cores=1(1) memory_mb=867(31763) wall_time_s=4(0)
    ...
    <span class="t-green">success             </span> reducer   trijet/SingleMu_Run2012B_195842-196531 reduction of 10 partials (id=10d93635) cores=1(1) memory_mb=201(31763) wall_time_s=1(0)
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=f5a99206) cores=1(1) memory_mb=201(31763) wall_time_s=1(0)
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

One thing is new: the `memory_mb` figure now has an allocation in
parentheses. TaskVine gives every task an allocation, and given that you only
declared `cores`, it gave the task a share of the worker's memory proportional
to its cores. For example, 1 of the worker's 2 cores means half the machine's
memory.

=== "coffea"

    Thus, the task *used* 248 MB of the 31,763 MB it was *allowed* (read from
    `memory_mb=248(31763)`), which is a bit generous.

=== "RDataFrame"

    Thus, the task *used* 867 MB of the 31,763 MB it was *allowed* (read from
    `memory_mb=867(31763)`), which is a bit generous. About 750 MB of that
    is ROOT starting up and compiling `BestTrijet`, before a single event is
    read.

Such a gap is what [Module 5](module-05-resources.md) tunes.

### `vine_status`, while it runs

Open a **second terminal**, `cd ~/vine-cms-analysis-stack/examples/tutorial_nd`, and ask the
manager directly, using your port:

=== "Option A: conda"

    ```bash
    conda activate vine-cms-analysis-stack
    vine_status --ssl localhost 41841
    ```

=== "Option B: pixi"

    ```bash
    pixi run vine_status --ssl localhost 41841
    ```

```
PROJECT                  HOST                   PORT WAITING RUNNING COMPLETE WORKERS
btovar-trijet-tutorial  ???                   41841      61       2       22       1
```

This shows 61 tasks waiting, 2 running (the worker's 2 cores), 22 done, and 1
worker. `--ssl` is needed because the manager encrypts its connections, which
is `TaskVineDistributor`'s default. `PROJECT` is the manager's name; Module 4
explains why it matters.

There are two more views of the same manager:

=== "Option A: conda"

    ```bash
    vine_status --ssl -W localhost 41841   # workers: cores/memory/disk used vs. available
    vine_status --ssl -T localhost 41841   # tasks: state, and resources each one asked for
    ```

=== "Option B: pixi"

    ```bash
    pixi run vine_status --ssl -W localhost 41841   # workers: cores/memory/disk used vs. available
    pixi run vine_status --ssl -T localhost 41841   # tasks: state, and resources each one asked for
    ```

```
HOST       ADDRESS         COMPLETED RUNNING CORE_U CORE_A MEM_U MEM_A DISK_U DISK_A GPUS_U GPUS_A
disc-head- ???                    22 2       2      2      63526 63526 136238 181654 0      0
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
perf.tasks-capacities.svg  perf.time-manager.svg  perf.times-stacked.svg perf.transfer.svg       perf.workers-disk.svg
taskgraph.pdf
```

(`vine_plot_taskgraph` also leaves a `taskgraph.dot` in the current directory,
which is the graphviz source for the PDF.) `-u s` puts time in seconds, and
`-s 5` samples the log every 5 seconds rather than the default 30, because
this run was short.

These are image files on glados. Copy them to your laptop by running this **on
your laptop**, not on glados:

```bash
scp '<netid>@glados.crc.nd.edu:vine-cms-analysis-stack/examples/tutorial_nd/plots/*' .
```

Open `perf.tasks-accum.svg` in a browser, which shows tasks submitted
vs. completed over time for all 94 of them (83 processor calls plus 11
reductions). Then open `taskgraph.pdf`, which shows processor tasks feeding
reductions, and reductions feeding the final one. This is a reduction tree
that `vine_reduce` built as results arrived, as opposed to one planned up
front.

## Distributor vs. executor, now for real

Given that there is a real manager and a real worker now, the split from
Module 0 is something you can actually point at.

The **distributor**, `TaskVineDistributor` (i.e., the TaskVine manager inside
your script), decided *where and when* each call ran: it queued 94 tasks,
sent them to the worker as cores freed up, and fetched the results. The
**executor**, in this case a plain in-process call inside each task's sandbox
on the worker, ran your processor once the task arrived.

Swapping `LocalDistributor` for `TaskVineDistributor` changed only the first.
Module 4 changes where the worker lives; the executor, and your processor,
stay put.
