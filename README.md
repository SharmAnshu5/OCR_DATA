# RO Intelligence – OCR-Based RO Extraction Pipeline

RO Intelligence is an end-to-end OCR system designed to extract, validate, and persist structured data from RO (Release Order) PDFs.  
The pipeline supports **70+ document formats** using layout-aware OCR, schema-driven field resolution, and rule-based validation.

---

## 🔁 High-Level Processing Flow

PDF  
└── Ingestion  
&nbsp;&nbsp;&nbsp;&nbsp;└── Layout-aware OCR  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── Schema-based Field Resolver  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── Validation Engine  
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── SQL Storage (Raw + Canonical)

---

## 🧭 Document Layout Understanding

The OCR engine uses layout positioning and contextual grouping to identify RO fields accurately.

---
```
┌───────────────┬──────────────────────┐
│ Left menu     │ RO Code / RO Date    │
│ navigation    │ Client Detail        │
│               │ Newspaper Details    │
├───────────────┴──────────────────────┤
│ Details of Advertisement             │
└──────────────────────────────────────┘
```
---

## 📂 Project Structure
```
ro-intelligence/
│
├── ingestion/
│   ├── pdf_loader.py
│   └── image_converter.py
│
├── ocr/
│   ├── tesseract_engine.py
│   ├── layout_extractor.py
│   └── confidence_utils.py
│
├── schema/
│   ├── ro_v1.json
│   ├── ro_v2.json
│   └── schema_engine.py
│
├── extraction/
│   ├── label_matcher.py
│   ├── position_resolver.py
│   └── fallback_regex.py
│
├── validation/
│   ├── business_rules.py
│   └── anomaly_detector.py
│
├── persistence/
│   ├── db.py
│   ├── insert_raw.py
│   └── insert_canonical.py
│
├── audit/
│   └── extraction_audit.py
│
├── airflow/
│   └── ro_pipeline_dag.py
│
└── main.py
```
---

## ⚙️ Technology Stack

- OCR Engine: Tesseract (layout-aware)
- Computer Vision: OpenCV
- Schema Resolution: JSON-based schemas
- Validation: Rule-based + anomaly detection
- Database: SQL (Raw + Canonical)
- Orchestration: Apache Airflow
- Language: Python

---

## 📦 Installation

```
pip install ultralytics opencv-python
```
---

## 🚀 GitHub Commands

```
git init
git remote add origin https://github.com/SharmAnshu5/OCR_DATA.git
git pull -u origin main
git add .
git commit -m "Initial OCR pipeline setup"
git push -u origin main

```
---

## ✅ Key Features

- Supports 70+ RO formats  
- Layout-aware OCR extraction  
- Schema-versioned field resolution  
- Robust fallback mechanisms  
- Business-rule validation  
- Raw and canonical data storage  
- Full audit trail  
- Automation-ready pipeline  

---

## 📌 Use Case

Designed for large-scale RO document processing where format variability, accuracy, and traceability are critical—ideal for media, publishing, and advertising workflows.
