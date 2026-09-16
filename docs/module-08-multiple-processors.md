# Module 8 - Multiple processors

**10 min**

A real analysis rarely runs a single selection. For example, you may scan a
cut, compare working points, or run signal and control regions side by
side. With VineReduce, such variations are simply more entries in the
`processors={...}` dict, and nothing else changes.

## Get the script

```bash
curl -sL -o scripts/vr_trijet_windows.py \
  https://raw.githubusercontent.com/cooperative-computing-lab/vine-cms-analysis-stack-tutorials/main/scripts/vr_trijet_windows.py
```

This is Module 4's `vr_trijet_condor.py` (same real data, same named
manager, same packed environment) with one idea added: it keeps only the
events whose best trijet mass is near the top quark mass, for three
different window sizes.

## A family of processors

```python
TOP_MASS = 172.5

# processor name -> half-width of the mass window, in GeV
MASS_WINDOWS = {
    "trijet_pm10": 10,
    "trijet_pm25": 25,
    "trijet_pm50": 50,
}


def make_trijet_processor(window):
    def trijet_processor(events):
        ...  # Module 4's trijet selection, then:
        # the only new line: keep trijets inside this processor's window
        trijet = trijet[abs(trijet.p4.mass - TOP_MASS) < window]
        ...  # fill the same two histograms
    return trijet_processor
```

`make_trijet_processor(window)` builds a new processor each time it's
called, with its own `window` baked in. All three processors then go into
one `VineReduceCoffea` call:

```python
vr = VineReduceCoffea(
    processors={
        name: make_trijet_processor(window) for name, window in MASS_WINDOWS.items()
    },
    input=datasets_path,
    ...
)
```

VineReduce builds one **pipeline** per (processor, dataset) pair, thus 3
processors x 1 dataset = 3 pipelines. Each pipeline has its own chunks, its
own reductions, and its own final result under
`results/SingleMu/<processor name>/`. All three run at the same time, on
the same manager and the same workers.

## Run it

Use the same two terminals as in [Module 4](module-04-scale-out.md).

**Terminal 1:**

=== "Option A: conda"

    ```bash
    conda activate vine-cms-analysis-stack
    python scripts/vr_trijet_windows.py
    ```

=== "Option B: pixi"

    ```bash
    pixi run python scripts/vr_trijet_windows.py
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

Once the workers arrived, this run took under a minute and a half:

<div class="term">
...
<span class="t-green">success             </span> final     trijet_pm10/SingleMu reduction of 5 partials (final) (id=c6e47d96) cores=1(1) memory_mb=190(2016) wall_time_s=1(0)
<span class="t-green">success             </span> final     trijet_pm25/SingleMu reduction of 5 partials (final) (id=587b5ee6) cores=1(1) memory_mb=191(2016) wall_time_s=1(0)
<span class="t-green">success             </span> processor trijet_pm50/SingleMu ...n2012B_SingleMu.root[400000:500000] (id=9f91db2f) cores=1(1) memory_mb=518(2016) wall_time_s=4(0)
<span class="t-green">success             </span> final     trijet_pm50/SingleMu reduction of 5 partials (final) (id=760636ee) cores=1(1) memory_mb=190(2016) wall_time_s=1(0)
trijet_pm10 [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">5</span>/<span class="t-red">0</span>/<span class="t-blue">5</span>
reductions  [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
events      [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">500000</span>(<span class="t-green">500000</span>)/<span class="t-red">0</span>/<span class="t-blue">500000</span>
datasets    [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>

trijet_pm25 [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">5</span>/<span class="t-red">0</span>/<span class="t-blue">5</span>
reductions  [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
events      [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">500000</span>(<span class="t-green">500000</span>)/<span class="t-red">0</span>/<span class="t-blue">500000</span>
datasets    [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>

trijet_pm50 [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">5</span>/<span class="t-red">0</span>/<span class="t-blue">5</span>
reductions  [ <span class="t-green">██████████████████████████████</span> ]                   <span class="t-yellow">1</span>/<span class="t-red">0</span>/<span class="t-blue">1</span>
events      [ <span class="t-green">██████████████████████████████</span> ] <span class="t-yellow">500000</span>(<span class="t-green">500000</span>)/<span class="t-red">0</span>/<span class="t-blue">500000</span>
datasets    [ <span class="t-green">██████████████████████████████</span> ]                     <span class="t-green">1</span>/<span class="t-cyan">1</span>
trijet_pm10 (|m - 172.5| < 10 GeV): 74334 entries
trijet_pm25 (|m - 172.5| < 25 GeV): 103191 entries
trijet_pm50 (|m - 172.5| < 50 GeV): 130999 entries
</div>

There is one set of four bars **per processor**, as each pipeline read all
500,000 events in 5 chunks and did its own final reduction. The task lines
interleave; in particular, `trijet_pm50` chunks were still finishing after
`trijet_pm10` and `trijet_pm25` were done, which is simply the three
pipelines sharing the same 2 workers.

The counts nest, as they should, given that every event within 10 GeV is
also within 25 GeV, and so on. For comparison, Module 4, with no window at
all, had 217,890. This is a small but useful sanity check whenever
you run a family of cuts like this one.

!!! question "Try it"
    Add a fourth entry, e.g. `"trijet_pm5": 5`, to `MASS_WINDOWS` and
    rerun. You get a fourth set of bars and a fourth line at the end, with
    no other change to the script.
