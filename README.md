# NATIONVK AVIATOR RESEARCH LAB

A statistics-first educational research toolkit for studying crash-game multiplier datasets. This project does **not** predict future rounds, provide betting signals, or guarantee outcomes.

## Project goals
- Descriptive statistics: count, mean, median, min/max, quantiles, standard deviation.
- Empirical threshold frequencies with Wilson confidence intervals.
- Run-length and lag-1 exploratory checks (not proof of dependence).
- Synthetic data generation for learning and testing.
- SHA-256 commitment / reveal verification helper.
- CSV import and JSON report export.
- Preserve the original authorized-use TCP port scanner as a separate utility.

## Requirements
- Python 3.9+
- No third-party packages required.

## Browser dashboard\nOpen `dashboard.html` directly in Chrome or another browser. It includes a synthetic demo dataset, CSV import, threshold-frequency analysis, a multiplier histogram, and JSON export. No server or external JavaScript library is needed.\n\n## Run on Android (Pydroid 3 / Termux)
1. Download or clone this repository.
2. Open its folder in Pydroid 3 or Termux.
3. Run:
   ```bash
   python app.py demo --rounds 1000 --seed 42
   python app.py analyze sample_data.csv
   python app.py verify-hash --seed YOUR_REVEALED_SEED --commit YOUR_SHA256_HASH
   ```

## CSV format
A CSV file must contain a column named `multiplier`. Optional columns: `round_id`, `timestamp`, `verified`.
Only use data you are permitted to collect. Do not treat screenshots, signal channels, or unverified claims as authoritative round records.

## Commands
- `python app.py demo --rounds 1000 --seed 42` — create a reproducible synthetic dataset and analyze it.
- `python app.py analyze sample_data.csv --json report.json` — analyze CSV and save JSON report.
- `python app.py verify-hash --seed TEXT --commit HEX` — verify SHA-256 commitment/reveal equality.
- `python -m unittest discover -s tests -v` — run tests.

## Methodology and limitations
1. A historical sample describes only the sample. It does not establish the next round's outcome.
2. Empirical frequencies are estimates and include uncertainty; small samples are especially noisy.
3. A lag correlation or streak pattern alone cannot establish predictability.
4. A hash commitment can be checked only when the matching revealed seed and exact protocol are known. This helper checks SHA-256(seed) only; it does **not** reconstruct a platform's complete crash algorithm.
5. Theoretical formulas shown in research must be labelled as assumptions and verified against the exact game rules before being attributed to a specific platform.

## Responsible use
This is an educational statistics project. No real-money betting integration, auto-betting, account automation, credential collection, or guaranteed prediction feature is included.

## Existing scanner
`scan.py` remains a separate TCP port-checking utility. Use it only against systems you own or are explicitly authorized to test.

## Author
NATIONVK — YEASIEN AHMED


## Android APK (experimental)
A native Android project is available in [android/](android/). It packages the research dashboard and includes an opt-in MediaProjection screen-capture service with on-device ML Kit OCR. Android requires the user to approve every capture session and displays a persistent notification while capture is active.

To build a debug APK, open the **Actions** tab and run **Build Android APK**, or push a change under `android/`. Download the `aviator-research-lab-debug-apk` artifact from the completed workflow run. This is an unsigned debug build, not a Play Store release.

**OCR limitations:** OCR may misread values and cannot reliably distinguish the current multiplier from historical values visible on screen. Review captured observations before analysis. Screen OCR does not reveal server seeds or provide a reliable next-round prediction.
