# Appendix

Reference material, not counted in the 180 live-taught minutes.

## conda vs. pixi differences

Both options install the same conda-forge environment; pixi, however, also
installs this repo's own code from PyPI/editable automatically.

This matters because `vine_reduce.get_environment()` packs whatever is in
`$CONDA_PREFIX`. It transparently repacks an *editable* install for the
pack step (temporarily non-editable, then back), but only for packages it
is told to watch, that is, `vine_reduce` itself by default, plus anything
named in `pip_editable={...}`.

Under pixi, this repo's own editable install happens automatically
(`[tool.pixi.pypi-dependencies]`), whereas `environment.yml` does not
install it. Today's modules don't need it: `vine-cms-analysis-stack`
declares no Python packages of its own (`packages = []`), and the tutorial
scripts only import `vine_reduce`, `coffea`, ROOT, and their dependencies.
Thus, Module 1's conda steps are complete as they are.

It matters, however, once your own analysis code lives in this repo as an
installable package that your processor imports. Under plain conda
(Option A), you must then `pip install -e .` this repo yourself first.
Otherwise, `get_environment()` ships a worker environment missing your own
code, and the failure mode (stale or missing code at the worker) is silent
until something breaks remotely.

Further, pass `pip_editable={"vine-cms-analysis-stack": ["examples",
"pyproject.toml"]}` so that uncommitted changes to *this* repo's checkout
(as opposed to only `vine_reduce`'s, which is watched by default) also
force a rebuild, rather than silently shipping stale code.

## coffea vs. RDataFrame differences

The two flavors compute the same thing, and on today's data they agree. The
entry counts are identical in Modules 2, 3, 4, and 9 (1,697,939 over the five
datasets, 289,270 / 497,298 / 276,498 / 247,576 / 387,297 for each) and in
Module 5 (206,251). The histograms agree bin for bin apart from a few dozen
events: roughly 45 of the 1.7 million events land one bin over in the trijet pT
histograms, and roughly 22 in the b-tag ones. Where a selection has a hard edge, the
flavors can differ by an event or two: the mass windows of Module 8 (578,860
with coffea against 578,859 with RDataFrame for ±10 GeV) and the skim of
Module 7 (776,186 events against 776,189). That is the size of difference to
expect from two implementations that round differently. Beyond that, they
differ in these ways:

- **What you write.** Under coffea, the processor is awkward-array code.
  Under RDataFrame, it is a short piece of C++ (`BestTrijet`, compiled by
  ROOT's interpreter) plus a `Filter`/`Define`/`Histo1D` chain in Python.
  The RDataFrame scripts also spell out `chunk_to_args`, which turns a chunk
  (a file and an entry range) into `ROOT.RDataFrame(...).Range(start,
  stop)`; `VineReduceCoffea` supplies the coffea equivalent for you, which
  is why the RDataFrame scripts use plain `VineReduce`.
- **Memory.** A coffea call needs memory in proportion to its chunk (1,837
  MB for the 430,713-event file of Module 5, 615 MB for 107,678 events). An
  RDataFrame call needs about 1,050 MB whatever the chunk size, because it
  streams through the entries, and ROOT's start-up and compilation of
  `BestTrijet` take about 750 MB of that. Thus, [Module
  5](module-05-resources.md) plays out differently: halving the chunk
  cannot rescue a limit below that floor.
- **Start-up cost.** Every RDataFrame call compiles `BestTrijet`, which
  takes about 5 seconds. With `LocalDistributor`, a worker process does so
  once and reuses it; with TaskVine, every task is a new process, so every
  task pays. Larger chunks amortize it better.
- **Histograms.** The processor returns `hist.Hist` objects rather than
  ROOT's `TH1D`. The reason is pickling: a `TH1D` that has been unpickled
  in a fresh process cannot be pickled again until that process has
  created a histogram of its own, and every reducer call under TaskVine is
  such a process. The scripts therefore copy each histogram into a
  `hist.Hist` (`to_hist`) before returning it, which also makes results
  files, `load_result`, and the reducer identical for the two flavors.
- **Skims.** An RDataFrame skim goes through `ak.from_rdataframe`, so
  [Module 7](module-07-result-postprocess.md)'s reducer and
  `result_postprocess` are the same for both flavors.
- **Dataset files.** The RDataFrame scripts read the same
  `datasets_*.json` files, through `coffea_input_to_datasets`, which is why
  coffea stays installed in an environment used only for RDataFrame.
- **Failures.** A missing file fails in `ROOT.RDataFrame(...)`, and PyROOT's
  error message lists every constructor it tried before giving the reason
  at the end (`could not open file`). It is a long traceback in
  `failed_files.log`, but the same failure as in the coffea flavor.

## `ttbarEFT` reference walkthrough (read, don't run)

`examples/ttBar/run_processor_with_vr.py` hard-requires an X509 proxy,
TopEFT's own Wilson-coefficient sample metadata, and a manager waiting on
independently-launched cluster workers, with no local-factory fallback.
Given these requirements, it was confirmed not adaptable into a runnable
15-30 min segment without someone on TopEFT providing a small public EFT
sample + WC list in advance. Therefore, use it only as a "this is what a
full production analysis looks like on top of the same API" slide.

## About the tutorial dataset

Every module runs on real CMS Open Data: the first 3 files of each of 5
datasets, taken from the `Run2012B_SingleMu` open-data file that IRIS-HEP's
ADL benchmarks (the source of the stack's `trijet_processor`) run over. That
is 15 ROOT files and 3,736,416 events. The files are not generated or built
live: they were split out ahead of time, with a fixed seed so the split is
reproducible.

Both manifests use coffea's minimal preprocessed shape
(`{name: {"metadata": {...}, "files": {path: {"object_path": "Events",
"num_entries": N}}}}`) and list the same files, so they are interchangeable
without any change to the processor code; the only thing that changes is
which manifest a script loads. The RDataFrame scripts read the very same
files.

1. **`data/datasets_vast.json`**: the files on VAST,
   `/project01/ndcms/btovar/tutorial/tutorial/SingleMu_Run2012B/<dataset>/file_<i>.root`
   (absolute paths, world-readable). Modules
   [2](module-02-local-distributor.md), [3](module-03-local-factory.md),
   [6](module-06-checkpoints-restart.md), and
   [9](module-09-failure-proportion.md) run on the login node and read these.
2. **`data/datasets_xrootd.json`**: the same files as
   `root://cmsxrootd.crc.nd.edu//store/user/btovar/tutorial/SingleMu_Run2012B/<dataset>/file_<i>.root`,
   with no grid proxy needed. Modules [4](module-04-scale-out.md),
   [5](module-05-resources.md), [7](module-07-result-postprocess.md), and
   [8](module-08-multiple-processors.md) run on HTCondor pool nodes and read
   these; Module 5 uses just one of the 15 files.

The five dataset names (`SingleMu_Run2012B_193834-194270`, ...) are styled
after real CMS run-range dataset splits, but are illustrative only: each
file's events were picked by position in the source file, not by any event's
actual run number, so a name's range isn't a claim about what's really inside
that dataset. The full split has 205 files and all 53,446,198 events.
