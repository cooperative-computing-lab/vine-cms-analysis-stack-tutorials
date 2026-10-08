# Module 7 - Shipping results out: `result_postprocess`

**15 min**

So far every result was a pair of histograms, which stays at a few
kilobytes whatever the input size. A **skim** is a bit different, as it
keeps the selected events themselves, and thus it grows with the data.
Passing gigabytes of events back through your manager process, just to
write them to disk there, is exactly what VineReduce is designed to avoid.

This module writes the skim straight from the worker to shared storage,
and sends back to the manager only a small note about where the skim went.

It uses the same real data and pool setup as [Module 4](module-04-scale-out.md).

## What changed in the script

This module's script (`scripts/vr_trijet_skim.py`,
or `scripts/vr_trijet_skim_rdf.py`) is Module 4's
(`vr_trijet_condor.py`, or `vr_trijet_condor_rdf.py`), with the processor
swapped for a skimmer, a reducer, and a `result_postprocess` that writes the
skim out. The sections below walk through each of the three, and then show
how they plug into the `VineReduce...(...)` call. The data, the manager, the
packed environment, and `resources_*` are as in Module 4.

## The skim

=== "coffea"

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

=== "RDataFrame"

    The processor makes the same best-trijet choice as before; however, rather
    than filling histograms, it keeps the events whose trijet mass is between
    150 and 195 GeV and returns them. Two things are new: `chunk_to_args` also
    hands over the dataset's name, since `result_postprocess` will only see the
    skim and not which dataset it came from, and the selected columns leave
    RDataFrame as an awkward array through `ak.from_rdataframe`, so that the
    rest of this module is the same for both flavors:

    ```python
    def chunk_to_args(chunk, dataset_metadata, distributor_metadata=None):
        ...  # Module 4's RDataFrame over [chunk.start, chunk.stop)
        return df, dataset_metadata["dataset"]


    def trijet_skimmer(args):
        df, dataset_name = args
        ...  # Module 4's BestTrijet, compiled as before
        selected = (
            df.Filter("nJet >= 3")
            .Define("best", "BestTrijet(Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_btag)")
            .Filter(f"best[2] > {MASS_LOW} && best[2] < {MASS_HIGH}")
            .Define("jet_pt", "Jet_pt")
            ...
            .Define("trijet_pt", "best[0]")
            .Define("trijet_mass", "best[2]")
        )
        skim = ak.from_rdataframe(selected, columns=("jet_pt", ..., "trijet_mass"))
        skim["dataset"] = ak.Array([dataset_name] * len(skim))
        return skim
    ```

    `best[2]` is the third value that `BestTrijet` returns, the trijet's mass,
    next to its pT and its highest b-tag score from Module 4.

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

