# NHANES: รายงานกลุ่มที่ 16

Python code สำหรับวิเคราะห์ข้อมูล สร้าง figures และจัดทำรายงานภาษาไทยสามเรื่อง
ใช้ English technical terms ในเนื้อหา tables และ figures

| เรื่อง | Research questions |
| --- | --- |
| Sedentary time กับ pulse rate | เปรียบเทียบ mean pulse rate ระหว่าง sedentary time <8 และ ≥8 h/day; ตรวจ continuous association; ประเมิน adjusted association เมื่อรวม age, sex, BMI และ smoking status |
| Age และ sex กับ haemoglobin | เปรียบเทียบ mean haemoglobin ระหว่าง Male และ Female; ตรวจ joint age association; เปรียบเทียบ linear age slopes ระหว่าง sex |
| Arm circumference กับ body weight | เปรียบเทียบ mean arm circumference ระหว่าง Male และ Female; ตรวจ association กับ body weight; ประเมิน adjusted association เมื่อรวม height, age และ sex |

รายงานทั้งสามเป็นทางเลือกสำหรับงานเดียวกัน ตาม instruction ให้ส่งหนึ่ง PDF ต่อกลุ่ม

ปรับตามเกณฑ์เพิ่มเติมเมื่อ 16 October 2026: เนื้อหาหลักไม่เกิน 2,500 คำ,
table captions อยู่ด้านบน และ figure captions อยู่ด้านล่าง ใช้ Vancouver เรียงตาม
ลำดับที่อ้างครั้งแรกทั้งรายงาน ตรวจต้นฉบับตาม [reference audit](REFERENCE_AUDIT.md)
Discussion เปรียบเทียบผล วิธีเก็บข้อมูล จุดแข็ง และข้อจำกัดของงานเดิมกับ teaching subset นี้

| Report | Main words | PDF pages | References |
| --- | ---: | ---: | ---: |
| Sedentary time / pulse rate | 1,768 | 11 | 10 |
| Age / sex / haemoglobin | 1,815 | 11 | 9 |
| Arm circumference / body weight | 1,833 | 11 | 9 |

นับคำด้วย Node `Intl.Segmenter(th, word)` เฉพาะ prose และ headings ตั้งแต่ Introduction
ถึง Conclusion โดยไม่รวม tables, captions, references และ appendices
จำนวนคำภาษาไทยอาจต่างกันเล็กน้อยตาม program ที่ใช้

## สมาชิก

| ชื่อ | หน้าที่หลัก |
| --- | --- |
| ธนาพัทธ์ จันทร์ธีร | Hypothesis testing, regression และ assumption checks |
| จิรเดช ศรีโนนยาง | Data preparation, missing data และ outlier checks |
| วีรภาพ คืนดี | Literature review, introduction, discussion และการจัดรูปแบบรายงาน |
| ณัฐพัชร์ ทัศนะเมธี | Descriptive statistics, tables, figures และ results |

## สร้างผลวิเคราะห์และรายงาน

ใช้ Python 3.11 และติดตั้ง packages ตาม versions ใน `requirements.txt`
การสร้าง PDF และ figures ใช้ Windows, Tahoma และ Node.js ที่รองรับ `Intl.Segmenter`
ชุดรายงานนี้ตรวจด้วย Python 3.11.5 และ Node.js 24.15.0

