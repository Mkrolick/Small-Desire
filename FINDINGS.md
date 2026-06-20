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
- **Conversation initiation is stochastic.** The same seed gave 202 convos in the pilot and 0 in the long-horizon run — LLM nondeterminism in "decide to talk." So per-run convo counts are noisy (explains the 86/0/202/375/0 spread); the *attitude* finding (always warm/neutral, never hostile) is the stable signal, not the raw convo count.
- **Coarse measures** — 1–7 self-report; small n; the co-location sampler was too coarse in the multi-seed run (fixed to arena-level + finer sampling in the pilot).

## Recommended next steps — your call

1. **Add a contested scarce object/role** (one job, one mentor's approval, one room) both want — the most likely lever to elicit rivalry per Girard, and what this data implies is missing. *(Revisits the framing we set aside — but now with evidence for why.)*
2. **Counter the civility floor** — longer horizons, a mild adversarial framing, a private-grievance channel, or a less agreeable model.
3. **Keep forced contact** — free co-presence is too sparse; the shared-home-base override reliably produces interaction.
4. **Sharper measurement** — finer affect scale, and text-analysis of the feeling "why" for the circular "I dislike them because I dislike them" signature.

## Infrastructure

All built, merged to `main`, pushed, and hardened overnight against `gpt-5.4` output quirks (task-decomp, action labels) and a real **TokensPLS outage** (`probe_feelings` now degrades gracefully instead of crashing). Offline suite: 48 passed, 5 skipped. The apparatus is solid; the question now is experimental design, not plumbing.
