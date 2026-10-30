# vine-cms-analysis-stack-tutorials

A 3-hour hands-on tutorial for HEP graduate students on
[TaskVine](https://cctools.readthedocs.io/en/latest/taskvine/),
VineReduce, and
[`vine-cms-analysis-stack`](https://github.com/cooperative-computing-lab/vine-cms-analysis-stack).

Students take one real CMS analysis from a single process on a login node,
to a TaskVine worker on the same machine, to an HTCondor pool, while the
processor code stays the same each time. Along the way they learn to read a
run's health, tune chunk and resource sizes, restart without redoing work,
ship large results out of band, and keep a run going when some chunks fail.
The analysis is written both with coffea and with ROOT's RDataFrame, and
students pick one.

**Start here: [docs/index.md](docs/index.md)**

## For students

You don't need to clone this repository. Read the tutorial from the web,
and clone only `vine-cms-analysis-stack`, as described in
[Module 1](docs/module-01-setup.md). The scripts and dataset manifests you
run are in that clone, under `examples/tutorial_nd/`.

Do Module 1 *before* the session: building and packing the environment can
take up to 15 minutes each.

## Contents

| # | Module | Minutes |
|---|---|---|
| 0 | [Intro / motivation (lecture)](docs/module-00-intro.md) | 15 |
| 1 | [Setup & verify](docs/module-01-setup.md) | 15 |
| 2 | [Local distributor: map/reduce concepts](docs/module-02-local-distributor.md) | 15 |
| 3 | [Local TaskVine factory](docs/module-03-local-factory.md) | 20 |
| 4 | [Scale out: packaging, catalog, condor, certs, real data](docs/module-04-scale-out.md) | 30 |
| 5 | [Resources & chunk/reduction size](docs/module-05-resources.md) | 15 |
| 6 | [Checkpoints & restart](docs/module-06-checkpoints-restart.md) | 20 |
| 7 | [Shipping results out: `result_postprocess`](docs/module-07-result-postprocess.md) | 15 |
| 8 | [Multiple processors](docs/module-08-multiple-processors.md) | 10 |
| 9 | [`failure_proportion`](docs/module-09-failure-proportion.md) | 15 |
| 10 | [Wrap-up / where to get help](docs/module-10-wrapup.md) | 10 |
| | **Total** | **180** |

Reference material outside the 180 minutes is in the
[Appendix](docs/appendix.md).

## Building the site locally

The site is built with MkDocs and the Material theme; [pixi](https://pixi.sh)
installs both from `pixi.toml`.

```bash
git clone https://github.com/cooperative-computing-lab/vine-cms-analysis-stack-tutorials.git
cd vine-cms-analysis-stack-tutorials
pixi run mkdocs serve          # live preview at http://127.0.0.1:8000
pixi run mkdocs build --strict # static site in site/
```

Pages live in `docs/`, the navigation in `mkdocs.yml`, and the styling in
`docs/stylesheets/extra.css`.

## License

See [LICENSE](LICENSE).