วาง CSV ทั้งสองไฟล์ใน `data/` ตาม [คำอธิบายข้อมูล](data/README.md) แล้วรันจาก root ของ repo:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe run.py
```

Program ทำงานตามลำดับ: analysis → numerical validation → figures → PDF/Word → document validation → ZIP
ไฟล์สำหรับส่งอยู่ใน `deliverables/group16/`:

- `Group16_01_Sedentary_Time_and_Pulse.pdf`
- `Group16_02_Age_Sex_and_Haemoglobin.pdf`
- `Group16_03_Arm_Circumference_and_Body_Weight.pdf`

แต่ละเรื่องมี Word file ชื่อเดียวกันสำหรับแก้ไข
ZIP `NHANES_Group16_Final_Reports.zip` รวม reports, code, input CSVs และ validation outputs
พร้อม SHA-256 manifest สำหรับตรวจทุกไฟล์

หากต้องการเฉพาะ analysis ใช้ได้บนระบบที่ติดตั้ง Python และ packages สองรายการนี้:

```powershell
python -m pip install -r requirements-analysis.txt
python run.py --analysis-only
```

Full-precision output อยู่ใน `reports/group16/*/results.json`
ส่วน `plot_data.npz` เก็บ arrays ที่ใช้สร้าง figures และตรวจ models
Program ใช้ Tahoma จาก `C:/Windows/Fonts` หรือ directory ที่กำหนดด้วย `THAI_FONT_DIR`
โดยต้องมี `tahoma.ttf` และ `tahomabd.ttf`; font files ไม่ได้รวมใน repo

## Code

| File | หน้าที่ |
| --- | --- |
| `run.py` | ตรวจ inputs และรันแต่ละขั้นตอน |
| `tools/analyze.py` | กำหนด research questions และคำนวณทั้งสาม analyses |
| `tools/data_utils.py` | อ่าน CSV และเลือก analysis-specific complete cases |
| `tools/stats_core.py` | Welch, Spearman, bootstrap, OLS, HC3 และ diagnostic calculations |
| `tools/verify_analysis.py` | ตรวจตัวเลขด้วย QR decomposition, leave-one-out refits และ raw CSV reconciliation |
| `tools/make_figures.py`, `tools/plotting.py` | สร้าง 12 figures ด้วย Matplotlib ทั้ง PNG และ vector PDF |
| `tools/build_reports.py` | เนื้อหารายงานและ tables จากผลวิเคราะห์ |
| `references.json`, `tools/bibliography.py` | Bibliographic metadata และ Vancouver numbering |
| `tools/report_io.py`, `tools/thai_report_io.py`, `tools/segment_thai.mjs` | สร้าง PDF, Word, HTML และ Markdown พร้อม Thai word segmentation |
| `tools/check_reports.py` | ตรวจข้อความ tables, captions, links, names, group number และขอบหน้า PDF |
| `tools/package_reports.py` | รวมไฟล์ที่ตรวจแล้วและสร้าง SHA-256 manifest |

หลังแก้เฉพาะเนื้อหารายงาน โดยมีผลวิเคราะห์และ figures อยู่แล้ว รัน:

```powershell
python tools/build_reports.py
python tools/check_reports.py
python tools/package_reports.py
```

## Statistical methods และ validation

ใช้ analysis-specific complete cases โดยไม่ทำ imputation และไม่ลบ outliers
Primary tests ใช้ Welch’s t-test, Spearman correlation หรือ OLS-HC3 ตามคำถาม
ปรับ p-values ด้วย Holm correction ภายในแต่ละรายงาน ส่วน 95% CIs เป็น nominal intervals
Paired bootstrap ใช้ 2,000 resamples ด้วย seeds 6101 และ 6301
รายละเอียด models และ sensitivity analyses อยู่ใน [analysis plan](ANALYSIS_PLAN.md)

ตรวจ normality ด้วย Jarque–Bera แยกกลุ่มและ model residuals รวมถึง correlation inputs
ตรวจ group variances ด้วย Brown–Forsythe และ regression heteroscedasticity ด้วย Koenker
ทุกกลุ่มมี n>2,000 จึงคง Welch สำหรับ mean difference และ OLS-HC3 สำหรับ linear summary
ตาม large-sample rationale พร้อมรายงาน skewness, Q–Q plots และ sensitivity analyses
Correlation ใช้ Spearman เพียงวิธีเดียว ไม่มี Pearson ซ้ำใน variable pair เดียวกัน

Numerical validation มี 98 checks ครอบคลุม input hashes, complete-case IDs, coefficients,
HC3 standard errors, Welch statistics, tied ranks, Holm adjustment, normality moments,
Brown–Forsythe, Koenker และ ID overlap audit
Document validation ตรวจทั้งสามรายงาน รวมถึงตำแหน่ง captions ใน PDF/Word, citation order,
hyperlink targets และขนาดตัวอักษรใน vector figures พร้อมสร้าง preview สำหรับตรวจ layout
กราฟไม่มี internal titles; final axis labels 10 pt และ ticks 9.5 pt เทียบกับ main text 10.5 pt
ผลตรวจอยู่ใน `outputs/`

ข้อมูลไม่มี sample weights, strata หรือ PSUs จึงรายงาน unweighted sample associations
ผลไม่ใช่ national estimates และไม่ยืนยัน causality
Unique IDs และ group overlap=0 แสดงว่าไม่มี repeated records หรือ paired groups
แต่ยืนยัน household/PSU independence ไม่ได้; inference จึงขึ้นกับ working assumption นี้

## GitHub

Code อยู่ที่ [enchantedglycerin/nhanes-group16-analysis](https://github.com/enchantedglycerin/nhanes-group16-analysis)
เป็น private repository เก็บ code, analysis plan, reference catalogue และข้อมูลสมาชิก
Input CSVs, generated reports และไฟล์ environment ถูกยกเว้นจาก Git
`publish.ps1` เป็น helper สำหรับ initial publication ของ checkout ที่ยังไม่มี `origin`
ส่วน repo นี้ใช้ `git push` ตามปกติ

