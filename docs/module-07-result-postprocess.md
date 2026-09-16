# Module 7 - Shipping results out: `result_postprocess`

**15 min**

So far every result was a pair of histograms, which stays at a few
kilobytes whatever the input size. A **skim** is a bit different, as it
keeps the selected events themselves, and thus it grows with the data.
Passing gigabytes of events back through your manager process, just to
write them to disk there, is exactly what VineReduce is designed to avoid.

This module writes the skim straight from the worker to shared storage,
and sends back to the manager only a small note about where the skim went.

## Get the script

```bash
curl -sL -o scripts/vr_trijet_skim.py \
  https://raw.githubusercontent.com/cooperative-computing-lab/vine-cms-analysis-stack-tutorials/main/scripts/vr_trijet_skim.py
```

It uses the same real data and pool setup as [Module 4](module-04-scale-out.md).

## The skim

The processor makes the same best-trijet choice as before; however, rather
than filling histograms, it keeps the events whose trijet mass is between
150 and 195 GeV and returns them:

```python
def trijet_skimmer(events):
    ...  # Module 4's best-trijet selection
    in_window = ak.fill_none((best.p4.mass > MASS_LOW) & (best.p4.mass < MASS_HIGH), False)

    selected = events[in_window]
    best = ak.drop_none(best[in_window], axis=0)
    return ak.zip(
        {
            "jet_pt": selected.Jet.pt,
            ...
            "trijet_pt": best.p4.pt,
            "trijet_mass": best.p4.mass,
            "dataset": ak.Array([events.metadata["dataset"]] * len(selected)),
        },
        depth_limit=1,
    )
```

The default reducer knows how to add histograms, but not how to merge event
arrays, so the skim brings its own:

```python
def accumulate_skims(a, b):
    return ak.concatenate([a, b], axis=0)
```

## Writing it out from the worker

`result_postprocess` runs **on the worker**, once per final result, just
before that result would be sent back:

```python
SKIM_DIR = f"/project01/ndcms/users/{getpass.getuser()}/trijet-skims"

def make_result_postprocess(skim_dir):
    def result_postprocess(skim):
        if len(skim) == 0:
            return {"path": None, "events": 0}
        dataset_name = str(skim["dataset"][0])
        os.makedirs(skim_dir, exist_ok=True)
        out_path = os.path.join(skim_dir, f"{dataset_name}.{uuid.uuid4().hex}.parquet")
        ak.to_parquet(skim, out_path)
        return {"path": out_path, "events": len(skim)}
    return result_postprocess
```

It writes the events to parquet under `/project01`, which is shared by the
pool's worker nodes and the login node. What it returns is only a
**locator**, that is, the file's path and how many events it holds.

Three settings in `VineReduceCoffea(...)` tie this together:

```python
vr = VineReduceCoffea(
    processors={"skim": trijet_skimmer},
    ...
    chunksize=10_000,
    reducer=accumulate_skims,
    is_result=lambda n, t, m: n >= 10_000,
    result_postprocess=make_result_postprocess(SKIM_DIR),
    result_postprocess_offload=True,
)
```

With **`result_postprocess_offload=True`**, the locator is the only thing
that comes back. Rather than pickling a result into `*.pkl.zst`, VineReduce
writes a small `*.pointer.json` into `results/`, and thus the manager never
sees the events.

**`is_result=lambda n, t, m: n >= 10_000`** changes how many final results
there are. Normally there is one final result per dataset, covering every
event. However, `is_result` gets a group's number of events (`n`), total
wall time (`t`), and total memory (`m`), and decides whether that group is
already a final result. Here any group covering 10,000 events or more is
final, so one run writes **several** parquet files, each a piece of the
skim. This is how you keep single skim files from growing without bound.

The **uuid** in each file name matters for the same reason. Several final
results can be written at the same moment, and each of them needs its own
file.

## Workers that can see `/project01`

