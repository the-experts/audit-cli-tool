# audit-cli

Opdrachtregelgereedschap voor het genereren van kwaliteitsdiagrammen vanuit SonarQube. Exporteert interactieve HTML-rapporten of statische PNG-afbeeldingen.

---

## Installatie

```bash
pip install -e .
```

Voor PNG-export is kaleido vereist:

```bash
pip install -e ".[png]"
```

**Vereisten:** Python 3.10 of hoger.

---

## Configuratie

De tool heeft een SonarQube-URL en een toegangstoken nodig. Deze kunnen als omgevingsvariabelen worden ingesteld zodat je ze niet bij elke opdracht hoeft mee te geven:

```bash
export SONAR_URL=https://sonar.jouworganisatie.nl
export SONAR_TOKEN=squ_xxxxxxxxxxxxxxxx
```

Of geef ze rechtstreeks mee als opties:

```bash
audit --url https://sonar.jouworganisatie.nl --token squ_xxx <commando>
```

---

## Algemene opties

De meeste commando's ondersteunen de volgende opties:

| Optie | Standaard | Omschrijving |
|---|---|---|
| `--url` | `$SONAR_URL` | URL van de SonarQube-instantie |
| `--token` | `$SONAR_TOKEN` | SonarQube-toegangstoken |
| `-o`, `--output` | `sonar-reports/` | Uitvoermap voor de gegenereerde bestanden |
| `-f`, `--format` | `html` | Uitvoerformaat: `html` of `png` |
| `--project` | — | Beperk tot één projectsleutel |
| `--prefix` | — | Beperk tot projecten waarvan de sleutel begint met dit voorvoegsel |

---

## Commando's

### `summary` — Systeemeigenschappen

Overzichtstabel met de belangrijkste kengetallen van het systeem.

```bash
audit summary
audit summary --prefix mijn-systeem
```

**Toont:**
- Aantal modules
- Aantal regels code (excl. commentaar)
- Gemiddelde testdekking (gewogen naar modulegrootte)
- Aandeel programmeertalen
- Geschatte ontwikkelkosten (in mensdagen, op basis van 150 LOC/dag)
- Geschatte technische schuld (in mensdagen)
- Aantal problemen / potentiële bugs
- Aantal geschatte veiligheidsissues (kwetsbaarheden + hotspots)
- Hoeveelheid duplicate code

---

### `health` — Gezondheidsoverzicht per project

Geeft per project de Quality Gate-status, bugs, kwetsbaarheden en testdekking.

```bash
audit health
audit health --prefix mijn-systeem
```

---

### `debt-coverage` — Technische schuld vs. testdekking

Bellendiagram met op de horizontale as de technische schuld (in dagen), op de verticale as de testdekking (in %), waarbij de belgrootte de moduleomvang weergeeft en de kleur de slechtste betrouwbaarheids- of veiligheidsrating.

De grafiek toont drie zones:
- **Hoge kwaliteit** — lage schuld, goede dekking
- **Gemiddelde kwaliteit** — middelmatig
- **Aandacht vereist** — hoge schuld en/of lage dekking

```bash
audit debt-coverage
audit debt-coverage --prefix mijn-systeem
```

---

### `matrix` — Geaggregeerde projectmatrix

Kleurgecodeerde heatmap van alle projecten × kwaliteitsmetrieken. Projecten worden gesorteerd van beste naar slechtste totaalscore.

```bash
audit matrix
audit matrix --prefix mijn-systeem
```

---

### `radar` — Kwaliteitsradar per project

Pentagoon-radar per project met vijf dimensies: betrouwbaarheid, veiligheid, onderhoudbaarheid, testdekking en duplicatie. Maximaal drie radardiagrammen per rij.

```bash
audit radar
audit radar --prefix mijn-systeem
```

---

### `ratings` — Ratingsverdeling

Verdeling van A–E-ratings voor betrouwbaarheid, veiligheid en onderhoudbaarheid over alle projecten.

```bash
audit ratings
```

---

### `risk` — Risicomatrix

Spreidingsdiagram met bugs op de horizontale as en kwetsbaarheden op de verticale as. Belgrootte geeft de moduleomvang aan; kleur geeft de Quality Gate-status weer.

```bash
audit risk
```

---

### `issues` — Problemen per type en ernst

Staafdiagrammen met het totaal aantal issues opgesplitst naar type (bug / kwetsbaarheid / code smell) en ernst (blocker / critical / major / minor / info).

```bash
audit issues
audit issues --prefix mijn-systeem
```

---

### `violations` — Overtredingen per ernst per project

Gestapeld staafdiagram van alle overtredingen per project, opgesplitst naar ernst.

```bash
audit violations
```

