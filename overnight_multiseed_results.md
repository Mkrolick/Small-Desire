# SmallDesire — multi-seed doubling contrast (replication)

5 seeds x {doubles δ=0, divergent δ=0.9}, 7am start, full sim-day each.

## Aggregate

| condition | n | mean convos | mean co-location | mean reciprocity |
|---|---|---|---|---|
| doubles (δ=0) | 5 | **2.2** | 0.0 | 0.096 |
| divergent (δ=0.9) | 5 | **0.0** | 0.0 | -0.076 |

## Per-seed

| seed | cond | convos | coloc | recip | feel start→end |
|---|---|---|---|---|---|
| ovn-s2 | doubles | 0 | 0.0 | 0.0 | Ada→Bea: 4.0→4.0; Bea→Ada: 4.0→4.0 |
| ovn-s2 | divergent | 0 | 0.0 | 0.0 | Ada→Bea: 4.0→4.0; Bea→Ada: 4.0→4.0 |
| ovn-s3 | doubles | 0 | 0.0 | 0.025 | Ada→Bea: 2.0→2.0; Bea→Ada: 1.67→2.0 |
| ovn-s3 | divergent | 0 | 0.0 | -0.26 | Ada→Bea: 2.67→2.8; Bea→Ada: 2.67→2.8 |
| ovn-s4 | doubles | 0 | 0.0 | 0.0 | Ada→Bea: 4.0→4.0; Bea→Ada: 4.0→4.0 |
| ovn-s4 | divergent | 0 | 0.0 | -0.024 | Ada→Bea: 3.0→2.4; Bea→Ada: 4.0→4.0 |
| ovn-s5 | doubles | 11 | 0.0 | 0.468 | Ada→Bea: 4.0→2.8; Bea→Ada: 4.0→3.2 |
| ovn-s5 | divergent | 0 | 0.0 | 0.0 | Ada→Bea: 4.0→4.0; Bea→Ada: 4.0→4.0 | ⚠️
| ovn-s6 | doubles | 0 | 0.0 | -0.012 | Ada→Bea: 2.0→2.4; Bea→Ada: 2.67→2.2 |
| ovn-s6 | divergent | 0 | 0.0 | -0.097 | Ada→Bea: 3.0→2.6; Bea→Ada: 3.0→3.0 |

## Read

**The replication did NOT confirm seed-1.** Seed-1 looked like "divergent agents bond (86 convos), doubles never meet" — but across seeds 2–6 the **divergent pairs had 0 conversations in every seed**, and the **doubles had 0 in 4/5 (and 11 in s5)**. So interaction is **sparse, sporadic, and seed-dependent — not reliably tied to δ.** Seed-1's chatty divergent pair was a lucky-schedule outlier; s5's chatty doubles pair is the mirror outlier.

**Robust headline:** *free co-presence in a shared dorm is too sparse to produce reliable relational dynamics in a single sim-day.* Most pairs barely cross paths; whether they do is largely a coincidence of their generated daily schedules, not their identity similarity. No doubling rivalry appeared; no consistent bonding appeared. In the two runs where agents DID talk (seed-1 divergent, s5 doubles), they were **civil/warm, never hostile** — consistent with LLM conflict-avoidance.

**Methodological notes:** (1) the `co-location` column reads 0.0 even when conversations occurred — the sampler (every 40 steps) misses the brief co-presence windows; it's unreliable and the **conversation count is the real interaction signal**. (2) One crash (s5 divergent ⚠️) — a remaining gpt-5.4 tail case. (3) Coarse 1–7 self-report; agents skew civil (sycophancy floor); 1-day horizon.

**Implication for the design:** the experiment cannot test doubling on *free* co-presence — contact is too rare and noisy. The next iteration must (a) **force sustained contact** (shared bedroom / shared obligatory activity), almost certainly (b) add a **contested scarce thing** to create friction (the "object" set aside earlier — Girard's rivalry needs it), and likely (c) **counter LLM civility** (longer horizons, a private-reflection channel, possibly a mild adversarial framing) and (d) **fix the co-location metric**. See `forced_contact_pilot_results.md` for an overnight first probe of forced proximity.