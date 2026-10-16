# Analysis plan: NHANES Group 16

## 1. Sedentary time and pulse rate

1. Does mean pulse rate differ between sedentary time <8 and >=8 h/day?
2. Is continuous sedentary time associated with pulse rate?
3. What is the pulse-rate difference per additional hour of sedentary time
   after adjustment for age, sex, BMI and smoking status?

Use Welch's t-test (>=8 minus <8), tied Spearman correlation with a paired
percentile bootstrap CI, and OLS with HC3 covariance. The 8-hour split is a
preselected descriptive contrast, not a diagnostic or guideline threshold.
The continuous analyses avoid relying solely on that split. Sensitivity:
add squared sedentary time and age terms, and restrict recorded age to <80.
Missing physical activity, sleep and medication variables limit interpretation.

## 2. Age, sex and haemoglobin

1. Does mean haemoglobin differ between recorded Male and Female groups?
2. Is age associated with haemoglobin when sex and age-by-sex interaction
   are included (joint test of both age coefficients)?
3. Do the linear age slopes differ between the two sex groups?

Use Welch's t-test (Male minus Female) and OLS with age centred at 50 years,
per decade, sex, and age-by-sex interaction, with HC3 covariance. Report both
sex-specific slopes and their CIs. Sensitivity: squared age and its interaction
with sex; also refit the primary model at age <80 to assess top-coding.
Do not interpret cross-sectional slopes as within-person ageing or diagnose
anaemia. Pregnancy, menstruation, iron status and renal function are unavailable.

## 3. Arm circumference and body weight

1. Does mean arm circumference differ between recorded Male and Female groups?
2. Is arm circumference associated with measured body weight?
3. What is the weight difference per 5 cm arm circumference after adjustment
   for height, age and sex?

Use Welch's t-test (Male minus Female), tied Spearman correlation with a paired
bootstrap CI, and OLS-HC3 for body weight. Sensitivity: squared arm circumference
and its interaction with sex; refit the primary model at age <80. Report residual
RMSE descriptively. This is an association study, not a validated weight-estimation
device; there is no independent prediction-validation dataset.

## Shared decisions

- Exactly three related questions per report. Holm correction over those three
  primary tests, with nominal 95% CIs; sensitivity tests are exploratory.
- Complete cases per analysis, report missingness and sample sizes. Never
  replace missing data with zero or drop rows missing unrelated measurements.
- Means/SDs, medians/Q1/Q3, frequency/percentage, ranges and IQR flags.
- At least two substantive figures plus residual–fitted and Q–Q diagnostics.
- Brown–Forsythe, residual skewness, Koenker diagnostic and Cook's distance.
  Flagged observations stay in the analysis; independence is a working
  assumption because survey design information is absent.
- Report Jarque–Bera normality tests separately for both comparison groups,
  primary-model residuals and the continuous variables used for Spearman.
  These samples exceed 2,000; use the asymptotic chi-square reference with 2 df.
- Welch comparisons target mean differences. Retain large-sample mean inference
  after assessing shape, group sizes and variance; do not automatically switch
  estimands following a normality or equal-variance pretest. OLS-HC3 estimates
  a linear mean summary, with the existing nonlinear sensitivity models.
- Audit unique participant IDs for each analysis and zero overlap between
  comparison groups. This checks record structure, not survey-cluster
  independence. Household and PSU dependence cannot be verified from these CSVs.
  Independence concerns observations, not absence of association between the
  predictor and outcome. Do not report an independence p-value for an ID audit.
- Use only Spearman for each unadjusted bivariate correlation; do not add
  Pearson tests for the same pair. Assumption diagnostics remain outside the
  three-question primary Holm family.
- Paired bootstrap: 2,000 resamples; deterministic seeds 6101 and 6301.
- Unweighted teaching-extract analyses, not nationally representative estimates.
- Thai prose with English technical terms; group number 16 and four named
  members with assigned responsibilities.
- At least two medical research comparisons and statistical references in each.
- Main prose <=2,500 segmented words; conclusion 2–3 sentences.
- Vancouver numbered references in first-citation order, with verified DOI or
  original documentation links; table captions above and figure captions below.
- Figures have no internal titles. At final printed size, axis labels are 10 pt
  and tick labels 9.5 pt, compared with 10.5 pt main prose.
