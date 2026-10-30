# Module 4 - Scale out

TODO: CURL with_oasis_certs FROM SOMEWHERE

**30 min**

This module runs the same trijet analysis as before, however with three
important differences. The data is now **CMS Open Data** read over
xrootd; the workers are **HTCondor jobs** on the pool, rather
than processes on the login node; and they find your manager **by name**,
through a catalog server, as opposed to by host and port.

Each of those changes needs one new piece: a packed environment, a manager
name, a `vine_factory` in a second terminal, and a certificate wrapper.
None of them touches the analysis itself, which is perhaps the main point
of this module.

## The files

From `~/vine-cms-analysis-stack/examples/tutorial_nd`, this module's script is
`scripts/vr_trijet_condor.py` (`scripts/vr_trijet_condor_rdf.py` for
RDataFrame); there is nothing to download.

You also need the certificate wrapper, `with_oasis_certs`, in
`~/vine-cms-analysis-stack/examples/tutorial_nd/` (see [Certificates](#certificates)):

!!! danger "TODO"
    How students get `with_oasis_certs` is still to be decided. It isn't
    published on GitHub. Once you have it:

    ```bash
    chmod +x with_oasis_certs
    ```

## What changed in the script

**1. The data.** The script reads `data/datasets_xrootd.json` from
Module 1, the same 15 files and 5 datasets as before, but now by their
`root://cmsxrootd.crc.nd.edu/...` URLs: pool nodes read them over xrootd,
which works from any node, whether or not it mounts `/project01`. (Every
node in glados's pool does, but many nodes in other pools don't.) The chunks are also
larger (`chunksize=100_000`), so that there are fewer, longer tasks:

```diff
-    datasets_path = os.path.join(REPO_ROOT, "data", "datasets_vast.json")
+    datasets_path = os.path.join(REPO_ROOT, "data", "datasets_xrootd.json")
 ...
-        chunksize=50_000,
+        chunksize=100_000,
```

**2. Every task ships your environment.** Pool nodes may not have coffea,
ROOT, vine_reduce, or even this Python installed, therefore the environment
has to travel with the tasks:

```diff
-from vine_reduce import serialization
+from vine_reduce import get_environment, serialization
 ...
+    environment = get_environment()
+
     distributor = TaskVineDistributor(
         name=MANAGER_NAME,
         port=0,
-        resources_processor={"cores": 1},
-        resources_reducer={"cores": 1},
+        environment=environment,
+        resources_processor={"cores": 1, "memory_mb": 2000},
+        resources_reducer={"cores": 1, "memory_mb": 2000},
     )
     print(f"TaskVine manager {MANAGER_NAME!r} listening on port {distributor.port}")
+    print("waiting for workers from your vine_factory...")
```

`get_environment()` returns the tarball you built in Module 1, and given
that it is a cache hit, the call is instant. TaskVine sends the tarball to
each worker once, unpacks it there, and runs every task inside it.

The `resources_*` dicts have a new `memory_mb`, and with it each call is now
allowed 1 core and 2000 MB. On a shared pool, you declare what a task
needs rather than letting it take a share of the whole worker. Choosing
those numbers well is a bit of an art, and it is the subject of
[Module 5](module-05-resources.md).

**3. No `vine.Factory`.** Workers now come from a separate `vine_factory`
process that you run yourself, in a second terminal, so the worker you
started inside the script in Module 3 goes away (and with it the
`import ndcctools.taskvine as vine`):

```diff
-import ndcctools.taskvine as vine
 ...
-    workers = vine.Factory(manager_host_port=f"localhost:{distributor.port}")
-    workers.ssl = True
-    workers.cores = 2
-    workers.min_workers = 1
-    workers.max_workers = 1
-    workers.extra_options = "--single-shot"
-
-    with distributor, workers:
+    with distributor:
         vr.compute()
```

**The manager's name** is not new (it came in with Module 3), but this is
where it starts to matter. The manager advertises its name to the catalog
server (`catalog.cse.nd.edu`). Workers on pool nodes have no idea which
machine or port your script is on. Rather, they ask the catalog for a
manager called `<your netid>-trijet-tutorial` and connect to whatever it
answers. Having your netid in the name keeps your workers from joining a
classmate's run.

## The factory configuration

Still in `~/vine-cms-analysis-stack/examples/tutorial_nd`, write `factory.json`:

```bash
cat > factory.json <<EOF
{
  "manager-name": "$USER-trijet-tutorial",
  "min-workers": 0,
  "max-workers": 2,
  "cores": 4,
  "memory": 8000,
  "disk": 16000,
  "timeout": 300,
  "factory-timeout": 120
}
EOF
cat factory.json
```

```json
{
  "manager-name": "<netid>-trijet-tutorial",
  "min-workers": 0,
  "max-workers": 2,
  "cores": 4,
  "memory": 8000,
  "disk": 16000,
  "timeout": 300,
  "factory-timeout": 120
}
```

- `manager-name`: only managers with exactly this name get workers.
- `min-workers`/`max-workers`: never more than 2 worker jobs at a time.
  This is today's per-student limit, so that the whole class fits on the
  pool.
- `cores`/`memory`/`disk`: what each worker job asks HTCondor for (MB for
  memory and disk).
- `timeout`: a worker with nothing to do for 300 s exits.
- `factory-timeout`: the factory exits after 120 s without seeing your
  manager.

## Run it: two terminals

**Terminal 1**, start the analysis:

=== "coffea"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_condor.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_condor.py
        ```

=== "RDataFrame"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_condor_rdf.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_condor_rdf.py
        ```

```
TaskVine manager '<netid>-trijet-tutorial' listening on port 45697
waiting for workers from your vine_factory...
```

Nothing happens yet, since the manager has tasks but no workers to run
them.

**Terminal 2**, `cd ~/vine-cms-analysis-stack/examples/tutorial_nd` and start the factory:

=== "Option A: conda"

    ```bash
    conda activate vine-cms-analysis-stack
    vine_factory -T condor -C factory.json -E '--single-shot' \
      --wrapper ./with_oasis_certs --wrapper-input with_oasis_certs
    ```

=== "Option B: pixi"

    ```bash
    pixi run vine_factory -T condor -C factory.json -E '--single-shot' \
      --wrapper ./with_oasis_certs --wrapper-input with_oasis_certs
    ```

- `-T condor`: submit workers as HTCondor jobs.
- `-C factory.json`: the configuration above.
- `-E '--single-shot'`: passed on to every `vine_worker`, as in Module 3,
  so that the worker exits as soon as its manager goes away.
- `--wrapper ./with_oasis_certs --wrapper-input with_oasis_certs`: send the
  wrapper script along with each job, and start the worker through it
  (see [Certificates](#certificates) below).

The factory prints its configuration, then one line per cycle:

```
manager-name: <netid>-trijet-tutorial
max-workers: 2
min-workers: 0
workers-per-cycle: 5
tasks-per-worker: 4
timeout: 300 s
cores: 4.000
factory-timeout: 120 MB
memory: 8000 MB
disk: 16000 MB
worker-extra-options: --single-shot
2026/09/14 11:09:42: |submitted: 0 |needed: 2 |waiting connection: 0 |requested: 2
PROJECT            HOST                   PORT WAITING RUNNING COMPLETE WORKERS
<netid>-trijet-tuto condorfe.crc.nd.edu   45697       5       0        0       0
```

The factory found your manager by name, with tasks waiting and no
workers, and thus requested 2 workers. (The host names in this module's
sample outputs — `condorfe.crc.nd.edu` here, `d32cepyc*` pool nodes
below — are the machines these pages were captured on; yours will show
your own login node and whatever nodes your workers land on.) (The numbers in this and the next section
come from an earlier, smaller version of this run on the pool, 5 tasks over one
file, so your counts are larger: 44 tasks today. The commands and the columns are
the same.) (The `factory-timeout: 120 MB` line
is a cosmetic typo in the factory's printout; the value is in fact 120
seconds.)

Further, the factory creates a scratch directory, `vine-factory-<uid>/`,
with the HTCondor submit file it generated (`condor.submit`), the job log
(`condor.logfile`), and copies of `vine_worker` and `with_oasis_certs`.

## Watch it

Use a **third terminal** (`cd ~/vine-cms-analysis-stack/examples/tutorial_nd`), or, if you
prefer to wait, terminal 2 after the run.

### The worker jobs

```bash
condor_q -nobatch
```

```
 ID        OWNER            SUBMITTED     RUN_TIME ST PRI SIZE CMD
391509.0   btovar          9/14 11:18   0+00:00:10 I  0    0.0 condor.sh ./with_oasis_certs ./vine_worker --parent-death -M "btovar-trijet-tutorial" -t 300 -C ''''catalog.cse.nd.edu,backup-catalog.cse.nd.edu'''' --cores=$$([TARGET.Cpus]) --memory=$$([TARGET.Memory]) --disk=$$([TARGET.Disk/1024]) --single-shot
391510.0   btovar          9/14 11:18   0+00:00:10 I  0    0.0 condor.sh ./with_oasis_certs ./vine_worker --parent-death -M "btovar-trijet-tutorial" -t 300 -C ''''catalog.cse.nd.edu,backup-catalog.cse.nd.edu'''' --cores=$$([TARGET.Cpus]) --memory=$$([TARGET.Memory]) --disk=$$([TARGET.Disk/1024]) --single-shot
```

There are two jobs, each a `vine_worker` started through
`with_oasis_certs` and looking for your manager by name. The `ST` column
is `I` (idle, waiting for a slot) and turns `R` once HTCondor places the
job on a node. How long that takes depends on how busy the pool is; for
example, it may be seconds on a quiet pool, as opposed to minutes when the
pool is full.

### The manager, through the catalog

With the catalog, you need no host or port, just the name:

=== "Option A: conda"

    ```bash
    vine_status -M "$USER-trijet-tutorial"
    ```

=== "Option B: pixi"

    ```bash
    pixi run vine_status -M "$USER-trijet-tutorial"
    ```

```
PROJECT            HOST                   PORT WAITING RUNNING COMPLETE WORKERS
btovar-trijet-tuto condorfe.crc.nd.edu   45697       5       0        0       0
```

This is the catalog's copy of your manager's status, rather than the
status itself. Managers report to the catalog about once a minute, thus
this view lags a bit behind. For a live view, ask the manager directly
with the host and port this line gives you (with `--ssl`, as in
Module 3):

=== "Option A: conda"

    ```bash
    vine_status --ssl -W condorfe.crc.nd.edu 45697
    ```

=== "Option B: pixi"

    ```bash
    pixi run vine_status --ssl -W condorfe.crc.nd.edu 45697
    ```

```
HOST       ADDRESS         COMPLETED RUNNING CORE_U CORE_A MEM_U MEM_A DISK_U DISK_A GPUS_U GPUS_A
d32cepyc19 ???                     0 1       1      4      2016  8064  6790   16001  0      0
d32cepyc20 ???                     0 4       4      4      8064  8064  15364  16001  0      0
```

Here there are two workers on pool nodes, `d32cepyc199` and `d32cepyc204`
(`vine_status` cuts the `HOST` column to 10 characters, hence `d32cepyc19`
and `d32cepyc20` above), each with the 4 cores and ~8 GB you asked for. In particular, on
`d32cepyc204`, 4 tasks use all 4 cores and all 8064 MB, given that each
1-core task was assigned its core's share of the worker's memory,
8064 / 4 = 2016 MB.

### A worker arriving, in the manager's log

```bash
grep -E 'worker .* connected|completed ssl' vine-run-info/most-recent/vine-logs/debug
```

```
2026/09/14 15:09:53.90 vine_manager[174896]vine: worker 10.32.91.175:55916 connected
2026/09/14 15:09:53.92 vine_manager[174896]vine: worker 10.32.91.175:55916 completed ssl connection
```

Note that these timestamps are in UTC. A few lines further down, the log
also names the node:
`rx from d32cepyc204.crc.nd.edu (10.32.91.175:55916)`.

## The result

=== "coffea"

    Back in terminal 1, the run ended like this:

    <div class="term">
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_1.root[100000:200000] (id=292610cb) cores=1(1) memory_mb=568(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_0.root[0:53733] (id=978fdac0) cores=1(1) memory_mb=249(2016) wall_time_s=1(0)
    ...
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_194790-195398 reduction of 8 partials (final) (id=76c03623) cores=1(1) memory_mb=203(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195399-195841 reduction of 7 partials (final) (id=ae745006) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=cd294495) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    trijet     [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">44</span>/<span class="t-red">0</span>/<span class="t-blue">44</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                      <span class="t-yellow">6</span>/<span class="t-red">0</span>/<span class="t-blue">6</span>
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

    The run processed 44 chunks of up to 100,000 events, read straight from the
    ND xrootd server by workers in the pool, followed by one final reduction per
    dataset (plus one more for the dataset with more than 10 chunks).
    The allocation in parentheses is `2016` MB because, as in Module 3, a 1-core
    task gets its core's share of the worker's memory, and on these 4-core,
    ~8 GB workers that share is just above the 2000 MB you declared. Each chunk
    used 250-770 MB of it, therefore the limit never came close to mattering;
    [Module 5](module-05-resources.md) shows how to make a memory limit
    actually bind.

=== "RDataFrame"

    Back in terminal 1, the run took about two minutes, and ended like this:

    <div class="term">
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_0.root[0:53733] (id=2ebe4cac) cores=1(1) memory_mb=865(2016) wall_time_s=4(0)
    <span class="t-green">success             </span> processor trijet/SingleMu_Run2012B_193834-194270 ...4-194270/file_1.root[0:100000] (id=2ec0199e) cores=1(1) memory_mb=911(2016) wall_time_s=6(0)
    ...
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_194790-195398 reduction of 8 partials (final) (id=8e835d0d) cores=1(1) memory_mb=203(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195399-195841 reduction of 7 partials (final) (id=1f0f7b6c) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> final     trijet/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=964518ff) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    trijet     [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">44</span>/<span class="t-red">0</span>/<span class="t-blue">44</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                      <span class="t-yellow">6</span>/<span class="t-red">0</span>/<span class="t-blue">6</span>
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

    The run processed 44 chunks of up to 100,000 events, read straight from the
    ND xrootd server by workers in the pool, followed by one final reduction per
    dataset (and one extra reduction in each dataset with more than 10 chunks).
    The allocation in parentheses is `2016` MB because, as in Module 3, a 1-core
    task gets its core's share of the worker's memory. Each chunk used 865-976
    MB of it, about 750 MB of which is ROOT compiling `BestTrijet`, and took 4
    to 8 seconds, as opposed to coffea's 1: every task compiles the C++ first.
    The limit is still not close to binding; [Module 5](module-05-resources.md)
    looks at what does bind it with RDataFrame.

*The output of this section was captured with a local worker of the same size as the pool's (4 cores, 8064 MB), rather than on the pool itself, so your timings will differ.*

This is perhaps the part worth pausing on. Your processor code didn't
change between Module 2's run over `/project01` on the login node and this
run on pool nodes reading over xrootd; only the dataset file and the
distributor did.

## Certificates

The `with_oasis_certs` wrapper runs on the pool node before the worker
starts, and goes through the following steps:

- If the node has `/cvmfs/oasis.opensciencegrid.org`, it sets up the grid
  certificates from there.
- If not (every node in glados's pool has it, but many nodes elsewhere
  don't), it writes the few CA certificates
  it needs, bundled inside the script, into a temporary directory and
  points `X509_CERT_DIR` there.
- If a `proxy.pem` is in the job's directory, it sets `X509_USER_PROXY`
  to it.
- Then it runs the rest of its command line (the `vine_worker`
  invocation) and cleans up.

!!! note "Today's data doesn't need a proxy"
    `cmsxrootd.crc.nd.edu` served these files without a proxy when this
    page was tested (from the login node), thus the proxy half of the
    wrapper does nothing today. However, you would need it for
    real, access-controlled CMS data; in that case, put your proxy next to
    the wrapper and add it with another `--wrapper-input`. The wrapper is
    in today's setup so that the command you practice is the same command
    you would use later.

## Clean up

On a shared pool, idle workers hold slots other people could use. Three
settings already limit that.
With `--single-shot`, each worker exits as soon as your manager goes away;
for example, in the run above both worker jobs ended (`Normal termination (return
value 0)` in `vine-factory-*/condor.logfile`) 2 seconds after the
script finished. With `timeout: 300`, a worker that never gets work exits
after 5 minutes. Further, with `factory-timeout: 120`, the factory exits
after 2 minutes without seeing your manager.

The factory looks your manager up
**by name in the catalog**, and the catalog keeps a manager's last status
for a while after the manager is gone. If an earlier run of yours was
killed while it still had tasks waiting, its stale entry keeps advertising
work under your name. The factory will then keep submitting workers for a
manager that no longer exists, and never reach its `factory-timeout`. Such
a factory is not broken; rather, it is responding to stale catalog
information.

Therefore, when your script finishes:

1. Stop the factory in terminal 2 with **Ctrl-C**. It removes the worker
   jobs it submitted before exiting:

    ```
    received signal(2), shutting down workers...
    removing 2 workers...
    all workers removed.
    ```

2. Check for leftover worker jobs:

    ```bash
    condor_q
    ```

3. Remove any that are still there:

    ```bash
    condor_rm <cluster id>
    ```
