import os
import re
import csv
import sys
from io import StringIO
import json
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from rapidfuzz import fuzz, process
from datetime import datetime
import pdfplumber
import re

from pdfminer.high_level import extract_text
try:
    from pdf2image import convert_from_path
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

PDFM_INTERPRETER_DPI = 300  
master_df = pd.read_csv("Unique _client_Name.csv", dtype=str).fillna("")

master_df["RO_NO_CLIENT_CODE"] = master_df["RO_NO_CLIENT_CODE"].astype(str).str.strip()
master_df["MASTER_CLIENT_CODE"] = master_df["MASTER_CLIENT_CODE"].astype(str).str.strip()
master_df["MASTER_CLIENT_NAME"] = master_df["MASTER_CLIENT_NAME"].astype(str).str.strip()


def load_mapping():
    mapping_path = "mapping.json"
    if not os.path.exists(mapping_path):
        print("[WARN] mapping.json not found — using empty mapping.")
        return {}

    with open(mapping_path, "r", encoding="utf-8") as f:
        return json.load(f) 
    
def extract_city_from_master(master_name):
    if not master_name:
        return ""

    name = master_name.upper()

    # Case 1: City inside brackets [CITY]
    bracket_match = re.search(r"\[(.*?)\]", name)
    if bracket_match:
        return bracket_match.group(1).strip()

    # Case 2: City after last comma
    if "," in name:
        parts = name.split(",")
        city = parts[-1].strip()
        return city

    return ""    
    
def extract_city_from_ro(text):
    if not text:
        return ""

    text = text.upper()

    # Match CITY followed by PINCODE
    match = re.search(r"\b([A-Z ]+)\s+\d{6}\b", text)
    if match:
        return match.group(1).strip()

    # Match standalone major word after comma
    matches = re.findall(r",\s*([A-Z ]+)", text)
    if matches:
        return matches[-1].strip()

    return ""    
    
def match_client(ro_client_code, ro_client_name):   
    if not ro_client_code or not ro_client_name:
        return "", ""
    ro_client_code = str(ro_client_code).strip().lstrip("0")
    ro_client_name = ro_client_name.upper()
    master_df["RO_NO_CLIENT_CODE_CLEAN"] = (
        master_df["RO_NO_CLIENT_CODE"]
        .astype(str)
        .str.strip()
        .str.lstrip("0")
    )
    filtered = master_df[
        master_df["RO_NO_CLIENT_CODE_CLEAN"] == ro_client_code
    ]
    if filtered.empty:
        return "", ""
    if len(filtered) == 1:
        row = filtered.iloc[0]
        return row["MASTER_CLIENT_NAME"], row["MASTER_CLIENT_CODE"]
    ro_city = extract_city_from_ro(ro_client_name)
    best_score = 0
    best_row = None
    for _, row in filtered.iterrows():
        master_name = row["MASTER_CLIENT_NAME"].upper()
        master_city = extract_city_from_master(master_name)
        score = max(
            fuzz.token_sort_ratio(ro_client_name, master_name),
            fuzz.partial_ratio(ro_client_name, master_name),
            fuzz.token_set_ratio(ro_client_name, master_name)
        )
        if ro_city and master_city and ro_city in master_city:
            score += 25 
        if score > best_score:
            best_score = score
            best_row = row
    if best_row is not None and best_score >= 60:
        return best_row["MASTER_CLIENT_NAME"], best_row["MASTER_CLIENT_CODE"]

    return "", ""


def remove_hindi_phrases(text):
    return re.sub(r"\([^)]*[\u0900-\u097F]+[^)]*\)", "", text)


def remove_noise(text: str) -> str:
    if not text:
        return ""
    t = text
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"[()]", " ", t)
    t = re.sub(r"[\u0900-\u097F]+", " ", t)
    t = re.sub(r"[�]+", " ", t)
    t = re.sub(
        r"GOVERNMENT OF INDIA.*?Release Order",
        " ",
        t,
        flags=re.I | re.S
    )
    t = re.sub(
        r"Please ensure.*?supplements\.",
        " ",
        t,
        flags=re.I | re.S
    )
    t = re.sub(r"\d{2}-\d{2}-\d{4},?\s*\d{2}:\d{2}", " ", t)
    t = re.sub(r",?NULL,?\s*NULL", " ", t, flags=re.I)
    t = re.sub(r"[|]+", " ", t)
    t = re.sub(r":\s*,", ":", t)
    t = re.sub(r"[^\x00-\x7F]+", " ", t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"\n\s*\n", "\n", t)
    t = re.sub(r",\s*,+", ", ", t)
    return t.strip()



