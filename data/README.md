# ข้อมูลที่ใช้

วาง CSV ที่ได้รับทั้งสองไฟล์ไว้ใน directory นี้ โดยคงชื่อและเนื้อหาเดิม:

| File | SHA-256 |
| --- | --- |
| `NHANES_BME_student - NHANES_BME_student.csv` | `ee2bd4d6bccb4860967fbb1cf7d4af510a5ebfddd4911fe6d0cd155738cd8c09` |
| `NHANES_BME_codebook - NHANES_BME_codebook.csv` | `1653074b1b5c721ce74511da21fe658c0ff62caa000ed980f1ee051af911920b` |

Participant CSV มี 8,153 records และ 26 variables เป็น teaching extract ของ NHANES 2021–2023
Program ตรวจ SHA-256 ก่อนวิเคราะห์ เพื่อให้ใช้ข้อมูลชุดเดียวกับรายงาน
CSV ทั้งสองไฟล์ถูกยกเว้นจาก Git ด้วย `.gitignore` แต่รวมอยู่ใน ZIP สำหรับสร้างรายงานซ้ำ

