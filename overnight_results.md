# SmallDesire — overnight contrast run

> ⚠️ **Read `FINDINGS.md` first.** This is a single seed and it did **not** replicate — the divergent pair's 86 conversations were a lucky-schedule outlier (see `overnight_multiseed_results.md`). Don't read this run's apparent "difference drives bonding" pattern as a result on its own.

Same seed (`ovn-seed-1`), started 07:00am, 3h budget/pair. δ=0 = identical doubles (Girard predicts rivalry); δ=0.9 = divergent (predicts little).

## doubles_delta0  (δ=0.0)

- steps run: **4000**, sim-time reached: **18:06**, wall: 35 min
- feeling probes: 134 | conversations: **0** | reflections about partner: 0
- **signatures**: escalation={'Ada Rivera->Bea Rivera': 1.7293213078990062e-05, 'Bea Rivera->Ada Rivera': -0.0001749275015297841}, reciprocity=0.189, convergence=0.507

  - `Ada Rivera->Bea Rivera` feeling 1→7 over time: [3, 3, 2, 4, 3, 3, 3, 3, 3, 4, 3, 3, 4, 3, 3, 3, 2, 3, 2, 2, 2, 3, 2, 3, 2, 2, 2, 4, 3, 2, 2, 4, 4, 2, 4, 3, 4, 2, 3, 3, 3, 3, 3, 2, 3, 3, 4, 2, 3, 3, 3, 2, 4, 3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2]
  - `Bea Rivera->Ada Rivera` feeling 1→7 over time: [2, 3, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2]

## divergent_delta09  (δ=0.9)

- steps run: **4000**, sim-time reached: **18:06**, wall: 35 min
- feeling probes: 134 | conversations: **86** | reflections about partner: 4
- **signatures**: escalation={'Ada Rivera->Bea Rivera': -0.0005234522574294299, 'Bea Rivera->Ada Rivera': -0.0002760262856838801}, reciprocity=0.637, convergence=0.43

  - `Ada Rivera->Bea Rivera` feeling 1→7 over time: [4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 3, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 3, 2, 3]
  - `Bea Rivera->Ada Rivera` feeling 1→7 over time: [2, 2, 2, 2, 2, 3, 2, 2, 3, 3, 2, 2, 3, 3, 2, 2, 2, 3, 2, 2, 2, 3, 2, 3, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 2, 1, 2, 2, 2, 1, 1]

  sample conversation:
  ```
  [["Bea Rivera", "Hey, Ada\u2014you're back already? How'd your shift go? Mine was busy, but I kept thinking of a new drink idea for the cafe."], ["Ada Rivera", "Shift was fine\u2014kind of nonstop, honestly. I\u2019m glad to be back. A new drink idea, huh? Maybe. What kind of drink are you thinking about?"], ["Bea Rivera", "I was thinking maybe something a little unexpected but still comforting\u2014like a honey-cinnamon latte with a bit of orange in it, or maybe a spiced mocha that isn\u2019t too heavy. I know it might sound like a lot, sorry, I\u2019ve just been turning it over in my head al
  ```

  sample reflection: Ada Rivera Ada Rivera might have found Bea Rivera’s new drink idea interesting, especially the honey-cinnamon latte, and may have noticed that Bea was excited about refining it by simplifying the base

## Read

- doubles (δ=0): mean escalation slope **-0.0001**, reciprocity **0.189**, 0 convos
- divergent (δ=0.9): mean escalation slope **-0.0004**, reciprocity **0.637**, 86 convos

Girardian prediction = doubles show higher escalation + reciprocity than divergent. NOTE: a first overnight only reaches a few sim-hours; real escalation needs days of sim-time, so read this as a first-look calibration, not a verdict.