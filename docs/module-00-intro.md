# Module 0 - Intro

**15 min, lecture**

!!! danger "TODO: slides link"
    Link to the lecture slides goes here.

The slides carry the lecture; this page is rather the short version, meant
for coming back to later.

## The physics

Today's analysis is IRIS-HEP's ADL benchmark Q6: for every event with at
least three jets, find the trijet whose combined invariant mass is closest
to the top quark mass (172.5 GeV), then histogram that trijet's $p_T$ and
the highest b-tag score among its three jets. It is small enough to read in
one screen; however, it has the same shape as a real analysis, namely a
function applied to chunks of events, whose outputs get added together.

Real analyses look like a much bigger version of this. For example,
[`TopEFT/ttbarEFT`](https://github.com/TopEFT/ttbarEFT), a CMS top-quark
EFT search, runs on this exact stack in production (see
[Module 10](module-10-wrapup.md)). Thus, the trijet selection is a toy
only with regards to its size, not its structure.

The same analysis is written two ways in this tutorial, and you pick one in
[Module 1](module-01-setup.md#pick-your-analysis-flavor):

- **coffea**: the processor is a Python function over awkward arrays. The
  trijet is built from array operations (`ak.combinations`, `ak.argmin`, and
  so on), and the result is `hist.Hist` objects.
- **RDataFrame**: the processor is a Python function that describes a
  ROOT `RDataFrame` computation (`Filter`, `Define`, `Histo1D`). The
  per-event trijet search is a short C++ function that ROOT compiles when
  the processor first runs, and the result is converted to the same
  `hist.Hist` objects.

Both are just "a function applied to a chunk of events", which is all that
VineReduce asks of a processor. Thus, everything below the processor is
shared.

## The shape of the stack

Every run today has the same two sides. Your physics code, VineReduce, and
a *distributor* run once, on the machine you're logged into. An
*executor* and your physics code, however, run remotely, once per chunk, on
whatever worker picks the chunk up:

```text
       local (x1)
+---------------------+
|     application +   |
|     physics code    |
+---------------------+
|     vine-reduce     |
+---------------------+
|     distributor     |
+---------------------+
           |
           v
      remote (xN)
+---------------------+
|       executor      |
+---------------------+
|     physics code    |
+---------------------+
```

## Why VineReduce, alongside coffea

coffea's own executors couple two concerns that don't have to be solved
together. The first is **parallelism**, that is, how one dataset's work is
split into chunks, mapped, and reduced back together. The second is
**distribution**, which is how those chunks get scheduled onto, transferred
to, and run on remote machines.

VineReduce owns the first and hands the second to a distributor (today,
TaskVine), so that each can change without touching the other. This is why,
all session, your processor code never changes; the only thing that changes
is what it's handed to. It is also why the processor can be built from
coffea or from RDataFrame: VineReduce only needs a function that takes a
chunk.

## What you'll stand up today

In order:

1. A process on the login node, with local subprocesses as "workers"
   ([Module 2](module-02-local-distributor.md)).
2. A TaskVine manager plus one TaskVine worker, both on the login node
   ([Module 3](module-03-local-factory.md)).
3. TaskVine workers on the real HTCondor pool, found through the catalog
   server, running a packed copy of your environment
   ([Module 4](module-04-scale-out.md)).

Then, on that pool, the remaining modules cover tuning resources and chunk sizes,
checkpoints and restart, shipping large outputs out of band, running
several processors at once, and tolerating failed files.