def rebuild_layout_text(words, y_tolerance=3):
    lines = []
    current_line = []
    current_y = None
    for w in words:
        if current_y is None:
            current_y = w["top"]
            current_line.append(w)
            continue
        if abs(w["top"] - current_y) <= y_tolerance:
            current_line.append(w)
        else:
            current_line = sorted(current_line, key=lambda x: x["x0"])
            lines.append(" ".join(word["text"] for word in current_line))
            current_line = [w]
            current_y = w["top"]
    if current_line:
        current_line = sorted(current_line, key=lambda x: x["x0"])
        lines.append(" ".join(word["text"] for word in current_line))
    return "\n".join(lines)


def extract_colour(text):
    if not text:
        return ""
    t = str(text)
    t = t.replace("0", "o") 
    t = t.replace("1", "l")
    if re.search(r"\b(b\s*/\s*w|b\s*&\s*w)\b", t, re.IGNORECASE):
        return "B"
    if re.search(r"black\s*(and|&)?\s*white", t, re.IGNORECASE):
        return "B"
    if re.search(r"\bb[1-4]\s*[-]?\s*black", t, re.IGNORECASE):
        return "B"
    if re.search(r"full\s*(colour|color)", t, re.IGNORECASE):
        return "C"
    if re.search(r"\b(colour|color)\b", t, re.IGNORECASE):
        return "C"
    if re.search(r"\bb[1-4]\s*[-]?\s*(colour|color)", t, re.IGNORECASE):
        return "C"
    return ""


def extract_page_premium(text: str) -> str:
    if not text:
        return "0"
    t = text.replace("\n", " ")
    t = re.sub(r"\s{2,}", " ", t)
    positioning_match = re.search(
        r"Positioning/?\s*:\s*(.*?)\s*(?:Display|Advt\.|Date of Publication|$)",
        t,
        re.IGNORECASE | re.DOTALL
    )
    if positioning_match:
        pos = positioning_match.group(1).upper().strip()
        if "FIRST JACKET" in pos:
            return "FIRST JACKET"
        if "TOP PAGE" in pos:
            return "TOP PAGE"
        if "FRONT PAGE" in pos:
            return "FRONT PAGE"
        if "3RD PAGE" in pos:
            return "3RD PAGE"
        if "LAST PAGE" in pos:
            return "LAST PAGE"
        if "NA" in pos:
            return "0"
    return "0"

def extract_remarks(text):
    if not text:
        return ""
    t = text.replace("\n", " ")
    t = re.sub(r"\s{2,}", " ", t)
    pattern = (
        r"Remarks\s*:\s*(.*?)\s*"
        r"(?:Asst\. Media Executive|This is a computer generated|Cut Here|Details of Advertisement|RO Amount)"
    )
    match = re.search(
        pattern,
        t,
        flags=re.IGNORECASE | re.DOTALL
    )
    if match:
        return match.group(1).strip(" .,-")
    return ""

