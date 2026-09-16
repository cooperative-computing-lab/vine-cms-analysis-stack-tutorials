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

!!! danger "TODO"
    A full-size real dataset, read over xrootd at Notre Dame, to show what
    scaling today's scripts up looks like. The source (server, path,
    collection) is still to be decided, so there is nothing to fetch or
    run yet.

## Where to get help

Questions after today are welcome, through any of these:

- **NDCMS Mattermost**: <https://mattermost.web.cern.ch/ndcms/channels/cctools>
- **Cooperative Computing Lab**: <https://cclnd.cse.nd.edu>
- **GitHub issues**: `cooperative-computing-lab/vine-reduce`,
  `cooperative-computing-lab/vine-cms-analysis-stack`
- **Email**: btovar@nd.edu
