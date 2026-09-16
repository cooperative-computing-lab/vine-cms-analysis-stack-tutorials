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
declares no Python packages of its own (`packages = []`), the tutorial
scripts only import `vine_reduce`, `coffea`, and their dependencies, and
`make_synthetic_data.py` runs `examples/write_test_data.py` by path. Thus,
Module 1's conda steps are complete as they are.

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

## `ttbarEFT` reference walkthrough (read, don't run)

`examples/ttBar/run_processor_with_vr.py` hard-requires an X509 proxy,
TopEFT's own Wilson-coefficient sample metadata, and a manager waiting on
independently-launched cluster workers, with no local-factory fallback.
Given these requirements, it was confirmed not adaptable into a runnable
15-30 min segment without someone on TopEFT providing a small public EFT
sample + WC list in advance. Therefore, use it only as a "this is what a
full production analysis looks like on top of the same API" slide.
