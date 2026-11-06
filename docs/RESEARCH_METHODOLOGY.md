# Research Methodology

## Research questions
1. What is the observed distribution of recorded multipliers?
2. How uncertain are empirical threshold rates?
3. Is there evidence of serial association in a supplied sample?
4. Can a published commitment be checked after its matching reveal?

## Data quality
Record source, timestamp, round identifier, multiplier, verification status, and protocol version where available. Keep synthetic, observed, and independently verified data clearly separated. Never silently merge them.

## Descriptive analysis
Report sample size, mean, median, quantiles, standard deviation, and threshold counts. Use Wilson score intervals for binomial threshold proportions.

## Dependence
Lag-1 correlation is exploratory only. It does not establish independence or predictability. A proper study should pre-register tests, account for multiple comparisons, use adequate sample sizes, and validate findings on held-out data.

## Cryptographic verification
A SHA-256 commitment/reveal check is valid only if the platform's exact commitment protocol is SHA256(seed). Real games may hash additional inputs, encode strings differently, or use a multi-stage algorithm. Do not claim platform verification from this helper alone.

## Ethics
No real-money wagers, automated betting, account access, bypasses, or claims of guaranteed prediction are part of this project.
