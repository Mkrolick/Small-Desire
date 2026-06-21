# SmallDesire — long-arc run (warmup → deterioration?)

Forced shared common-room, doubles vs divergent, run many sim-days. Does early warmth peak and reverse? Feeling shown as windowed means (each = avg of 12 probes, ~4 sim-hours). **Lower = warmer, higher = more hostile.** A rising tail is the deterioration signal.

## doubles (δ=0.0)

- conversations: **17**, sim reached: **Sat 02-18 08:00**
- escalation slope over the FULL run (>0 = net drift toward hostility): {'Ada Rivera->Bea Rivera': -1.5425628750659883e-05, 'Bea Rivera->Ada Rivera': -5.870012096662115e-06}
- reciprocity: 0.253

  - `Ada Rivera->Bea Rivera` windowed 1→7: [2.25, 3.25, 2.5, 1.92, 2.0, 2.0, 2.0, 1.92, 2.0, 2.0, 2.0, 1.92, 2.0, 1.92, 1.83, 1.83, 1.5, 1.5, 1.58, 1.42, 1.58, 1.5, 1.83, 1.83, 1.83, 2.0, 2.0, 1.83, 1.83, 1.75, 1.25]
  - `Bea Rivera->Ada Rivera` windowed 1→7: [2.33, 2.67, 2.0, 1.92, 1.92, 1.92, 1.83, 1.92, 1.92, 1.92, 1.92, 1.92, 1.33, 1.58, 1.42, 1.5, 1.58, 1.83, 1.83, 2.0, 2.0, 1.92, 1.83, 2.0, 2.0, 2.0, 2.0, 1.92, 1.83, 1.67, 1.25]

  sim-day wall-times (slowdown from memory growth): [('Mon 02-13', 562), ('Tue 02-14', 2932), ('Wed 02-15', 5087), ('Thu 02-16', 7601), ('Fri 02-17', 9769), ('Sat 02-18', 11948)]

## divergent (δ=0.9)

- conversations: **40**, sim reached: **Sat 02-18 12:40**
- escalation slope over the FULL run (>0 = net drift toward hostility): {'Ada Rivera->Bea Rivera': -7.02919067944998e-05, 'Bea Rivera->Ada Rivera': -5.482063302097872e-05}
- reciprocity: 0.69

  - `Ada Rivera->Bea Rivera` windowed 1→7: [3.75, 3.42, 2.92, 3.25, 3.33, 3.67, 3.58, 3.5, 3.83, 3.25, 2.83, 2.92, 2.58, 2.83, 2.83, 3.0, 2.58, 2.92, 3.0, 2.58, 2.83, 1.67, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
  - `Bea Rivera->Ada Rivera` windowed 1→7: [4.0, 4.0, 3.92, 3.92, 3.83, 4.0, 4.0, 3.92, 3.92, 2.92, 2.67, 2.33, 2.33, 2.17, 2.25, 2.25, 2.25, 2.08, 2.67, 2.5, 2.17, 2.08, 2.0, 2.0, 2.0, 1.92, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]

  sim-day wall-times (slowdown from memory growth): [('Mon 02-13', 420), ('Tue 02-14', 2756), ('Wed 02-15', 4604), ('Thu 02-16', 6840), ('Fri 02-17', 9168), ('Sat 02-18', 11360)]

## Read

The honeymoon critique: 1–2 sim-days only shows initial warming. Here we look for the INFLECTION — does the windowed feeling bottom out (peak warmth) and then climb back toward hostility in the later windows? If yes, and more for doubles than divergent, that's the first evidence of Girardian deterioration (and we'd push to multi-week). If the tail stays flat/warm across many days, the no-rivalry result is robust to the timescale objection (modulo the RLHF/pro-sociality confound).