# Module 4 - Scale out

**30 min**

This module runs the same trijet analysis as before, however with three
important differences. The data is now **real CMS Open Data**, read over
xrootd from CERN; the workers are **HTCondor jobs** on the pool, rather
than processes on the login node; and they find your manager **by name**,
through a catalog server, as opposed to by host and port.

Each of those changes needs one new piece: a packed environment, a manager
name, a `vine_factory` in a second terminal, and a certificate wrapper.
None of them touches the analysis itself, which is perhaps the main point
of this module.

## Get the files

From `~/vine-cms-analysis-stack`:

```bash
curl -sL -o scripts/vr_trijet_condor.py \
  https://raw.githubusercontent.com/cooperative-computing-lab/vine-cms-analysis-stack-tutorials/main/scripts/vr_trijet_condor.py
```

You also need the certificate wrapper, `with_oasis_certs`, in
`~/vine-cms-analysis-stack/` (see [Certificates](#certificates)):

!!! danger "TODO"
    How students get `with_oasis_certs` is still to be decided. It isn't
    published on GitHub. Once you have it:

    ```bash
    chmod +x with_oasis_certs
    ```

## What changed in the script

Open `scripts/vr_trijet_condor.py`. The functions `trijet_processor` and
`load_result` are the same as in Module 3; thus, only four things differ:

**1. The data.** The script reads `data/datasets_small_real.json` from
Module 1, which points to one NanoAOD file on `eospublic.cern.ch`, capped
at 500,000 events.

**2. The manager has a name**, and advertises it to the catalog server
(`catalog.cse.nd.edu`):

```python
MANAGER_NAME = f"{getpass.getuser()}-trijet-tutorial"
```

Workers on pool nodes have no idea which machine or port your script is
on. Rather, they ask the catalog for a manager called
`<your netid>-trijet-tutorial` and connect to whatever it answers. Having
your netid in the name keeps your workers from joining a classmate's run.

**3. Every task ships your environment.** Pool nodes don't have coffea,
vine_reduce, or even this Python installed, therefore the environment has
to travel with the tasks:

```python
environment = get_environment()

distributor = TaskVineDistributor(
    name=MANAGER_NAME,
    port=0,
    environment=environment,
    resources_processor={"cores": 1, "memory_mb": 2000},
    resources_reducer={"cores": 1, "memory_mb": 2000},
)
```

`get_environment()` returns the tarball you built in Module 1, and given
that it is a cache hit, the call is instant. TaskVine sends the tarball to
each worker once, unpacks it there, and runs every task inside it.

The `resources_*` dicts are new too, and with them each call is now
allowed 1 core and 2000 MB. On a shared pool, you declare what a task
needs rather than letting it take a share of the whole worker. Choosing
those numbers well is a bit of an art, and it is the subject of
[Module 5](module-05-resources.md).

**4. No `vine.Factory`.** Workers now come from a separate `vine_factory`
process that you run yourself, in a second terminal.

## The factory configuration

Still in `~/vine-cms-analysis-stack`, write `factory.json`:

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

=== "Option A: conda"

    ```bash
    conda activate vine-cms-analysis-stack
    python scripts/vr_trijet_condor.py
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/vr_trijet_condor.py
    ```

```
TaskVine manager '<netid>-trijet-tutorial' listening on port 45697
waiting for workers from your vine_factory...
```

Nothing happens yet, since the manager has tasks but no workers to run
them.

**Terminal 2**, `cd ~/vine-cms-analysis-stack` and start the factory:

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

The factory found your manager by name, with 5 tasks waiting and no
workers, and thus requested 2 workers. (The host names in this module's
sample outputs — `condorfe.crc.nd.edu` here, `d32cepyc*` pool nodes
below — are the machines these pages were captured on; yours will show
your own login node and whatever nodes your workers land on.) (The `factory-timeout: 120 MB` line
is a cosmetic typo in the factory's printout; the value is in fact 120
seconds.)

Further, the factory creates a scratch directory, `vine-factory-<uid>/`,
with the HTCondor submit file it generated (`condor.submit`), the job log
(`condor.logfile`), and copies of `vine_worker` and `with_oasis_certs`.

## Watch it

Use a **third terminal** (`cd ~/vine-cms-analysis-stack`), or, if you
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

Back in terminal 1, the run took under a minute once the workers
arrived:

<div class="term">
<span class="t-green">success             </span> processor trijet/SingleMu ...n2012B_SingleMu.root[200000:300000] (id=29460336) cores=1(1) memory_mb=544(2016) wall_time_s=5(0)
<span class="t-green">success             </span> processor trijet/SingleMu ...n2012B_SingleMu.root[100000:200000] (id=cadbabfd) cores=1(1) memory_mb=684(2016) wall_time_s=5(0)
<span class="t-green">success             </span> processor trijet/SingleMu ...n2012B_SingleMu.root[300000:400000] (id=118a1a19) cores=1(1) memory_mb=580(2016) wall_time_s=5(0)
<span class="t-green">success             </span> processor trijet/SingleMu ...n2012B_SingleMu.root[0:100000] (id=2f009f6e) cores=1(1) memory_mb=408(2016) wall_time_s=6(0)
<span class="t-green">success             </span> processor trijet/SingleMu ...n2012B_SingleMu.root[400000:500000] (id=b3295482) cores=1(1) memory_mb=524(2016) wall_time_s=5(0)
<span class="t-green">success             </span> final     trijet/SingleMu reduction of 5 partials (final) (id=707891ec) cores=1(1) memory_mb=190(2016) wall_time_s=1(0)
trijet     [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">5</span>/<span class="t-red">0</span>/<span class="t-blue">5</span>
reductions [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">500000</span>(<span class="t-green">500000</span>)/<span class="t-red">0</span>/<span class="t-blue">500000</span>
datasets   [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>
trijet pT histogram: 217890 entries
max b-tag histogram: 217890 entries
</div>

The run processed five 100,000-event chunks, read straight from CERN by
workers on the ND pool, followed by one final reduction. The allocation in
parentheses is `2016` MB because, as in Module 3, a 1-core task gets its
core's share of the worker's memory, and on these 4-core, ~8 GB workers
that share is just above the 2000 MB you declared. Each chunk used
400-700 MB of it, therefore the limit never came close to mattering;
[Module 5](module-05-resources.md) shows how to make a memory limit
actually bind.

This is perhaps the part worth pausing on. Your processor code didn't
change between the laptop-sized synthetic files and a real NanoAOD file on
another continent; only the dataset file and the distributor did.

## Certificates

The `with_oasis_certs` wrapper runs on the pool node before the worker
starts, and goes through the following steps:

- If the node has `/cvmfs/oasis.opensciencegrid.org`, it sets up the grid
  certificates from there.
- If not (and many pool nodes don't), it writes the few CA certificates
  it needs, bundled inside the script, into a temporary directory and
  points `X509_CERT_DIR` there.
- If a `proxy.pem` is in the job's directory, it sets `X509_USER_PROXY`
  to it.
- Then it runs the rest of its command line (the `vine_worker`
  invocation) and cleans up.

!!! note "Today's data doesn't need a proxy"
    `eospublic.cern.ch` serves CMS Open Data to anyone, thus the proxy
    half of the wrapper does nothing today. However, you would need it for
    real, access-controlled CMS data; in that case, put your proxy next to
    the wrapper and add it with another `--wrapper-input`. The wrapper is
    in today's setup so that the command you practice is the same command
    you would use later.

## Clean up after yourself

On a shared pool, idle workers hold slots other people could use. Three
settings already limit that.
With `--single-shot`, each worker exits as soon as your manager goes away;
for example, in the run above both worker jobs ended (`Normal termination (return
value 0)` in `vine-factory-*/condor.logfile`) 2 seconds after the
script finished. With `timeout: 300`, a worker that never gets work exits
after 5 minutes. Further, with `factory-timeout: 120`, the factory exits
after 2 minutes without seeing your manager.

However, don't rely on those alone. The factory looks your manager up
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