def extract_fields(clean_text):
    mapping = load_mapping()
    fields = {}
    basic_patterns = {
        "RO_NUMBER": r"RO Code\s*:\s*([0-9/]+)",
        "RO_DATE": r"RO Date\s*:\s*([\d\-]+)",
        "RO_AMOUNT": r"RO Amount\s*:\s*(\d+)",
        "INSERT_DATE": r"Date of Publication.*?(\d{2}-\d{2}-\d{4})",
        "AD_HEIGHT": r"Height\s*=\s*([0-9]+(?:\.[0-9]+)?)",
        "AD_WIDTH": r"Width\s*=\s*([0-9]+(?:\.[0-9]+)?)",
        "RO_RATE": r"Rate\s+per\s+Sq\.?\s*Cms\.?\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)",
    }
    for key, pattern in basic_patterns.items():
        match = re.search(pattern, clean_text, re.I | re.S)
        fields[key] = match.group(1).strip() if match else ""
    fields["RO_CLIENT_CODE"] = (
        fields["RO_NUMBER"].split("/")[0]
        if fields.get("RO_NUMBER") else ""
    )
    fields["RO_REMARKS"] = extract_remarks(clean_text)    
    if not fields["RO_REMARKS"]:
        fields["RO_REMARKS"] = "NO REMARK ON RO"
    client_match = re.search(
        r"Client Detail\s*:\s*(.*?)\s*(?:The Advertisement|Premium|Display|Date of Publication|$)",
        clean_text,
        re.I | re.S
    )
    if client_match:
        client_block = client_match.group(1).strip()
        client_block = re.sub(r",\s*,+", ", ", client_block)
        fields["RO_CLIENT_NAME"] = client_block
    else:
        fields["RO_CLIENT_NAME"] = ""
    premium_match = re.search(
        r"Premium/?\s*:\s*(.*?)\s*Positioning",
        clean_text,
        re.I | re.S
    )
    fields["PAGE_PREMIUM"] = premium_match.group(1).strip() if premium_match else "0"
    positioning_match = re.search(
        r"Positioning/?\s*:\s*(.*?)\s*(?:Display|Advt\.|Date of Publication|$)",
        clean_text,
        re.I | re.S
    )
    fields["POSITIONING"] = positioning_match.group(1).strip() if positioning_match else ""
    package_patterns = [
        r"Advertisement\s+Manager.*?AMAR\s+UJALA\s*,\s*([A-Za-z ]+?)\s*,",
        r"The\s+Advertisement\s*[:\-]\s*AMAR\s+UJALA\s*,\s*([A-Za-z ]{2,30})\b",
        r"Advertisement\s+Manager\s*[:\-]?\s*.*?,\s*([A-Za-z ]{2,30})\b",
        r"Manager\s*[:\s]+([A-Za-z ]{2,30})\b"
    ]
    pkge = ""
    for pat in package_patterns:
        match = re.search(pat, clean_text, re.I)
        if match:
            pkge = match.group(1).strip()
            break
    pkg_upper = pkge.upper() if pkge else ""
    mapped_pkg = mapping.get("PACKAGE_NAME_MAP", {}).get(pkg_upper)
    fields["PACKAGE_NAME"] = mapped_pkg if mapped_pkg else pkge
    agency_map = mapping.get("AGENCY_NAME_MAP", {})
    fields["AGENCY_NAME"] = agency_map.get(fields["PACKAGE_NAME"], "")
    fields["AGENCY_CODE"] = mapping.get("AGENCY_CODE_MAP", {}).get(
        fields["PACKAGE_NAME"], ""
    )
    std_name, std_code = match_client(
        fields.get("RO_CLIENT_CODE", ""),
        fields.get("RO_CLIENT_NAME", "")
    )
    fields["CLIENT_NAME"] = std_name
    fields["CLIENT_CODE"] = std_code
    fields["COLOUR"] = extract_colour(clean_text)
    fields["AD_CAT"] = "GO2"
    fields["AD_SUBCAT"] = "0"
    fields["PRODUCT"] = "DISPLAY - MISCELLANEOUS"
    fields["BRAND"] = "N/A"
    try:
        if fields["AD_HEIGHT"] and fields["AD_WIDTH"]:
            h = float(fields["AD_HEIGHT"])
            w = float(fields["AD_WIDTH"])
            area = h * w
            fields["AD_SIZE"] = str(int(round(area)))
        else:
            fields["AD_SIZE"] = ""
    except:
        fields["AD_SIZE"] = ""
    key_match = re.search(
        r"\b([0-9]{5,}/[0-9]{2}/[0-9]{4}/[0-9]{4})\b",
        clean_text
    )    
    fields["KEY_NUMBER"] = key_match.group(1).strip() if key_match else fields.get("RO_NUMBER", "")   
    fields["EXTRACTED_TEXT"] = clean_text.replace("\n", " ").strip()
    for k, v in list(fields.items()):
        if isinstance(v, str):
            fields[k] = v.strip()
    return fields

def extract_pdf_layout(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        words = page.extract_words()
        page_width = page.width
        x_threshold = page_width * 0.25
        filtered_words = [
            w for w in words if w["x0"] > x_threshold
        ]
        filtered_words = sorted(filtered_words, key=lambda x: (x["top"], x["x0"]))
        structured_text = rebuild_layout_text(filtered_words)
        clean_text = remove_noise(structured_text)
        fields = extract_fields(clean_text)
        return structured_text, clean_text, fields
    return text.strip(" ,")

