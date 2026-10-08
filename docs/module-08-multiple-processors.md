# Module 8 - Multiple processors

**10 min**

A real analysis rarely runs a single selection. For example, you may scan a
cut, compare working points, or run signal and control regions side by
side. With VineReduce, such variations are simply more entries in the
`processors={...}` dict, and nothing else changes.

## What changed in the script

This module's script (`scripts/vr_trijet_windows.py`, or
`scripts/vr_trijet_windows_rdf.py`) is Module 4's (`vr_trijet_condor.py`, or
`vr_trijet_condor_rdf.py`; same real data, same named manager, same packed
environment) with one idea added: it keeps only the events whose best trijet
mass is near the top quark mass, for three different window sizes. Everything
below is shown as a diff against Module 4.

## A family of processors

=== "coffea"

    ```diff
    +TOP_MASS = 172.5
    +
    +# processor name -> half-width of the mass window, in GeV
    +MASS_WINDOWS = {
    +    "trijet_pm10": 10,
    +    "trijet_pm25": 25,
    +    "trijet_pm50": 50,
    +}
    +
    +
    +def make_trijet_processor(window):
    +    def trijet_processor(events):
    -def trijet_processor(events):
             ...  # Module 4's trijet selection, then:
    +        # the only new line: keep trijets inside this processor's window
    +        trijet = trijet[abs(trijet.p4.mass - TOP_MASS) < window]
             ...  # fill the same two histograms
    +
    +    return trijet_processor
    ```

    (The body of `trijet_processor` is indented one more level to sit inside
    `make_trijet_processor`; apart from that and the new line, it is Module 4's
    function.) `make_trijet_processor(window)` builds a new processor each
    time it's called, with its own `window` baked in. All three processors
    then go into one `VineReduceCoffea` call:

    ```diff
     vr = VineReduceCoffea(
    -    processors={"trijet": trijet_processor},
    +    processors={
    +        name: make_trijet_processor(window) for name, window in MASS_WINDOWS.items()
    +    },
         input=datasets_path,
         ...
     )
    ```

=== "RDataFrame"

    ```diff
    +TOP_MASS = 172.5
    +
    +# processor name -> half-width of the mass window, in GeV
    +MASS_WINDOWS = {
    +    "trijet_pm10": 10,
    +    "trijet_pm25": 25,
    +    "trijet_pm50": 50,
    +}
    +
    +
    +def make_trijet_processor(window):
    +    def trijet_processor(df):
    -def trijet_processor(df):
             ...  # compile `BestTrijet`, as in Module 4, then:
             best = (
                 df.Filter("nJet >= 3")
                 .Define("best", "BestTrijet(Jet_pt, Jet_eta, Jet_phi, Jet_mass, Jet_btag)")
    +            # the only new line: keep trijets inside this processor's window
    +            .Filter(f"abs(best[2] - {TOP_MASS}) < {window}")
                 ...
             )
             ...  # fill the same two histograms
    +
    +    return trijet_processor
    ```

    (The body of `trijet_processor` is indented one more level to sit inside
    `make_trijet_processor`; apart from that and the new line, it is Module 4's
    function.) `make_trijet_processor(window)` builds a new processor each
    time it's called, with its own `window` baked in (`best[2]` is the best
    trijet's mass). All three processors then go into one `VineReduce` call:

    ```diff
     vr = VineReduce(
    -    processors={"trijet": trijet_processor},
    +    processors={
    +        name: make_trijet_processor(window) for name, window in MASS_WINDOWS.items()
    +    },
         input=datasets_path,
         ...
     )
    ```

VineReduce builds one **pipeline** per (processor, dataset) pair, thus 3
processors x 5 datasets = 15 pipelines. Each pipeline has its own chunks, its
own reductions, and its own final result under
`results/<dataset name>/<processor name>/`. All fifteen run at the same time, on
the same manager and the same workers.

## Run it

Use the same two terminals as in [Module 4](module-04-scale-out.md).

**Terminal 1:**

