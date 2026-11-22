"""Luna Tomato Logistics: safely document existing algorithms and measured results.

Run from the project root: python update_luna_docs.py
This script only updates README.md and docs/DECISIONS.md, keeping backups.
No solution files, algorithm code or checklist boxes are modified.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
README = ROOT / "README.md"
DECISIONS = ROOT / "docs" / "DECISIONS.md"
METRICS = ROOT / "results" / "metrics.csv"
MARKER_START = "<!-- luna-algorithm-analysis:start -->"
MARKER_END = "<!-- luna-algorithm-analysis:end -->"
DECISION_MARKER = "<!-- luna-decision:local-search-2swap -->"


def backup_once(path: Path) -> None:
    backup = path.with_name(path.name + ".bak")
    if path.exists() and not backup.exists():
        shutil.copy2(path, backup)


def read_metrics() -> tuple[list[str], str]:
    if not METRICS.exists():
        return [], "Nuk u gjet `results/metrics.csv`; tabela krijohet pasi të ekzekutohet `python tasks.py run`."
    with METRICS.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    table = [
        "| Problemi | Algoritmi | Pesha e transportuar | Koha (s) |",
        "|---|---|---:|---:|",
    ]
    for row in rows:
        if row.get("instance") not in {"matching-i", "matching-ii"}:
            continue
        try:
            transported = -float(row["fitness"])
            seconds = float(row["seconds"])
        except (KeyError, ValueError, TypeError):
            continue
        table.append(f"| {row['instance']} | {row.get('algorithm','?')} | {transported:,.3f} | {seconds:.3f} |")
    return [r.get("algorithm", "") for r in rows], "\n".join(table) if len(table) > 2 else "Nuk ka matje për Matching I/II."


def read_upper_bounds() -> str:
    p = ROOT / "results" / "upper_bounds.csv"
    if not p.exists():
        return "Upper Bound nuk u gjet ende në `results/upper_bounds.csv`."
    with p.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return "Upper Bound nuk ka rreshta ende."
    result = ["| Problemi | Algoritmi më i mirë i matur | Upper Bound | Dallimi me kufirin |", "|---|---:|---:|---:|"]
    for r in rows:
        result.append(f"| {r.get('instance', '?')} | {r.get('transported', '?')} | {r.get('upper_bound', '?')} | {r.get('gap_to_bound_pct', '?')}% |")
    return "\n".join(result)


def analysis_text(results: str, bounds: str) -> str:
    return f"""{MARKER_START}

## Analiza e algoritmeve — Luna Tomato Logistics

### Modelimi i problemit

Një transfer është një katërshe `(e, l, d, w)`: orbitë rreth Tokës, orbitë rreth Hënës, destinacion, peshë. Zgjidhet një grup transferesh me shumën më të madhe të peshave, duke përdorur secilën vlerë `e`, `l`, `d` maksimumi një herë. Vektori i dorëzimit ka 0/1 për secilin transfer. Vlerësuesi ESA kthen **negativin** e peshës së transportuar, prandaj rezultati më negativ është më i mirë.

### 1. Random Search — baseline i VSI

Ideja: krijon vektorë rastësorë brenda kufijve, i vlerëson me `udp.fitness()` dhe ruan më të mirin.

```text
best <- asnjë
përderisa ka kohë:
    x <- vektor rastësor
    rezultat <- fitness(x)
    nëse rezultat është më i mirë: best <- x
kthe best
```

Kompleksiteti për `k` kandidatë me `n` pozicione: rreth `O(k*n)` kohë (duke supozuar vlerësim `O(n)`); `O(n)` hapësirë për kandidat/best. Ky baseline nuk garanton zgjidhje valide për instanca të mëdha.

### 2. Greedy sipas peshës — `src/algorithms.py`

Ideja: rendit transferet nga pesha më e madhe te më e vogla; zgjedh një transfer vetëm nëse nuk përsërit E, L ose D.

