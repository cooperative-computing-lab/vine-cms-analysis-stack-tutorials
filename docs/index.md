# TaskVine / VineReduce / vine-cms-analysis-stack

A 3-hour hands-on tutorial for HEP graduate students. You take one real CMS
analysis from a single process on a login node, to a TaskVine worker on the
same machine, to an HTCondor pool, while the processor code stays the same
each time. Along the way you learn to read a run's health, tune it, restart
it without redoing work, and keep it going when some chunks fail.

[Start: Module 0 - Intro](module-00-intro.md){ .md-button .md-button--primary }
[Set up before the session](module-01-setup.md){ .md-button }

## Who this is for

Students comfortable with a terminal, Python, and an editor. No background
with TaskVine, coffea, or HTCondor is assumed.

!!! warning "Before the session"
    Do these ahead of time; they are not done live:

    - Have a glados account.
    - Have conda or pixi working.
    - Clone `cooperative-computing-lab/vine-cms-analysis-stack` and create
      its environment, following [Module 1](module-01-setup.md). Building
      and packing the environment can take up to 15 minutes each.
    - Pick an analysis flavor, coffea or RDataFrame (see below).

## Pick a flavor: coffea or RDataFrame

The analysis is written both with coffea and with ROOT's RDataFrame, and you
choose the one you prefer. Wherever the two differ, a page shows `coffea`
and `RDataFrame` tabs, and a click on one switches every other such tab on
the site. Everything else, namely VineReduce, TaskVine, the factory, and the
pool, is shared between them. Both are installed by the same environment, so
you can switch later. [Module
1](module-01-setup.md#pick-your-analysis-implementation) says more.

## What you will learn

By the end, you can:

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

## The data

Every module runs on real CMS Open Data from `Run2012B_SingleMu`, the input
of the IRIS-HEP ADL benchmarks: 5 datasets of 3 files each, 15 ROOT files
and 3,736,416 events in all. The same files are read from the VAST
filesystem by the modules that run on the login node, and over xrootd by
the modules that run on the pool. [Module 1](module-01-setup.md#data-descriptions)
shows the two manifests, and the
[Appendix](appendix.md#about-the-tutorial-dataset) has the details.

## Schedule

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
[Appendix](appendix.md). After the session, [Module
10](module-10-wrapup.md) lists where to get help.