---

### `debt` — Technische schuld heatmap

Heatmap van SQALE-ratings (A–E) per project en dimensie.

```bash
audit debt
```

---

### `coverage` — Dekking en duplicatie

Bellendiagram van testdekking versus duplicatie per project.

```bash
audit coverage
```

---

### `security` — Kwetsbaarhedenverdeling

OWASP Top 10-verdeling, ernstverdeling en hotspot-overzicht voor het gehele portfolio.

```bash
audit security
audit security --prefix mijn-systeem
```

---

### `security-projects` — Veiligheid per project

Kwetsbaarheden en hotspots per project, inclusief herstelinspanning.

```bash
audit security-projects
```

---

### `remediation` — Herstelinspanning

Schatting van de hersteltijd per project, opgesplitst naar issuetype.

```bash
audit remediation
```

---

### `trend` — Trend over tijd

Lijndiagram van geselecteerde metrieken voor één project over de tijd.

```bash
audit trend MIJN-PROJECT-KEY
audit trend MIJN-PROJECT-KEY --metric bugs --metric coverage --from 2024-01-01
```

Beschikbare metrieken: `bugs`, `vulnerabilities`, `code_smells`, `coverage`, `duplicated_lines_density`, `sqale_index`, `security_hotspots`, `ncloc`.

---

### `ownership` — Eigenaarschapskaart

Quality Gate-slagingspercentage, schuld en issues per team, op basis van een YAML-configuratiebestand.

```bash
audit ownership --teams teams.yaml
```

Voorbeeld `teams.yaml`:

```yaml
teams:
  - name: Team Alpha
    projects:
      - mijn-systeem-module-a
      - mijn-systeem-module-b
  - name: Team Beta
    projects:
      - mijn-systeem-module-c
```

---

### `git` — Git-geschiedenis

Commits per dag, activiteitsheatmap (weekdag × uur) en cumulatieve groei. Ondersteunt meerdere repository's tegelijk. Bevat dropdowns om te filteren op auteur en/of repository.

```bash
audit git --repo /pad/naar/repo
audit git --repo /pad/naar/repo-a --repo /pad/naar/repo-b --since "180 days ago"
```

| Optie | Standaard | Omschrijving |
|---|---|---|
| `-r`, `--repo` | `.` | Pad naar een git-repository (herhaalbaar) |
| `--since` | `90 days ago` | Beginpunt van de geschiedenis (git-datumformaat) |
| `-o`, `--output` | `sonar-reports/` | Uitvoermap |
| `-f`, `--format` | `html` | `html` of `png` |

Auteurs die onder meerdere namen committen worden via e-mailadres samengevoegd (mailmap-logica).

---

### `all` — Alles in één keer

Genereert alle bovenstaande diagrammen in één opdracht.

```bash
audit all
audit all --prefix mijn-systeem --format png
audit all --prefix mijn-systeem --teams teams.yaml
```

---

## Voorbeelden

```bash
# Alle diagrammen voor projecten met prefix "myapp"
audit all --prefix myapp

# Alleen de systeemeigenschappentabel als PNG
audit summary --prefix myapp --format png

# Git-analyse van twee repo's over het afgelopen jaar
audit git --repo ../repo-a --repo ../repo-b --since "1 year ago"

# Trend van één project
audit trend myapp-backend --metric bugs --metric coverage --from 2024-01-01
```

---

## Uitvoer

Alle bestanden worden opgeslagen in de uitvoermap (standaard `sonar-reports/`). Bij HTML-uitvoer bevat elk bestand interactieve Plotly-grafieken. Bij PNG-uitvoer worden afbeeldingen op hoge resolutie (1600 px breed) weggeschreven.

| Bestand | Inhoud |
|---|---|
| `summary.html` | Systeemeigenschappentabel |
| `health_overview.html` | Gezondheidsoverzicht per project |
| `debt_coverage.html` | Technische schuld vs. testdekking |
| `project_matrix.html` | Geaggregeerde projectmatrix |
| `radar.html` | Kwaliteitsradars |
| `ratings_distribution.html` | Ratingsverdeling A–E |
| `risk_matrix.html` | Risicomatrix |
| `issues_breakdown.html` | Problemen per type en ernst |
| `violations.html` | Overtredingen per project |
| `debt_heatmap.html` | Technische schuld heatmap |
| `coverage_landscape.html` | Dekking en duplicatie |
| `security_dist.html` | Kwetsbaarhedenverdeling |
| `security_per_project.html` | Veiligheid per project |
| `remediation.html` | Herstelinspanning |
| `git_history.html` | Git-geschiedenis |
| `ownership_map.html` | Eigenaarschapskaart (alleen met `--teams`) |