```text
rendit transferet sipas peshës në zbritje
E, L, D <- bashkësi boshe
për secilin transfer t në renditje:
    nëse pesha(t) > 0 dhe asnjë prej E/L/D nuk është përdorur:
        zgjidhe t; shëno E/L/D si të përdorura
kthe transferet e zgjedhura
```

Kompleksiteti: **`O(n log n)` kohë**, për shkak të renditjes; **`O(n)` hapësirë** për indeksat dhe bashkësitë. Greedy nuk garanton optimumin global.

### 3. Local Search (1-nga-2 swap) — `src/algorithms.py`

Ideja: nis nga Greedy. Provon të heqë një transfer dhe të shtojë dy transfere të përputhshme me peshë më të madhe; pas përmirësimeve plotëson hapësirat me transfere pa konflikte. Implementimi ynë kufizon listën në **35 kandidatë për transfer të bllokuar** dhe përdor afat kohor, për ta mbajtur kërkimin praktik.

```text
S <- Greedy(transfers)
përderisa ka kohë:
    për çdo transfer jashtë S, gjej cilat transfere të S e bllokojnë
    kërko dy kandidatë që bllokohen vetëm nga i njëjti transfer i S
    nëse dy kandidatët janë kompatibilë dhe kanë peshë më të madhe:
        hiq transferin bllokues; shto të dy kandidatët
    përndryshe: ndalo
plotëso S me transfere pozitive pa konflikte
kthe S
```

Le të jenë `r` numri i raundeve, `n` numri i transfereve dhe `s` numri i atyre të zgjedhur. Me listë të shkurtuar `k=35`, një kufi i sipërm për secilin raund është `O(n log n + s*k²)` (përfshirë renditjen); në total `O(r*(n log n + s*k²))`, plus kufizimin praktik të kohës. Hapësira është `O(n+s)` për kandidatët dhe bashkësitë. Për shkak të kërkimit lokal nuk ka garanci të optimumit global.

### 4. Upper Bound — `src/upper_bound.py`

Për çdo nyje të Tokës, Hënës dhe destinacion merr peshën më të madhe të një transferi që e përdor atë nyje. Shuma e peshave maksimale për secilin grup jep tre kufij; minimumi i tyre është Upper Bound i sigurt mbi optimumin. Kompleksiteti: `O(n)` për kalimin nëpër transfere, plus nyjet e regjistruara për shumat; hapësira `O(v)`, ku `v` është numri i nyjeve të ndryshme. Kufiri mund të jetë i lirshëm.

### Pse problemi është i vështirë (NP-hard)

Problemi klasik **3-dimensional matching** pyet nëse ekziston një grup prej të paktën `K` triples pa nyje të përbashkëta. Nëse në versionin tonë i japim çdo triple pesha 1, kërkimi nëse pesha optimale arrin `K` e zgjidh edhe problemin klasik. Kështu, problemi i përputhjes tredimensionale me pesha është të paktën po aq i vështirë (**NP-hard**). Për këtë arsye përdorim heuristika për instancat me 25,000 dhe 92,103 transfere; nuk pretendojmë zgjidhje optimale.

### Rezultatet e matura lokalisht

Tabela më poshtë lexohet nga `results/metrics.csv` në momentin e ekzekutimit të këtij skripti. Pesha e transportuar është `-fitness`; nuk janë pikë të Combined Leaderboard.

{results}

### Krahasim me Upper Bound

{bounds}

**Kujdes:** Dallimi nga Upper Bound nuk është gabimi real nga optimumi. Advanced (Trajectory Matching) kërkon trajektore fizike të vlefshme; skanimet tona të deritanishme nuk kanë prodhuar pikë pozitive dhe nuk përfaqësojnë një zgjidhje finale.

### Mjetet dhe përgjegjësia e punës