=== "coffea"

    Three settings in `VineReduceCoffea(...)` tie this together (diffed
    against Module 4's call):

    ```diff
     vr = VineReduceCoffea(
    -    processors={"trijet": trijet_processor},
    +    processors={"skim": trijet_skimmer},
         input=datasets_path,
         distributor=distributor,
         results_dir=results_dir,
         checkpoint_dir=checkpoint_dir,
    -    chunksize=100_000,
    +    chunksize=50_000,
    +    reducer=accumulate_skims,
    +    is_result=lambda n, t, m: n >= 50_000,
    +    result_postprocess=make_result_postprocess(SKIM_DIR),
    +    result_postprocess_offload=True,
     )
    ```

=== "RDataFrame"

    Three settings in `VineReduce(...)` tie this together (diffed against
    Module 4's call; `input_to_datasets` and `chunk_to_args` are as in
    Module 4, and `reducer=coffea_reducer` is replaced by the skim's own):

    ```diff
     vr = VineReduce(
    -    processors={"trijet": trijet_processor},
    +    processors={"skim": trijet_skimmer},
         input=datasets_path,
         input_to_datasets=coffea_input_to_datasets,
         chunk_to_args=chunk_to_args,
    -    reducer=coffea_reducer,
         distributor=distributor,
         results_dir=results_dir,
         checkpoint_dir=checkpoint_dir,
    -    chunksize=100_000,
    +    chunksize=50_000,
    +    reducer=accumulate_skims,
    +    is_result=lambda n, t, m: n >= 50_000,
    +    result_postprocess=make_result_postprocess(SKIM_DIR),
    +    result_postprocess_offload=True,
     )
    ```

With **`result_postprocess_offload=True`**, the locator is the only thing
that comes back. Rather than pickling a result into `*.pkl.zst`, VineReduce
writes a small `*.pointer.json` into `results/`, and thus the manager never
sees the events.

**`is_result=lambda n, t, m: n >= 50_000`** changes how many final results
there are. Normally there is one final result per dataset, covering every
event. However, `is_result` gets a group's number of events (`n`), total
wall time (`t`), and total memory (`m`), and decides whether that group is
already a final result. Here any group covering 50,000 events or more is
final, so one run writes **several** parquet files per dataset, each a piece
of the skim. This is how you keep single skim files from growing without bound.

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

=== "coffea"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_skim.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_skim.py
        ```

=== "RDataFrame"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_skim_rdf.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_skim_rdf.py
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

This time there are 83 chunks of up to 50,000 events, five datasets in all.

=== "coffea"

    The run below took under a minute once the workers were up:

    <div class="term">
    TaskVine manager 'btovar-trijet-tutorial' listening on port 43775
    skims will be written under /project01/ndcms/users/btovar/trijet-skims
    waiting for workers from your vine_factory...
    ...
    <span class="t-green">success             </span> processor skim/SingleMu_Run2012B_195842-196531 ...2-196531/file_2.root[50000:99449] (id=c37dc2d6) cores=1(1) memory_mb=315(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> final     skim/SingleMu_Run2012B_195399-195841 reduction of 3 partials (final) (id=fafb5f28) cores=1(1) memory_mb=249(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> result    skim/SingleMu_Run2012B_195842-196531 reduction of 10 partials (final) (id=0acae435) cores=1(1) memory_mb=295(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> final     skim/SingleMu_Run2012B_195842-196531 reduction of 8 partials (final) (id=86e0ead4) cores=1(1) memory_mb=268(2016) wall_time_s=1(0)
    skim       [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">83</span>/<span class="t-red">0</span>/<span class="t-blue">83</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">11</span>/<span class="t-red">0</span>/<span class="t-blue">11</span>
    events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>
     51491 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_193834-194270.d293f06c26b34a6881ef56cacb6479f4.parquet
     78200 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_193834-194270.628e1ba07e4444edb3c4d91f3e73b974.parquet
    104495 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194271-194789.22bad5ac4d604a428acfe8cecb3fadca.parquet
    101615 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194271-194789.f29ed1a0abe944db967f5aaa56039250.parquet
     20949 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194271-194789.3baf79829f824684a95aed90c7f4bfff.parquet
     21085 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194790-195398.3f7e0817258a44b49ca1384db2c09200.parquet
    105864 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194790-195398.1a9f144626af4f4eb419cc4e42e77ad1.parquet
     85146 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_195399-195841.bcf1498ba042400da20e05c8bcf0ef3e.parquet
     29110 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_195399-195841.3dbcdfeebd3242a2b45106904efff75f.parquet
     71729 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_195842-196531.e1e6b2219d0d4b3cba1fc6847e1a513d.parquet
    106502 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_195842-196531.885b37f41b764cbbb7a3af8bf3e3821d.parquet
    11 final results, 776186 events in the skim
    </div>

    Every group of 10 partial results covered up to 500,000 events, well over
    `is_result`'s 50,000, so each of them became a final result on the spot
    (`result ... (final)`), and what was left of each dataset was folded by one
    more, forced `final` reduction. Thus the run produces **11 final
    results** rather than one per dataset, and 11 parquet files: two or three for each dataset. Of
    the 3,736,416 events, **776,186** have a best trijet between 150
    and 195 GeV. The file sizes differ because each file is a different slice of
    the data. Further, all 11 final reductions wrote their files on the workers, and
    none of the events came back through this terminal.

=== "RDataFrame"

    The run below took about two and a half minutes once the workers were up:

    <div class="term">
    TaskVine manager 'btovar-trijet-tutorial' listening on port 43775
    skims will be written under /project01/ndcms/users/btovar/trijet-skims
    waiting for workers from your vine_factory...
    ...
    <span class="t-green">success             </span> processor skim/SingleMu_Run2012B_195842-196531 ...2-196531/file_2.root[50000:99449] (id=e90bb2a9) cores=1(1) memory_mb=881(2016) wall_time_s=7(0)
    <span class="t-green">success             </span> final     skim/SingleMu_Run2012B_195399-195841 reduction of 3 partials (final) (id=1f289b39) cores=1(1) memory_mb=143(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> result    skim/SingleMu_Run2012B_195842-196531 reduction of 10 partials (final) (id=e3afaddd) cores=1(1) memory_mb=187(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> final     skim/SingleMu_Run2012B_195842-196531 reduction of 8 partials (final) (id=4667c3e4) cores=1(1) memory_mb=169(2016) wall_time_s=1(0)
    skim       [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">83</span>/<span class="t-red">0</span>/<span class="t-blue">83</span>
    reductions [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">11</span>/<span class="t-red">0</span>/<span class="t-blue">11</span>
    events     [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets   [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>
     51491 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_193834-194270.87dd1353bb14470684ccf368d04a7db0.parquet
     78200 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_193834-194270.d9e238285510447e9bc0658a7508ba5a.parquet
     98205 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194271-194789.253b21ea0c024132994b9070c7be72b5.parquet
     27239 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194271-194789.84e438e287ae4dc58c90a247733bc507.parquet
    101616 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194271-194789.4b1ce447a3cb482e9ecac5ae4c2a1518.parquet
    105864 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194790-195398.a91bf258aa7b4c3fb7f81cad86594243.parquet
     21086 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194790-195398.49c3ed3774804c8ba892b840b8e4804f.parquet
     85146 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_195399-195841.d75589d1d3e24242be17082a013c47a2.parquet
     29111 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_195399-195841.a2906dbe00cd4ac88425c4735b3f43f7.parquet
     74400 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_195842-196531.5e8f8fa5d9314a31af54c22c20453151.parquet
    103831 events -> /project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_195842-196531.06d2ffcf22594d159918439b879fc1ba.parquet
    11 final results, 776189 events in the skim
    </div>

    Every group of 10 partial results covered up to 500,000 events, well over
    `is_result`'s 50,000, so each of them became a final result on the spot
    (`result ... (final)`), and what was left of each dataset was folded by one
    more, forced `final` reduction. Thus the run produces **11 final
    results** rather than one per dataset, and 11 parquet files: two or three for each dataset. Of
    the 3,736,416 events, **776,189** have a best trijet between 150
    and 195 GeV. (The coffea flavor finds 776,186: a few events lie very close to the
    edges of the window, where the two flavors' floating-point rounding can
    disagree.) The file sizes differ because each file is a different slice of
    the data. Further, all 11 final reductions wrote their files on the workers, and
    none of the events came back through this terminal. Note that a reducer's `memory_mb` is far below
    a processor's, since it never loads ROOT.

    *The RDataFrame output on this page was captured with a local worker of the same size as the pool's (4 cores, 8064 MB), rather than on the pool itself, so your hosts and timings will differ.*

## What's on the manager's side

=== "coffea"

    ```bash
    ls results/SingleMu_Run2012B_194271-194789/skim/
    ```

    ```
    skim__1fa576b5b5924f43ac49e06908cc7864.pointer.json
    skim__3930d8fff44d426188f43cfb0331c447.pointer.json
    skim__831fe1d4e3ce460897672e6489a347cd.pointer.json
    ```

    There is no `*.pkl.zst` this time, only one small pointer file per final
    result, in each dataset's own directory (this dataset has 3).

    ```bash
    cat results/SingleMu_Run2012B_194271-194789/skim/skim__1fa576b5b5924f43ac49e06908cc7864.pointer.json
    ```

    ```json
    {
      "offloaded": true,
      "processor_name": "skim",
      "dataset_name": "SingleMu_Run2012B_194271-194789",
      "locator": {
        "path": "/project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194271-194789.22bad5ac4d604a428acfe8cecb3fadca.parquet",
        "events": 104495
      }
    }
    ```

    VineReduce wraps whatever `result_postprocess` returned (`locator`) with
    the pipeline it came from. This is everything the manager ever held for
    this skim, and also everything a later step needs to find and read the
    data.

=== "RDataFrame"

    ```bash
    ls results/SingleMu_Run2012B_194271-194789/skim/
    ```

    ```
    skim__60938e7a51974c19a5b424b33327f91b.pointer.json
    skim__b233318ea4994b38802196514853db74.pointer.json
    skim__b2d49b42c44c44a687fae5a827fbff5d.pointer.json
    ```

    There is no `*.pkl.zst` this time, only one small pointer file per final
    result, in each dataset's own directory (this dataset has 3).

    ```bash
    cat results/SingleMu_Run2012B_194271-194789/skim/skim__60938e7a51974c19a5b424b33327f91b.pointer.json
    ```

    ```json
    {
      "offloaded": true,
      "processor_name": "skim",
      "dataset_name": "SingleMu_Run2012B_194271-194789",
      "locator": {
        "path": "/project01/ndcms/users/btovar/trijet-skims/SingleMu_Run2012B_194271-194789.253b21ea0c024132994b9070c7be72b5.parquet",
        "events": 98205
      }
    }
    ```

    VineReduce wraps whatever `result_postprocess` returned (`locator`) with
    the pipeline it came from. This is everything the manager ever held for
    this skim, and also everything a later step needs to find and read the
    data.

## What's on `/project01`

=== "coffea"

    The skim itself is on shared storage. From the login node:

    ```bash
    ls -lgo /project01/ndcms/users/$USER/trijet-skims/
    ```

    ```
    total 108940
    -rw-r--r-- 1 10897674 Oct 02 17:15 SingleMu_Run2012B_193834-194270.628e1ba07e4444edb3c4d91f3e73b974.parquet
    -rw-r--r-- 1  7176090 Oct 02 17:15 SingleMu_Run2012B_193834-194270.d293f06c26b34a6881ef56cacb6479f4.parquet
    -rw-r--r-- 1 15259609 Oct 02 17:15 SingleMu_Run2012B_194271-194789.22bad5ac4d604a428acfe8cecb3fadca.parquet
    -rw-r--r-- 1  2610537 Oct 02 17:15 SingleMu_Run2012B_194271-194789.3baf79829f824684a95aed90c7f4bfff.parquet
    -rw-r--r-- 1 14898298 Oct 02 17:15 SingleMu_Run2012B_194271-194789.f29ed1a0abe944db967f5aaa56039250.parquet
    -rw-r--r-- 1 15550490 Oct 02 17:15 SingleMu_Run2012B_194790-195398.1a9f144626af4f4eb419cc4e42e77ad1.parquet
    -rw-r--r-- 1  2716659 Oct 02 17:15 SingleMu_Run2012B_194790-195398.3f7e0817258a44b49ca1384db2c09200.parquet
    -rw-r--r-- 1  4355176 Oct 02 17:15 SingleMu_Run2012B_195399-195841.3dbcdfeebd3242a2b45106904efff75f.parquet
    -rw-r--r-- 1 12376975 Oct 02 17:15 SingleMu_Run2012B_195399-195841.bcf1498ba042400da20e05c8bcf0ef3e.parquet
    -rw-r--r-- 1 15726664 Oct 02 17:15 SingleMu_Run2012B_195842-196531.885b37f41b764cbbb7a3af8bf3e3821d.parquet
    -rw-r--r-- 1  9965454 Oct 02 17:15 SingleMu_Run2012B_195842-196531.e1e6b2219d0d4b3cba1fc6847e1a513d.parquet
    ```

    That is 11 files, about 112 MB in total. At this size it perhaps wouldn't
    have mattered much where they were written; however, the pattern is the
    same when the skim is hundreds of gigabytes, as the manager only ever
    handles the 11 one-line pointers.

=== "RDataFrame"

    The skim itself is on shared storage. From the login node:

    ```bash
    ls -lgo /project01/ndcms/users/$USER/trijet-skims/
    ```

    ```
    total 114988
    -rw-r--r-- 1  7581561 Oct 02 17:16 SingleMu_Run2012B_193834-194270.87dd1353bb14470684ccf368d04a7db0.parquet
    -rw-r--r-- 1 11520287 Oct 02 17:16 SingleMu_Run2012B_193834-194270.d9e238285510447e9bc0658a7508ba5a.parquet
    -rw-r--r-- 1 14752072 Oct 02 17:17 SingleMu_Run2012B_194271-194789.253b21ea0c024132994b9070c7be72b5.parquet
    -rw-r--r-- 1 15709460 Oct 02 17:16 SingleMu_Run2012B_194271-194789.4b1ce447a3cb482e9ecac5ae4c2a1518.parquet
    -rw-r--r-- 1  4120557 Oct 02 17:17 SingleMu_Run2012B_194271-194789.84e438e287ae4dc58c90a247733bc507.parquet
    -rw-r--r-- 1  2884450 Oct 02 17:17 SingleMu_Run2012B_194790-195398.49c3ed3774804c8ba892b840b8e4804f.parquet
    -rw-r--r-- 1 16396351 Oct 02 17:17 SingleMu_Run2012B_194790-195398.a91bf258aa7b4c3fb7f81cad86594243.parquet
    -rw-r--r-- 1  4581872 Oct 02 17:17 SingleMu_Run2012B_195399-195841.a2906dbe00cd4ac88425c4735b3f43f7.parquet
    -rw-r--r-- 1 13054138 Oct 02 17:17 SingleMu_Run2012B_195399-195841.d75589d1d3e24242be17082a013c47a2.parquet
    -rw-r--r-- 1 15929778 Oct 02 17:18 SingleMu_Run2012B_195842-196531.06d2ffcf22594d159918439b879fc1ba.parquet
    -rw-r--r-- 1 11193755 Oct 02 17:18 SingleMu_Run2012B_195842-196531.5e8f8fa5d9314a31af54c22c20453151.parquet
    ```

    That is 11 files, about 118 MB in total. At this size it perhaps wouldn't
    have mattered much where they were written; however, the pattern is the
    same when the skim is hundreds of gigabytes, as the manager only ever
    handles the 11 one-line pointers.

!!! note "The skim directory keeps growing"
    Every run adds new files (new uuids) next to the old ones.
    `results/` is wiped at the start of each run, but
    `/project01/.../trijet-skims/` is not. Clean it up yourself between
    attempts: `rm /project01/ndcms/users/$USER/trijet-skims/*.parquet`.

When you're done, stop the factory with Ctrl-C and check `condor_q`, as
in [Module 4](module-04-scale-out.md#clean-up-after-yourself).
