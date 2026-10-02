# Module 10 - Wrap-up

**10 min**

## What you did today

The same trijet processor ran, unchanged, through:

1. `LocalDistributor` on the login node ([Module 2](module-02-local-distributor.md)),
2. a TaskVine manager and one local worker ([Module 3](module-03-local-factory.md)),
3. HTCondor workers on the pool, reading real CMS data from CERN
   ([Module 4](module-04-scale-out.md)).

Along the way you declared resources and let chunks shrink to fit
([Module 5](module-05-resources.md)), resumed an interrupted run
([Module 6](module-06-checkpoints-restart.md)), wrote a skim to shared
storage without it passing through the manager
([Module 7](module-07-result-postprocess.md)), ran several processors in
one job ([Module 8](module-08-multiple-processors.md)), and decided how
many lost files a run may tolerate
([Module 9](module-09-failure-proportion.md)).

## Scaling this up for a real analysis

Nothing you used today is a tutorial-only API. A production analysis
changes the size of the inputs and the physics inside the processor, rather
than the shape of the script.

For an example of what that looks like, read (but don't run)
`examples/ttBar/run_processor_with_vr.py` in your
`vine-cms-analysis-stack` clone. It is a full EFT analysis in the style of
`ttbarEFT`/`TopEFT`, on the same `VineReduceCoffea` +
`TaskVineDistributor` API. However, it expects TopEFT's own sample
metadata, a grid proxy for access-controlled CMS data, and a pool of
workers started independently, so it isn't something to try in the room.
Such a script is perhaps best read as a map of where today's pieces end up
once the analysis is no longer a toy.

### `datasets_real.json`

The same `Run2012B_SingleMu` CMS Open Data file used live today, but no
longer capped at 500,000 events: the **entire** file (53,446,198 events)
is split into 205 local ROOT files (10,000-500,000 events each), divided
at random across 5 datasets of 34-47 files apiece:

| dataset | files | events |
|---|---|---|
| `SingleMu_Run2012B_193834-194270` | 42 | 11,072,840 |
| `SingleMu_Run2012B_194271-194789` | 41 | 11,743,639 |
| `SingleMu_Run2012B_194790-195398` | 47 | 11,562,084 |
| `SingleMu_Run2012B_195399-195841` | 41 | 10,101,069 |
| `SingleMu_Run2012B_195842-196531` | 34 | 8,966,566 |

Built once, ahead of time, by `scripts/make_real_scale_data.py` (seeded,
so the split is reproducible) - not run live in the room. The dataset
names are styled after real CMS run-range dataset splits, but are
illustrative only: files were divided by position in the source file, not
by each event's actual run number, so a name's range isn't a claim about
what's really inside that dataset.

This is the shape a production analysis (`ttbarEFT`/`TopEFT`) takes on top
of the exact same API used all session: many files, several datasets, in
one `VineReduceCoffea` call.

## Where to get help

Questions after today are welcome, through any of these:

- **NDCMS Mattermost**: <https://mattermost.web.cern.ch/ndcms/channels/cctools>
- **Cooperative Computing Lab**: <https://cclnd.cse.nd.edu>
- **GitHub issues**: `cooperative-computing-lab/vine-reduce`,
  `cooperative-computing-lab/vine-cms-analysis-stack`
- **Email**: btovar@nd.edu