=== "coffea"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_windows.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_windows.py
        ```

=== "RDataFrame"

    === "Option A: conda"

        ```bash
        conda activate vine-cms-analysis-stack
        python scripts/vr_trijet_windows_rdf.py
        ```

    === "Option B: pixi"

        ```bash
        pixi run python scripts/vr_trijet_windows_rdf.py
        ```

**Terminal 2**, the same factory command as Module 4:

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

!!! note "Still have Module 7's `factory.json`?"
    If you did [Module 7](module-07-result-postprocess.md), your
    `factory.json` still has its `condor-requirements` line. It is harmless
    here — it only narrows which nodes your 2 workers land on. Delete the
    line to use the whole pool, since nothing in this module writes to
    `/project01`.

=== "coffea"

    Once the workers arrived, this run took about a minute:

    <div class="term">
    ...
    <span class="t-green">success             </span> final     trijet_pm10/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=180f1889) cores=1(1) memory_mb=202(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> final     trijet_pm25/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=c1ecbb6a) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> processor trijet_pm50/SingleMu_Run2012B_195842-196531 ...2-196531/file_2.root[0:99449] (id=68b6219b) cores=1(1) memory_mb=438(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> final     trijet_pm50/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=2e456fbb) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    trijet_pm10 [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">44</span>/<span class="t-red">0</span>/<span class="t-blue">44</span>
    reductions  [ <span class="t-green">██████████████████████████████</span> ]                      <span class="t-yellow">6</span>/<span class="t-red">0</span>/<span class="t-blue">6</span>
    events      [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets    [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>

    trijet_pm25 [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">44</span>/<span class="t-red">0</span>/<span class="t-blue">44</span>
    reductions  [ <span class="t-green">██████████████████████████████</span> ]                      <span class="t-yellow">6</span>/<span class="t-red">0</span>/<span class="t-blue">6</span>
    events      [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets    [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>

    trijet_pm50 [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">44</span>/<span class="t-red">0</span>/<span class="t-blue">44</span>
    reductions  [ <span class="t-green">██████████████████████████████</span> ]                      <span class="t-yellow">6</span>/<span class="t-red">0</span>/<span class="t-blue">6</span>
    events      [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets    [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>
    trijet_pm10 (|m - 172.5| < 10 GeV): 578860 entries
    trijet_pm25 (|m - 172.5| < 25 GeV): 804801 entries
    trijet_pm50 (|m - 172.5| < 50 GeV): 1021537 entries
    </div>

=== "RDataFrame"

    Once the workers arrived, this run took about three and a half minutes:

    <div class="term">
    ...
    <span class="t-green">success             </span> final     trijet_pm10/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=d175b973) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> final     trijet_pm25/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=2958d19a) cores=1(1) memory_mb=201(2016) wall_time_s=1(0)
    <span class="t-green">success             </span> processor trijet_pm50/SingleMu_Run2012B_195842-196531 ...2-196531/file_2.root[0:99449] (id=09217da6) cores=1(1) memory_mb=879(2016) wall_time_s=6(0)
    <span class="t-green">success             </span> final     trijet_pm50/SingleMu_Run2012B_195842-196531 reduction of 9 partials (final) (id=2096c766) cores=1(1) memory_mb=202(2016) wall_time_s=1(0)
    trijet_pm10 [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">44</span>/<span class="t-red">0</span>/<span class="t-blue">44</span>
    reductions  [ <span class="t-green">██████████████████████████████</span> ]                      <span class="t-yellow">6</span>/<span class="t-red">0</span>/<span class="t-blue">6</span>
    events      [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets    [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>

    trijet_pm25 [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">44</span>/<span class="t-red">0</span>/<span class="t-blue">44</span>
    reductions  [ <span class="t-green">██████████████████████████████</span> ]                      <span class="t-yellow">6</span>/<span class="t-red">0</span>/<span class="t-blue">6</span>
    events      [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets    [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>

    trijet_pm50 [ <span class="t-green">██████████████████████████████</span> ]                    <span class="t-yellow">44</span>/<span class="t-red">0</span>/<span class="t-blue">44</span>
    reductions  [ <span class="t-green">██████████████████████████████</span> ]                      <span class="t-yellow">6</span>/<span class="t-red">0</span>/<span class="t-blue">6</span>
    events      [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">3736416</span>(<span class="t-green">3736416</span>)/<span class="t-red">0</span>/<span class="t-blue">3736416</span>
    datasets    [ <span class="t-green">██████████████████████████████</span> ]                        <span class="t-green">5</span>/<span class="t-cyan">5</span>
    trijet_pm10 (|m - 172.5| < 10 GeV): 578859 entries
    trijet_pm25 (|m - 172.5| < 25 GeV): 804800 entries
    trijet_pm50 (|m - 172.5| < 50 GeV): 1021536 entries
    </div>

    *The RDataFrame output on this page was captured with a local worker of the same size as the pool's (4 cores, 8064 MB), rather than on the pool itself, so your hosts and timings will differ.*

There is one set of four bars **per processor**, as each processor's five
pipelines read all 3,736,416 events in 44 chunks and did their own six
reductions. The task lines interleave; in particular, `trijet_pm50` chunks were still finishing after
`trijet_pm10` and `trijet_pm25` were done, which is simply the three
pipelines sharing the same 2 workers.

The counts nest, as they should, given that every event within 10 GeV is
also within 25 GeV, and so on. For comparison, Module 4, with no window at
all, had 1,697,939. This is a small but useful sanity check whenever
you run a family of cuts like this one. (The two flavors differ by one entry
in each window: 578,860 with coffea against 578,859 with RDataFrame for
±10 GeV, and so on. An event that sits at the edge of a window is decided
by floating-point rounding, which the two implementations do differently.)

!!! note "Adding a fourth window"
    Another window is one more entry in `MASS_WINDOWS` (for example,
    `"trijet_pm5": 5`), with no other change to the script: you would get a
    fourth set of bars and a fourth line at the end.
