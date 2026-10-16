# Reference audit

Reviewed on 16 October 2026. The three reports use Vancouver numbering in order of
first citation. Journal entries use abbreviated journal names, publication year,
volume(issue), full page range or article number, and DOI. Entries with more than
six authors list the first six followed by “et al.” Official web documentation uses
a corporate author, title, `[Internet]`, access date, and URL. The formatting follows
the [NLM examples](https://www.nlm.nih.gov/bsd/uniform_requirements.html).

`references.json` is the shared catalogue. Every reference appears in the report
that uses it; numbering is generated from the prose. Each report also exports
`references_used.json`. The document checks verify numbering and the actual PDF
and Word hyperlink targets.

## Journal articles

For all eight articles, the title, full author list, publication year, volume,
issue, pages/article number and DOI were checked against publisher-deposited
Crossref metadata. Original article content or its author-supplied abstract was
checked using the sources below. DOI links in the reports identify the original
article, including where a publisher has changed. Some publisher pages restrict
automated access; metadata verification is not a claim that every publisher URL
returned an unrestricted full text.

| Reference | Original article / reviewed source | Checks affecting the reports |
| --- | --- | --- |
| Beijer et al., 2018 | [Publisher article](https://ujms.net/index.php/ujms/article/view/5793), DOI `10.1080/03009734.2018.1540505` | Seven authors; 47,457 participants; TV time differs from total sedentary time. The study adjusts for physical activity. |
| McGregor et al., 2018 | [Publisher version held by the authors’ university](https://researchonline.gcu.ac.uk/ws/files/26454511/ijerph_15_01779_v2.pdf), DOI `10.3390/ijerph15081779` | Title uses “Canadian Health Measure Survey.” Table 1 reports sedentary/resting-heart-rate p=0.301 in adults. Waking behaviours use accelerometry, sleep uses self-report, and inference accounts for survey design. |
| Nah et al., 2020 | [Original abstract and journal record](https://pubmed.ncbi.nlm.nih.gov/32048801/), DOI `10.1111/ijlh.13160` | Six authors; 1,159,298 health-checkup participants from 16 centres in 13 cities. Means 15.29 and 13.25 g/dL. Discussion does not infer a country effect. |
| Su et al., 2023 | [Publisher article](https://link.springer.com/article/10.1186/s12902-022-01218-w) | Article 8 in volume 23; publication year 2023 despite “2022” in the DOI. The Female increase at ages 50–59 is qualified by the non-hyperglycaemic subgroup. The discussion identifies spline modelling, selection and exclusions. |
| Cattermole et al., 2017 | [Original abstract and journal record](https://pubmed.ncbi.nlm.nih.gov/27993936/), DOI `10.1136/emermed-2015-205623` | Final issue is 2017, although published online in 2016. Adult derivation/validation samples are 5,595/6,049; validation uses a different NHANES cycle. |
| Cattermole and Wells, 2021 | [Original open-access article](https://pmc.ncbi.nlm.nih.gov/articles/PMC8295032/), DOI `10.1002/emp2.12515` | Table 3: MAC P10/P20=62.3/90.9%; Lorenz=86.8/99.4%. The 2021 journal name is retained even though the current DOI destination is a new publisher. |
| Delacre et al., 2017 | [Original article](https://doi.org/10.5334/irsp.82), [authors’ institutional record](https://research.tue.nl/en/publications/why-psychologists-should-by-default-use-welchs-t-test-instead-of-/) | Supports Welch as the default mean comparison without using a variance pretest to choose Student versus Welch. |
| Lumley et al., 2002 | [Original publisher abstract](https://www.annualreviews.org/content/journals/10.1146/annurev.publhealth.23.100901.140546) | Supports large-sample mean inference under non-normality; does not remove the independence requirement. |

## Official documentation

| Source | Verified scope |
| --- | --- |
| [CDC sample-design overview](https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/OverviewBrief.aspx?Cycle=2021-2023) | NHANES August 2021–August 2023; weighting, clustered sampling and nonresponse. |
| [DEMO_L](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm) | RIDAGEYR records all ages 80 and above as 80. |
| [PAQ_L](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/PAQ_L.htm) | Sedentary-time item excludes sleeping. |
| [BPXO_L](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPXO_L.htm) | Oscillometric measurements after five minutes of seated rest. |
| [CBC_L](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/CBC_L.htm) | LBXHGB in g/dL; missing measurements and phlebotomy weights. |
| [BMX_L](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.htm) | BMXARMC, BMXWT and BMXHT measurement definitions. |
| [statsmodels HC3 documentation](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.HC3_se.html) | HC3 covariance formula; the project implements the formula rather than using statsmodels. |
| [SciPy Jarque–Bera documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.jarque_bera.html) | Asymptotic chi-square with 2 df and the large-sample condition n>2,000. The project implements the formula rather than using SciPy. |

The discussion distinguishes results reported by each article from possible
explanations for differences between samples. Those explanations are not presented
as mechanisms established by this teaching dataset. No downloaded article text is
included in the Git repository or the report package.
