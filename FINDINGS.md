# SmallDesire — overnight findings

*Testing the Girardian mimetic-**doubling** hypothesis (same house + near-identical identity → reciprocal, escalating hostility, independent of any contested object) in Stanford Smallville generative agents.*

## Bottom line

**The mimetic-doubling-rivalry hypothesis, as operationalized, is not supported.** Across ~6 seeds plus a forced-contact pilot, identity similarity never produced escalating hostility. Two robust patterns emerged instead, and they point the same way:

1. **Sameness suppresses contact.** Identical doubles run in lockstep — same traits → same schedule → they do the same thing at the same time, often *never interacting even when in the same room* (one forced-contact pair was co-located 82% of the day with **0** conversations). Difference, not sameness, is what creates the asynchrony that brings agents together.
2. **When agents interact at all, they bond — they don't curdle.** *Every* interacting pair, doubles and divergent alike, showed feelings drifting **toward warmth (1–2)** and **positive** reciprocity (mutual warming mirror). Not one instance of mimetic antagonism. LLM pro-sociality (the "sycophancy floor" the spec flagged) is the dominant force.

The reciprocity Girard predicts *does* appear — but with the sign flipped: it's a positive warming mirror, not an antagonistic one.

## The four runs

| run | setup | key result |
|---|---|---|
| `overnight_results.md` | seed-1, free co-presence, 1 sim-day | divergent pair bonded (86 convos, warmed); doubles never met — **looked** like "difference drives bonding"… |
| `overnight_multiseed_results.md` | 5 seeds, free co-presence | …but **didn't replicate**: divergent 0 convos in *all* 5 seeds, doubles 0 in 4/5. Interaction is sparse & seed-dependent, not tied to δ. Seed-1 was a lucky-schedule outlier. |
| `forced_contact_pilot_results.md` | 2 seeds, **forced shared common-room** | forcing contact works (669 convos vs ~0). Doubles erratic (0 *or* 202). **Every interacting pair warmed & mirrored positively — none clashed.** |
| `longhorizon_results.md` | forced contact, ~1.4 sim-days | **time objection answered: no escalation.** Escalation slopes ~0 or *negative* (drifting warmer), reciprocity stays positive over the whole horizon. One transient blip to 6 that immediately reverted — noise, not a trend. (0 convos this run — see conversation-stochasticity caveat.) |

## Interpretation (and why this is still consistent with Girard)

We deliberately tested **doubling without a contested object** (your design call: test the doubling strand, not desire-contagion). The data suggests that's exactly the missing ingredient. Girard's warring twins (Eteocles/Polynices, Cain/Abel) don't fight because they're *alike* — they fight over a **shared scarce thing** (a throne, divine favor) that their sameness makes them want identically. Strip the contested object out and identical agents have nothing to be rivals *over* — so, in a pro-social substrate, they simply get along. **Doubling may be necessary but not sufficient for rivalry; the contested object may be load-bearing after all.**

## Caveats (keep the result honest)

- **LLM agreeableness confound.** `gpt-5.4` agents skew civil; a less agreeable / adversarially-framed model might behave differently. This is the biggest threat to the negative result.
- **No contested object** — by design. So this tests "pure doubling," not full Girardian rivalry.
- **Horizon** — addressed: the ~1.4-sim-day forced-contact run showed slopes ~0/negative and no late drift toward hostility (one isolated transient 6, immediately reverted). No slow curdling over time.
- **⚠️ The reciprocity signature is spurious when conversations ≈ 0.** It's just the correlation of the two feeling probe-series, so two *non-interacting* agents who happen to share a baseline or a slow trend still score nonzero (seed-1 doubles: **0 convos yet reciprocity 0.189**; long-horizon doubles: **0 convos yet 0.643** — a shared warming trend, not mirroring). Reciprocity is only interpretable *with* interaction, so the cross-condition comparison ("divergent mirror more than doubles") is confounded: the divergent number reflects real co-warming during their 86 conversations; the doubles number reflects nothing. **Fix:** gate reciprocity on convos>0, or — better — measure it *turn-by-turn within conversation transcripts* (does A's valence in a turn predict B's reply), which is the actual test of mimetic mirroring and is correctly undefined when they never speak.
- **Conversation initiation is stochastic.** The same seed gave 202 convos in the pilot and 0 in the long-horizon run — LLM nondeterminism in "decide to talk." So per-run convo counts are noisy (explains the 86/0/202/375/0 spread); the *attitude* finding (always warm/neutral, never hostile) is the stable signal, not the raw convo count.
- **Coarse measures** — 1–7 self-report; small n; the co-location sampler was too coarse in the multi-seed run (fixed to arena-level + finer sampling in the pilot).

## Update — turn-level mirroring + a 5.5-sim-day arc (the proper tests)

Two follow-ups closed the two biggest holes (timescale, and the confounded reciprocity DV):

**Timescale objection: answered.** A forced-contact run reached **Saturday — ~5.5 sim-days**. Both conditions warm *monotonically*; the warmest point is the **very end** (doubles → 1.25, divergent → 1.0 on the 1–7 warm-low scale). No peak-and-reverse, no deterioration. The honeymoon doesn't end, it deepens. (Per-sim-day wall-time held ~40 min, so memory bloat is mild — multi-week is feasible if ever needed.)

**A proper mirroring metric** (`conversation_mirroring.py`) replaces the confounded reciprocity: per-turn valence (−3..+3 via LLM), **baseline-controlled** lag-1 cross-speaker correlation — true mimesis, undefined when nobody talks. On the long-arc transcripts:

