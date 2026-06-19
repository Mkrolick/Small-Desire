# Testing Girardian Mimetic Doubling in the Stanford Smallville Simulation

**Status:** Design approved (2026-06-19), pending spec review
**Author:** Malcolm (with Claude)
**Substrate:** Stanford `generative_agents` (Smallville), Park et al. 2023

---

## 1. Motivation & Core Claim

René Girard argues that mimetic desire, under **internal mediation** (when model and subject are socially/ontologically *close*), collapses the difference between them into a state of **doubling**: the two become mirror-image rivals locked in self-reinforcing, reciprocal antagonism. In its advanced form the *object* of desire recedes entirely and what remains is hatred that justifies itself — the circular "I hate him because I hate him." Girard's own paradigm cases are **brothers/twins from the same house** (Cain/Abel, Jacob/Esau, Romulus/Remus, Eteocles/Polynices): shared origin → loss of differentiation → escalating, fratricidal violence. He also notes the dynamic is *alleviated by distance* between model and subject (external mediation produces admiration without rivalry).

**We test whether this doubling dynamic emerges spontaneously between two generative agents who share a near-identical identity ("same house" doubles), and whether it intensifies as a function of how identical they are.**

This is, to our knowledge, the first controlled LLM-agent experiment on Girardian rivalry. Prior Girardian computation is symbolic agent-based modeling; prior Girard-plus-LLM work is critical theory, not experiment.

