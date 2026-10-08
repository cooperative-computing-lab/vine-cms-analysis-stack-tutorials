# TaskVine / VineReduce / vine-cms-analysis-stack

This is a 3-hour hands-on tutorial for HEP graduate students.

**Audience:** students comfortable with a terminal, Python, and an editor;
no background with TaskVine, coffea, or HTCondor is assumed.

**Two flavors:** the analysis is written both with coffea and with ROOT's
RDataFrame, and you choose the one you prefer. Wherever the two differ, a
page shows `coffea` and `RDataFrame` tabs, and a click on one switches every
other such tab on the site. Everything else, namely VineReduce, TaskVine,
the factory, and the pool, is shared between them. [Module
1](module-01-setup.md#pick-your-analysis-flavor) says more.

**Format:** Software-Carpentries style, that is, a short framing followed
by live-coding along, in short build-run-break-fix cycles. This comes to
~15 min of lecture and ~165 min hands-on (see the
[timing table](#timing-table)).

!!! warning "Prerequisite check (send before the session, not done live)"
    - A glados account
    - conda (or pixi) working
    - `cooperative-computing-lab/vine-cms-analysis-stack` cloned and its
      environment created ([Module 1](module-01-setup.md))
    - A choice of analysis flavor, coffea or RDataFrame (both are in the
      environment; see below)

    Given that you are reading this tutorial from the web, there is nothing
    else to clone. Every module's script and the dataset manifests are
    already in your `vine-cms-analysis-stack` clone, under
    `examples/tutorial_nd/`.

## Learning objectives

By the end, a student can:

1. Explain the distributor/executor split and why VineReduce separates
   chunking/reduction logic from cluster execution.
2. Run an analysis, written with coffea or with RDataFrame, locally
   (`LocalDistributor`), then on a local TaskVine worker, then on a real
   HTCondor pool, with the same processor code each time.
3. Package a conda environment for remote workers and explain why that is
   needed once workers aren't on the same machine or filesystem.
4. Read a run's health from both the live console and the on-disk logs.
5. Tune (and autotune) chunk/reduction size and resource declarations, and
   explain what changes when they're wrong.
6. Explain checkpointing and demonstrate restart-without-redoing-work.
7. Write a `result_postprocess` that ships large results out of band
   rather than pickling them through the manager.
8. Run several processors over the same datasets in one job.
9. Explain and demonstrate `failure_proportion`.
10. Know where to ask for help afterward.

## Infrastructure plan

!!! info "Decide/confirm before the session - not a student task"
    - **Shared vine_catalog**: reuse ND's real catalog
      (`catalog.cse.nd.edu`, `backup-catalog.cse.nd.edu`, the same servers
      `examples/scale-cortado`'s workers already report to — they are baked
      into the worker command line in the factory's generated
      `vine-factory-*/condor.submit`), rather than standing up a new
      catalog instance for the class.
    - **Shared HTCondor pool**: glados' real pool, where the factory submits
      worker jobs via `batch_type="condor"`, with
      `vine-factory-*/condor.submit` as the template. Each student's factory
      dispatches into this same pool.
    - **Per student**: their own `vine.Manager`/`TaskVineDistributor` (with
      its own port) and their own `vine_factory` process, named uniquely so
      that the catalog and `vine_status` can tell students' runs apart. The
      proposed convention is manager name `<netid>-trijet-tutorial` and
      factory `-M '<netid>-trijet-tutorial'`.

!!! info "Decided"
    - **Per-student worker cap**, in each student's `factory.json`: at most
      2 workers, 4 cores, 8000 MB memory, and 16000 MB disk each
      (`--single-shot`, `timeout` 300 s, `factory-timeout` 120 s).
    - **`condor-requirements`**: none for Modules 4, 5, and 8. Module 7 adds
      `(has_vast)` so that workers can write to `/project01` on the CRC
      pool. On glados (T3), however, leave it out, since every worker there
      has VAST.

!!! danger "TODO before the session"
    Confirm that the `<netid>-trijet-tutorial` naming convention does not
    collide with other CCL or production use of the same catalog, and get a
    headcount to check that 2 workers per student is sane for the pool
    under class load.

## Dataset plan: real data, two manifests

Every module runs on real CMS Open Data: the first 3 files of each of 5
datasets, taken from the `Run2012B_SingleMu` open-data file that IRIS-HEP's
ADL benchmarks (the source of this repo's `trijet_processor`) run over. That is
15 ROOT files and 3,736,416 events. The files are not generated or built live:
they were split out ahead of time by `scripts/make_real_scale_data.py` (seeded,
so the split is reproducible) and are read in two ways, each with its own
manifest.

Both manifests use coffea's minimal preprocessed shape
(`{name: {"metadata": {...}, "files": {path: {"object_path": "Events",
"num_entries": N}}}}`), and list the same files, so they are interchangeable
without any change to the processor code; the only thing that changes is
which manifest a script loads. The RDataFrame scripts read the very same
files.

1. **`data/datasets_vast.json`**: the files on VAST,
   `/project01/ndcms/btovar/store/user/btovar/tutorial/SingleMu_Run2012B/<dataset>/file_<i>.root`
   (absolute paths, world-readable). The local Modules
   [2](module-02-local-distributor.md), [3](module-03-local-factory.md),
   [6](module-06-checkpoints-restart.md), and
   [9](module-09-failure-proportion.md) run on the login node and read these.
2. **`data/datasets_xrootd.json`**: the same files as
   `root://cmsxrootd.crc.nd.edu//store/user/btovar/tutorial/SingleMu_Run2012B/<dataset>/file_<i>.root`,
   with no grid proxy needed (checked from the login node). Modules
   [4](module-04-scale-out.md), [5](module-05-resources.md),
   [7](module-07-result-postprocess.md), and
   [8](module-08-multiple-processors.md) run on HTCondor pool nodes, and read
   these; Module 5 uses just one of the 15 files.

The five dataset names (`SingleMu_Run2012B_193834-194270`, ...) are styled
after real CMS run-range dataset splits, but are illustrative only: each
file's events were picked by position in the source file, not by any event's
actual run number, so a name's range isn't a claim about what's really inside
that dataset. The full split (205 files, all 53,446,198 events) is described in
[Module 10](module-10-wrapup.md).

## Timing table

| # | Module | Minutes |
|---|---|---|
| 0 | [Intro / motivation (lecture)](module-00-intro.md) | 15 |
| 1 | [Setup & verify](module-01-setup.md) | 15 |
| 2 | [Local distributor: map/reduce concepts](module-02-local-distributor.md) | 15 |
| 3 | [Local TaskVine factory](module-03-local-factory.md) | 20 |
| 4 | [Scale out: packaging, catalog, condor, certs, real data](module-04-scale-out.md) | 30 |
| 5 | [Resources & chunk/reduction size](module-05-resources.md) | 15 |
| 6 | [Checkpoints & restart](module-06-checkpoints-restart.md) | 20 |
| 7 | [Shipping results out: `result_postprocess`](module-07-result-postprocess.md) | 15 |
| 8 | [Multiple processors](module-08-multiple-processors.md) | 10 |
| 9 | [`failure_proportion`](module-09-failure-proportion.md) | 15 |
| 10 | [Wrap-up / where to get help](module-10-wrapup.md) | 10 |
| | **Total** | **180** |

Reference material that is not counted in the 180 minutes lives in the
[Appendix](appendix.md).