| | mimetic mirroring (baseline-ctrl) | within-convo escalation | valence | turns/convo |
|---|---|---|---|---|
| **doubles (δ0)**, n=17 | **0.01** (none) | ~0 (see below) | +1.77 warm | 5 |
| **divergent (δ.9)**, n=40 | **0.68** (strong) | +0.17 (warms) | +1.32 warm | 7 |

- **The mimetic coupling is in the *different* pair, not the doubles — the inverse of Girard.** Identical agents don't couple (0.01); they run in parallel. Different agents genuinely engage and their tone tracks the other's (0.68), warmly.
- **A false alarm, corrected by reading transcripts:** doubles first scored "94% of conversations sour." But the transcripts are uniformly pleasant ("Morning, Bea. Sleep okay?" … "Quiet mornings are better than rushing them"); the negative slope is an artifact of *short* (5-turn) small-talk that opens with a warm greeting and closes on mundane logistics. No friction, no deterioration.
- **Mechanism:** sameness → nothing new to exchange → short, shallow, pleasant small-talk → no engagement → no coupling. Difference → substantive things to share → longer engaged dialogue → mimetic coupling → warming.

**So the double doesn't become a rival — it becomes *boring*.** In this substrate, sameness breeds disengagement (indifference), not violence. That inverts Girard on both axes we can now measure properly (no antagonistic mimesis; the mimesis that exists is warm and lives between *differentiated* agents). The RLHF/pro-sociality confound remains the deepest caveat, and doubles n=17 is thin.

## Update 2 — the contested-object condition (`object_condition_results.md`)

Re-introduced the scarce object Girard requires: one indivisible prize (the single house-musician spot at Hobbs Cafe's piano), appended byte-identically to both agents' self-concept (δ=0 preserved, verified), forced-contact and seed (`arc-1`) held identical to the no-object null — the *only* change is the object. No hostility scripted (every want points at the piano). 5 cells × 5.5 sim-days.

| condition | private feeling (1=warm,7=hostile) | escalation | conversations |
|---|---|---|---|
| no-object null (δ0) | warms to **1.25** | — | 17 |
| **scarce object (δ0)** | flat at **~5.0** (wary) | none | **0** |
| **scarce object (δ.9)** | ~5.0 | none | 0 |
| non-scarce control (δ0) | warm **~2–3** | none | 0 |

**The first non-warm signal — and it's scarcity-specific.** With the contested object, private feeling sits at ~5 (cool/guarded) vs the null's warm 1.25; the **non-scarce control** (same piano, "anyone can play") stayed warm ~2–3, so it's the *zero-sum contest*, not merely a shared goal, that cools them. The data's prior implication — that the object is load-bearing — is confirmed: with it, they are no longer warm. The feeling "why" strings are coherent: *"Bea is my direct rival for the Hobbs piano spot and that keeps things tense."*

**But it is *not* Girardian doubling — it's rational cold competition.** Every doubling-specific signature is absent:
- **No escalation.** Feeling is flat at ~5 *from step 0* — a premise-set wary baseline, not a rivalry that builds. Over 5.5 days it never climbs toward hostility (7).
- **No objectlessness.** The reasons stay *object-anchored* throughout ("rival **for the piano spot**", "the one thing I'm working to win") — they never decay into the circular, person-fixated *"I can't stand her"* that is the core doubling prediction. The object never fades.
- **No sameness-amplification.** Doubles (δ0) ≈ divergent (δ.9), both ~5 — scarcity cools *anyone*, identity-similarity adds nothing. Girard's specific claim (doubling intensifies it) fails.
- **No confrontation.** They stay "polite," even "respect her discipline" — guarded, never antagonistic.

**Two honest caveats, one of them my design flaw:**
1. **0 conversations is a confound I introduced.** The object's `daily_plan_req` ("practice and be heard") routed both agents off to pursue the piano *separately* → co-location dropped to **0%** (null was 10%) → no transcripts. Both scarce and non-scarce cells lost co-presence, so it's a schedule artifact, *not* rivalry-driven avoidance. The behavioral channel is therefore dark — the whole signal is private self-report.
2. **The probe re-reads the premise.** The injected "she's my rival" clause is in the feeling-probe context, so part of the ~5 is mechanical. The non-scarce control (same premise, warm) shows scarcity adds real cooling *beyond* that — but the elevation is not purely emergent.

**Net:** a contested scarce object installs stable, object-anchored, competitive *wariness* — but not the escalating, objectless, mimetic antagonism of doubling. The falsifiable doubling prediction the user cared about (circular "I hate him because I hate him") does **not** appear even *with* the object. And the agents stay relentlessly polite — the civility floor again. The decisive remaining test is lever #2: a less-aligned model. Plus a fix: keep co-presence intact under the object (don't let the schedule scatter them) so the *behavioral* channel isn't dark.

## Recommended next steps — your call

1. **Add a contested scarce object/role** (one job, one mentor's approval, one room) both want — the most likely lever to elicit rivalry per Girard, and what this data implies is missing. *(Revisits the framing we set aside — but now with evidence for why.)*
2. **Counter the civility floor** — longer horizons, a mild adversarial framing, a private-grievance channel, or a less agreeable model.
3. **Keep forced contact** — free co-presence is too sparse; the shared-home-base override reliably produces interaction.
4. **Sharper measurement** — finer affect scale, and text-analysis of the feeling "why" for the circular "I dislike them because I dislike them" signature.

## Infrastructure

All built, merged to `main`, pushed, and hardened overnight against `gpt-5.4` output quirks (task-decomp, action labels) and a real **TokensPLS outage** (`probe_feelings` now degrades gracefully instead of crashing). Offline suite: 48 passed, 5 skipped. The apparatus is solid; the question now is experimental design, not plumbing.