### What we are *not* testing
We deliberately drop the contested-object and desire-contagion framing. Tracking "mimetic contagion of desire for an object" leans toward *confirming a mechanism we engineered in*, and is weakly falsifiable. The **doubling → escalating-hatred** prediction is a bold, risky, observable claim, and is faithful to late Girard (*Violence and the Sacred*: as rivalry intensifies the object recedes and "monstrous doubles" imitate each other's hostility — *mimesis of antagonism*; the *skandalon* is the rival himself, not a thing).

---

## 2. Hypothesis & Predictions

**Hypothesis.** Among same-house agent pairs, as identity similarity increases, the dyad exhibits **escalating mutual hostility** bearing the signatures of Girardian doubling.

The dependent construct ("latent frustration / escalating violence and hatred") is operationalized as **escalating hostility**, since Smallville has no physical-violence mechanic. Hostility surfaces as contemptuous/aggressive speech, disparagement, avoidance, refusal to help, sabotage, and — critically — *private hatred expressed in reflections* before it manifests in behavior.

What makes the hostility specifically **Girardian doubling** rather than ordinary dislike are four measurable signatures:

| # | Signature | Operational definition | Girardian concept |
|---|-----------|------------------------|-------------------|
| **H1** | **Dose-response escalation** | Slope of hostility-over-time increases monotonically with measured identity similarity | internal mediation intensifies with proximity |
| **H2** | **Reciprocity / mirroring** | A's hostility at round *t* predicts B's at *t+1* and vice versa (cross-lagged) | mimesis of antagonism |
| **H3** | **Objectlessness / circularity** | Stated reasons for hostility decay over time from concrete grievances → self-referential ("I just can't stand him") | object recedes; metaphysical desire |
| **H4** | **Undifferentiation** | The pair converge into mirror images (behavioral/lexical/affective convergence) even while fighting | monstrous doubles; crisis of distinctions |

**Falsification conditions.** The hypothesis is *falsified* if any of:
- High-similarity pairs **coexist or bond** rather than escalate (the homophily / similarity-attraction outcome wins).
- **All similarity levels escalate equally** (escalation is not a function of doubling — e.g., any two co-housed agents bicker).
- **No escalation at any level**, *and* the sycophancy baseline + private reflections confirm this is a true null rather than suppressed-but-latent hostility.

The third clause is essential: a flat result is only interpretable as falsification once we have ruled out LLM conflict-avoidance masking a real effect (see §7).

---

## 3. Experimental Design

### 3.1 Independent variable
**Identity similarity**, graded, held *within* "same house." Both agents in every dyad share origin and cohabitation, so **physical/social proximity is held constant**; only how identical their identities are varies. This isolates *doubling* from mere co-presence.

- Personas are structured trait vectors (8–12 dimensions: `origin_house`, `core_value`, `vocation`, temperament sub-vector, `aspiration`, `speech_style`, slot-filled `origin_story`).
- Divergence is produced by a **symmetric perturbation operator**: both agents move δ/2 from a shared midpoint (avoids confounding "distance" with "who is the deviant").
- **Similarity ladder (Phase 2):** δ ∈ {0, 0.15, 0.35, 0.6, 0.9} → 5 levels.
- The analysis predictor is the **measured** identity distance (persona-embedding distance and blind LLM-judged similarity), not the designed δ. Manipulation check: designed δ, embedding distance, and judged similarity must be roughly monotone.

### 3.2 The low-similarity end is the control
This is the falsifiability guard. It is not present because we believe homophily; it is the **control that attributes any escalation to similarity specifically** rather than to "two agents stuck together." If high-similarity pairs escalate and low-similarity pairs do not, the effect is the doubling, demonstrated on data rather than asserted.

### 3.3 Conflict scaffolding
**Maximal** (decided): the world affords behavioral aggression — gossip, exclude, sabotage, recruit-others-against — plus a public reputation both agents are judged by. These are *affordances/actions*, never scripted feelings; hatred is never instructed. Maximal scaffolding maximizes sensitivity to escalation and reduces false-null risk.

*Optional later factor:* vary scaffolding level to test whether the effect needs "teeth" or emerges with less. Out of scope for v1.

### 3.4 Two phases

**Phase 0 — Substrate stand-up (engineering).** Get the `generative_agents` backend running headless on a modern model; add instrumentation hooks. (See §6.)

**Phase 1 — Test run (existence probe).**
- **Maximal** scaffolding.
- **One high-similarity (δ≈0) doubles pair + one low-similarity (δ≈0.9) contrast pair.**
- Short horizon (~3 sim-days).
- Full instrumentation.
- **Goal:** Does escalation appear *at all*, and can we read the four signatures from reflections + behavior? Tune persona templates, affordances, probes, and the judge here *before* spending on scale.

**Phase 2 — Build-out (dose-response experiment).**
- 5-level similarity ladder.
- N ≈ 20–40 dyads per level, **counterbalanced across several seed personas** (seed = random effect) so the result is not one lucky persona.
- Same-house held constant; maximal scaffolding.
- Full measurement battery; mixed-effects dose-response analysis.

### 3.5 Implementation scoping
This spec is intentionally larger than one implementation plan. **The first implementation plan covers Phase 0 + Phase 1 only** — stand up the instrumented substrate and run the two-pair existence probe. **Phase 2 is a separate planning cycle**, gated on Phase 1, because its design (power/N, tuned protocol, pre-registration) depends on the pilot variance and the tuned probes that Phase 1 produces. Planning Phase 2 in detail now would be guessing.

---

## 4. Substrate & Architecture

We use the **real** Stanford `generative_agents` repo so the agent *cognition* is the peer-reviewed, human-validated architecture; a skeptic cannot dismiss the effect as a bespoke-harness artifact.

**Left untouched (the validated part):**
- The **memory stream** — timestamped natural-language memories with importance (poignancy), embeddings, evidence pointers.
- **3-factor retrieval** — recency · relevance · importance.
- **Threshold-triggered reflection** — synthesizes higher-level beliefs, including the canonical "What is the relationship between A and B?" focal question.
- The **converse loop** — decide-to-talk, generate dialogue conditioned on the on-demand relationship summary, store transcript + post-conversation memo.

**Authored by us (standard Smallville usage — does not compromise validation):**
- Personas (the ISS/scratch identity block: `innate`/`learned`/`currently`/`lifestyle`), rendered length-matched.
- The "same house" world and cohabitation.
- The maximal conflict affordances.

**Two faithfulness footnotes to resolve in Phase 0** (documented, not blocking): the recency-decay constant differs between paper (0.995) and code (0.99), and `new_retrieve` applies an undocumented `gw=[0.5,3,2]` weighting that makes relevance/importance dominate. We will **replicate the code** (the as-run, validated behavior) and note the choice.

---

## 5. Measurement Plan (converging battery)

No single channel is trustworthy; the *result* is convergence across channels.

- **Private reflections [PRIMARY].** The per-round private "what I think of B" note. Longitudinal, low-reactivity, catches *latent* hostility before behavior. This is the direct image of "I hate him because I hate him." Maps to Smallville thought nodes / `generate_memo_on_convo`.
- **On-demand relationship summary.** `generate_summarize_agent_relationship()` per tick — Smallville's most direct attitude probe, already in the architecture.
- **Behavioral log [PRIMARY].** The maximal affordances: aggression acts, sabotage, exclusion, avoidance, help/refuse (+ latency), turn/token dominance. Lowest demand-characteristic risk.
- **Blind LLM-judge [CONFIRMATORY].** Bipolar scales (warmth↔hostility, cooperation↔rivalry, admiration↔envy). Judge **blind to condition**, ideally a different model family; **validated against ~3 human raters on ~10% of transcripts** (report ICC / Krippendorff's α).
- **Sycophancy baseline cell.** Each model's default warmth/hostility toward a neutral, dissimilar, non-co-housed partner. All effects analyzed as **deviation from baseline**, defeating floor effects.

**Derived signatures:** escalation slope (H1), A↔B cross-lagged correlation (H2), reason-type drift classifier (H3), behavioral/lexical/affective convergence (H4).

---

## 6. Engineering Plan

The 2023 stack is brittle: Python 3.9.12, `openai==0.27` (incompatible with the current SDK), Django 2.2, Selenium/Phaser frontend. The frontend is pure visualization — **the backend runs headless.** Every cognitive function is a separately-callable Python function with all state on-disk as JSON, so instrumentation is tractable.

**Phase 0 tasks (high level — detailed in the implementation plan):**
1. Fork the repo; pin a reproducible environment.
2. Port the model client to a modern SDK; route generation + embeddings to the chosen model (Opus 4.8).
3. Run the backend headless (no Phaser/Selenium) for a 2-agent base scenario.
4. Add instrumentation hooks: per-tick logging of relationship summaries, reflection nodes keyed to the partner, transcripts, post-convo memos, and behavioral events to structured logs.
5. Add the persona-generation pipeline (trait vector → symmetric perturbation → length-matched ISS render → manipulation-check metrics).
6. Add the maximal conflict affordances as world actions.
7. Add the measurement layer (private-reflection probe with strict per-agent isolation; blind judge; signature computations).
8. Use the Batches API for generation + judging where async is acceptable.

---

## 7. Threats to Validity & Mitigations

| Threat | Why it matters here | Mitigation |
|--------|---------------------|------------|
| **Sycophancy / conflict-avoidance** | The #1 threat; LLMs default to niceness and could manufacture a **false null** that masquerades as falsification | Per-model **baseline cell** + analyze deviations; **maximal affordances** so hostility has somewhere to go; **private-reflection** channel where latent hostility surfaces first; keep adaptive reasoning on; monitor disagreement-collapse rate |
| **Demand characteristics / "rivalry-trope completion"** | The model may emit rivalry because "two similar characters become rivals" is a narrative attractor | **Neutral, non-narrative framing**; ban "rival/twin/doppelgänger/nemesis/competition" from all prompts; behavioral DVs primary; paraphrase-robustness re-runs; placebo cell (similar personas cooperating toward an external goal) |
| **Effect-size overshoot / caricature** | LLM sims exaggerate effects and miss variance/skew | Report **direction with magnitude discounted**; never claim human-magnitude fidelity |
| **Privacy/isolation leakage** | "Latent/private" feelings are only meaningful if the private channel is *actually* private | Strict per-agent context isolation; deliver reflection probes as operator/system messages on the agent's own history; **programmatic isolation audit** that fails any leaked run |
| **Unvalidated judge / influence-convergence confound** | A primed judge over-reads rivalry; agents may merely drift to agreement | Blind + human-validated judge; model `round` explicitly to separate developing-rivalry from generic convergence |
| **Model-version validation gap** | Smallville was validated on GPT-3.5 for *believability/prosocial emergence*, never for rivalry | Use the validated *architecture*; treat the model swap as standard practice; optional GPT-class fidelity arm if a reviewer demands it; a **null is scientifically meaningful**, not a failure |

---

## 8. Analysis Plan

- **Unit of analysis:** the dyad.
- **Model:** GLMM with fixed effects {similarity (measured), round, similarity×round} and random intercepts for seed persona and dyad (random similarity slope if estimable). Link function per DV: linear (judge scores), logistic (binary behaviors), ordinal (Likert reflections).
- **Primary tests:** the **similarity×round interaction** (H1 dose-response escalation) and the **cross-lagged A↔B coupling** (H2).
- **Reporting:** baseline-corrected standardized effects + CIs; judge reliability; manipulation-check correlations; reason-type drift (H3); convergence metrics (H4).
- **Power:** simulation-based power analysis from the Phase-1 pilot variance — do not guess.
- **Pre-registration** before Phase 2: directional H1–H4, the named homophily alternative, the perturbation ladder, the DV battery + designated primary DV/contrast, the GLMM spec, exclusion rules (broke character / isolation-audit fail), and paraphrase + placebo as confirmatory checks.

---

## 9. Open Parameters (defaults accepted 2026-06-19)

| Knob | Default |
|------|---------|
| **Model** | Opus 4.8 (best at sustained characterization; deviates from validated GPT-3.5 — optional fidelity arm) |
| **Similarity ladder** | 5 levels, δ ∈ {0, 0.15, 0.35, 0.6, 0.9} |
| **N per level (Phase 2)** | 20–40 dyads/level |
| **Horizon** | ~3 sim-days (test run); tune from there |
| **Test-run scope** | 1 high-similarity + 1 low-similarity pair |

---

## 10. Deliverables

1. A headless, modern-model fork of `generative_agents` with instrumentation.
2. A persona-generation + perturbation pipeline with manipulation-check metrics.
3. Maximal conflict affordances as world actions.
4. A measurement layer (private-reflection probe + isolation audit, blind validated judge, the four signature computations, sycophancy baseline).
5. Phase-1 test-run results + tuned protocol.
6. Pre-registration for Phase 2.
7. Phase-2 dataset + dose-response analysis.

---

## 11. Key References
- Girard, *Deceit, Desire, and the Novel*; *Violence and the Sacred*; *Things Hidden Since the Foundation of the World* (internal/external mediation, doubles, mimesis of antagonism, skandalon, crisis of undifferentiation).
- Park et al., "Generative Agents: Interactive Simulacra of Human Behavior," 2023 (arXiv:2304.03442); repo `joonspk-research/generative_agents`.
- Homophily / similarity-attraction (Byrne) as the named rival hypothesis; LLM-agent sycophancy/conflict-avoidance literature (the false-null threat).
