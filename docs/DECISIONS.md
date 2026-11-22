# Design decisions log

Append one entry per decision (agents: always do this when adding or changing an algorithm).

```
## YYYY-MM-DD — <title>
- What: …
- Why: …
- Complexity: …
- Alternatives tried / rejected: …
```

<!-- luna-decision:local-search-2swap -->
## 2026-11-22 — Greedy + Local Search (1-nga-2 swap) me shortlist

- **Çka:** Baseline Random Search u krahasua me Greedy; pastaj u shtua Local Search që provon zëvendësimin e një transferi me dy transfere kompatibile.
- **Pse:** Greedy është i shpejtë por mund të bllokojë dy transfere me peshë totale më të lartë. Kërkimi lokal mund të përmirësojë zgjidhjen pa thyer kufizimet E/L/D.
- **Vendim praktik i implementimit:** `limit_per_transfer = 35` dhe buxhet kohor për të shmangur kërkimin shumë të kushtueshëm në Matching II. Ky është kompromis shpejtësi/cilësi dhe duhet testuar me vlera të tjera përpara pretendimeve për optimalitet.
- **Kompleksiteti:** Greedy `O(n log n)`; Local Search me `r` raunde, `s` transfere të zgjedhura dhe `k=35` kandidatët e shkurtuar: `O(r*(n log n + s*k²))` si kufi i sipërm i përgjithshëm.
- **Alternativa të konsideruara:** Random Search (shpesh 0 pikë), Greedy pa përmirësim, kërkim lokal pa shkurtim (më i kushtueshëm).
- **Provat:** Testet automatike dhe `results/metrics.csv`; përpara dorëzimit verifiko rezultatet me vlerësuesin zyrtar të ESA-s.
- **Origjina:** Vendimi dhe implementimi janë zhvilluar gjatë punës së studentit me asistencën e ChatGPT; studenti duhet të kuptojë e të justifikojë çdo zgjedhje në mbrojtje.