Not every node in today's pool mounts `/project01`. Therefore, add a condor
requirement to your factory configuration so that your workers only land on
nodes that do:

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
  "factory-timeout": 120,
  "condor-requirements": "(has_vast)"
}
EOF
```

!!! note "On glados (T3)"
    Remove the `condor-requirements` line when running from glados, as all
    workers there have VAST (`/project01`) mounted already.

## Run it

**Terminal 1:**

=== "Option A: conda"

    ```bash
    conda activate vine-cms-analysis-stack
    python scripts/vr_trijet_skim.py
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/vr_trijet_skim.py
    ```

**Terminal 2**, the factory with the new `factory.json`:

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

This time there are 50 chunks of 10,000 events. In the run below, the workers
took about two and a half minutes to start, and the whole run about six:

<div class="term">
TaskVine manager 'btovar-trijet-tutorial' listening on port 43775
skims will be written under /project01/ndcms/users/btovar/trijet-skims
waiting for workers from your vine_factory...
...
<span class="t-green">success             </span> processor skim/SingleMu ...n2012B_SingleMu.root[490000:500000] (id=f94fb8b3) cores=1(1) memory_mb=214(2016) wall_time_s=4(0)
<span class="t-green">success             </span> result    skim/SingleMu reduction of 10 partials (final) (id=614f2c8c) cores=1(1) memory_mb=222(2016) wall_time_s=1(0)
<span class="t-green">success             </span> result    skim/SingleMu reduction of 10 partials (final) (id=a000f590) cores=1(1) memory_mb=211(2016) wall_time_s=1(0)
<span class="t-green">success             </span> result    skim/SingleMu reduction of 10 partials (final) (id=4e6be0be) cores=1(1) memory_mb=220(2016) wall_time_s=1(0)
<span class="t-green">success             </span> result    skim/SingleMu reduction of 10 partials (final) (id=401c7050) cores=1(1) memory_mb=219(2016) wall_time_s=1(0)
<span class="t-green">success             </span> result    skim/SingleMu reduction of 10 partials (final) (id=bd866061) cores=1(1) memory_mb=218(2016) wall_time_s=1(0)
skim       [ <span class="t-green">██████████████████████████████</span> ]                 <span class="t-yellow">50</span>/<span class="t-red">0</span>/<span class="t-blue">50</span>
reductions [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">5</span>/<span class="t-red">0</span>/<span class="t-blue">5</span>
events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">500000</span>(<span class="t-green">500000</span>)/<span class="t-red">0</span>/<span class="t-blue">500000</span>
datasets   [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>
 22111 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu.99c11030654a4ddb9016ba56e306a4d4.parquet
 17109 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu.3fc05863b6e24e3c80dd809751fe584b.parquet
 14624 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu.fe18e8c785634bd4a2abfadc5e82f768.parquet
 25364 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu.dc3f684afde045e0b45aa072777a2f23.parquet
 20343 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu.0bcd9c4b5efa46af9e8cd361ed858ba2.parquet
5 final results, 99551 events in the skim
</div>

Every group of 10 partial results already covered 100,000 events, well
over `is_result`'s 10,000, so each of them became a final result on the
spot (`result ... (final)`). Thus the run produces **5 final results** rather than
one, and 5 parquet files. Of the 500,000 events, **99,551** have a best
trijet between 150 and 195 GeV. The file sizes differ because each
file is a different slice of the data. Further, all 5 final
reductions wrote their files on the workers, and none of the events came
back through this terminal.

## What's on the manager's side

```bash
ls results/SingleMu/skim/
```

```
skim__38ccab6c2c0647cdb8c8759df329121c.pointer.json
skim__9e3cbdd17e1d4e1995749d6f039313d7.pointer.json
skim__b3d216d9782a4c7eaf3baeb0f876c587.pointer.json
skim__df7b1f74eedc4e3bb5d89173e520d270.pointer.json
skim__f3afafd779f04878add3c48913d36761.pointer.json
```

There is no `*.pkl.zst` this time, only one small pointer file per final
result.

```bash
cat results/SingleMu/skim/skim__38ccab6c2c0647cdb8c8759df329121c.pointer.json
```

```json
{"offloaded": true, "processor_name": "skim", "dataset_name": "SingleMu", "locator": {"path": "/project01/ndcms/users/btovar/trijet-skims/SingleMu.99c11030654a4ddb9016ba56e306a4d4.parquet", "events": 22111}}
```

VineReduce wraps whatever `result_postprocess` returned (`locator`) with
the pipeline it came from. This is everything the manager ever held for
this skim, and also everything a later step needs to find and read the
data.

## What's on `/project01`

The skim itself is on shared storage. From the login node:

```bash
ls -l /project01/ndcms/users/$USER/trijet-skims/
```

```
total 14208
-rw-r--r-- 1 btovar osguser 2967719 Sep 14 11:57 SingleMu.0bcd9c4b5efa46af9e8cd361ed858ba2.parquet
-rw-r--r-- 1 btovar osguser 2499395 Sep 14 11:57 SingleMu.3fc05863b6e24e3c80dd809751fe584b.parquet
-rw-r--r-- 1 btovar osguser 3270735 Sep 14 11:57 SingleMu.99c11030654a4ddb9016ba56e306a4d4.parquet
-rw-r--r-- 1 btovar osguser 3950022 Sep 14 11:57 SingleMu.dc3f684afde045e0b45aa072777a2f23.parquet
-rw-r--r-- 1 btovar osguser 1859295 Sep 14 11:57 SingleMu.fe18e8c785634bd4a2abfadc5e82f768.parquet
```

That is five files, about 14 MB in total. At this size it perhaps wouldn't
have mattered much where they were written; however, the pattern is the
same when the skim is hundreds of gigabytes, as the manager only ever
handles the five one-line pointers.

!!! note "The skim directory keeps growing"
    Every run adds five new files (new uuids) next to the old ones.
    `results/` is wiped at the start of each run, but
    `/project01/.../trijet-skims/` is not. Clean it up yourself between
    attempts: `rm /project01/ndcms/users/$USER/trijet-skims/*.parquet`.

When you're done, stop the factory with Ctrl-C and check `condor_q`, as
in [Module 4](module-04-scale-out.md#clean-up-after-yourself).