VSI krijoi strukturën dhe baseline-in. Algoritmet Greedy, Local Search dhe Upper Bound u zhvilluan me ndihmën e ChatGPT dhe u testuan në projekt. Studenti duhet të kuptojë e të shpjegojë kodin dhe eksperimentet në prezantim. Rezultatet reale janë ato që raporton skedari `results/metrics.csv`.

{MARKER_END}
"""


def upsert_readme(section: str) -> None:
    content = README.read_text(encoding="utf-8") if README.exists() else "# Luna Tomato Logistics\n"
    if MARKER_START in content and MARKER_END in content:
        before, remaining = content.split(MARKER_START, 1)
        _, after = remaining.split(MARKER_END, 1)
        new_text = before.rstrip() + "\n\n" + section.strip() + "\n" + after
    elif MARKER_START in content or MARKER_END in content:
        raise SystemExit("README contains an incomplete analysis marker; no changes made.")
    else:
        new_text = content.rstrip() + "\n\n" + section.strip() + "\n"
    backup_once(README)
    README.write_text(new_text, encoding="utf-8")


def update_decisions() -> None:
    DECISIONS.parent.mkdir(parents=True, exist_ok=True)
    content = DECISIONS.read_text(encoding="utf-8") if DECISIONS.exists() else "# Design decisions log\n"
    if DECISION_MARKER in content:
        return
    decision = f"""

{DECISION_MARKER}
## {date.today().isoformat()} — Greedy + Local Search (1-nga-2 swap) me shortlist

- **Çka:** Baseline Random Search u krahasua me Greedy; pastaj u shtua Local Search që provon zëvendësimin e një transferi me dy transfere kompatibile.
- **Pse:** Greedy është i shpejtë por mund të bllokojë dy transfere me peshë totale më të lartë. Kërkimi lokal mund të përmirësojë zgjidhjen pa thyer kufizimet E/L/D.
- **Vendim praktik i implementimit:** `limit_per_transfer = 35` dhe buxhet kohor për të shmangur kërkimin shumë të kushtueshëm në Matching II. Ky është kompromis shpejtësi/cilësi dhe duhet testuar me vlera të tjera përpara pretendimeve për optimalitet.
- **Kompleksiteti:** Greedy `O(n log n)`; Local Search me `r` raunde, `s` transfere të zgjedhura dhe `k=35` kandidatët e shkurtuar: `O(r*(n log n + s*k²))` si kufi i sipërm i përgjithshëm.
- **Alternativa të konsideruara:** Random Search (shpesh 0 pikë), Greedy pa përmirësim, kërkim lokal pa shkurtim (më i kushtueshëm).
- **Provat:** Testet automatike dhe `results/metrics.csv`; përpara dorëzimit verifiko rezultatet me vlerësuesin zyrtar të ESA-s.
- **Origjina:** Vendimi dhe implementimi janë zhvilluar gjatë punës së studentit me asistencën e ChatGPT; studenti duhet të kuptojë e të justifikojë çdo zgjedhje në mbrojtje.
"""
    backup_once(DECISIONS)
    DECISIONS.write_text(content.rstrip() + decision, encoding="utf-8")


def main() -> None:
    required = [ROOT / "src" / "algorithms.py", ROOT / "src" / "upper_bound.py", ROOT / "docs" / "REQUIREMENTS.md"]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise SystemExit("Kjo nuk duket rrënja e projektit Luna Tomato. Mungojnë: " + ", ".join(missing))
    _, table = read_metrics()
    upsert_readme(analysis_text(table, read_upper_bounds()))
    update_decisions()
    print("OK: README.md u pasurua me pseudokod, kompleksitet dhe rezultatet e matura.")
    print("OK: docs/DECISIONS.md u përditësua me arsyetimin e algoritmeve.")
    print("Kopjet rezervë: README.md.bak dhe docs/DECISIONS.md.bak (nëse ekzistonin).")
    print("Asnjë algoritëm, test apo checkbox i REQUIREMENTS nuk u ndryshua.")


if __name__ == "__main__":
    main()
