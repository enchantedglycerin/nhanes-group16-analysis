# NHANES: รายงานกลุ่มที่ 16

Python code สำหรับวิเคราะห์ข้อมูล สร้าง figures และจัดทำรายงานภาษาไทยสามเรื่อง
ใช้ English technical terms ในเนื้อหา tables และ figures

| เรื่อง | Research questions |
| --- | --- |
| Sedentary time กับ pulse rate | เปรียบเทียบ mean pulse rate ระหว่าง sedentary time <8 และ ≥8 h/day; ตรวจ continuous association; ประเมิน adjusted association เมื่อรวม age, sex, BMI และ smoking status |
| Age และ sex กับ haemoglobin | เปรียบเทียบ mean haemoglobin ระหว่าง Male และ Female; ตรวจ joint age association; เปรียบเทียบ linear age slopes ระหว่าง sex |
| Arm circumference กับ body weight | เปรียบเทียบ mean arm circumference ระหว่าง Male และ Female; ตรวจ association กับ body weight; ประเมิน adjusted association เมื่อรวม height, age และ sex |

รายงานทั้งสามเป็นทางเลือกสำหรับงานเดียวกัน ตาม instruction ให้ส่งหนึ่ง PDF ต่อกลุ่ม

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
| `tools/make_figures.py`, `tools/plotting.py` | สร้าง 12 figures |
| `tools/build_reports.py` | เนื้อหารายงานและ tables จากผลวิเคราะห์ |
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

Numerical validation มี 51 checks ครอบคลุม input hashes, complete-case IDs, coefficients,
HC3 standard errors, Welch statistics, tied ranks, Holm adjustment และ analysis-plan hash
Document validation ตรวจทั้งสามรายงานและสร้างภาพ preview สำหรับตรวจ layout
ผลตรวจอยู่ใน `outputs/`

ข้อมูลไม่มี sample weights, strata หรือ PSUs จึงรายงาน unweighted sample associations
ผลไม่ใช่ national estimates และไม่ยืนยัน causality

## GitHub

Repo เก็บ code, analysis plan และข้อมูลสมาชิกที่ใช้สร้างรายงาน
Input CSVs, generated reports และไฟล์ environment ถูกยกเว้นจาก Git
การสร้าง repo บน GitHub ใช้ GitHub CLI ที่ login แล้ว:

```powershell
gh auth login --hostname github.com
.\publish.ps1
```

`publish.ps1` สร้าง **private repository** ชื่อ `nhanes-group16-analysis` ใน account ที่ใช้งานอยู่
และ push commit จาก local repo นี้ หากมี `origin` อยู่แล้ว script จะหยุดก่อนเปลี่ยน remote

