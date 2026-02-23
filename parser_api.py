import re
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

USE_GPT = False  # Set False if you want regex-only mode

client = None
if USE_GPT:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        client = OpenAI(api_key=api_key)


# ==========================================
# MAIN PARSER
# ==========================================

def parse_fields(full_text, pdf_path=None, mapping=None):
    text = clean_text(full_text)

    data = {}

    # ==========================
    # REGEX EXTRACTION
    # ==========================

    data["RO_NUMBER"] = search(r'RO Code.*?:\s*([0-9\/]+)', text)
    data["RO_DATE"] = search(r'RO Date.*?:\s*([0-9\-]+)', text)
    data["INSERT_DATE"] = search(r'Date of Publication.*?\n\s*([0-9\-]+)', text)
    data["RO_AMOUNT"] = search(r'RO Amount.*?:\s*([0-9]+)', text)
    data["RATE_PER_SQ_CM"] = search(r'Rate per Sq.*?:\s*([0-9.]+)', text)

    size = re.search(r'Height\s*=\s*([\d.]+).*?Width\s*=\s*([\d.]+).*?Size\s*=\s*([\d.]+)', text)
    if size:
        data["HEIGHT"] = size.group(1)
        data["WIDTH"] = size.group(2)
        data["AREA_SQ_CM"] = size.group(3)

    data["COLOUR"] = search(r'B2\s*-\s*([A-Za-z\s&]+)', text)
    data["PAGE_PREMIUM"] = search(r'Premium.*?:\s*(Yes|No)', text)

    # SUBJECT (multiline safe)
    subject_match = re.search(r'Subject.*?:\s*(.*?)Campaign Name', text, re.DOTALL)
    if subject_match:
        subject = subject_match.group(1)
        data["SUBJECT"] = normalize(subject)

    # CLIENT BLOCK
    client_block = re.search(r'Client Detail.*?:\s*(.*?)The Advertisement Manager', text, re.DOTALL)
    if client_block:
        block = client_block.group(1)
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        if lines:
            data["CONTACT_PERSON"] = lines[0]
        if len(lines) > 1:
            data["CLIENT_NAME"] = lines[1]

    # ==========================
    # GPT FALLBACK IF NEEDED
    # ==========================

    if USE_GPT and client:
        if not data.get("CLIENT_NAME") or not data.get("SUBJECT"):
            gpt_data = gpt_extract(text)

            for field in ["CLIENT_NAME", "SUBJECT"]:
                if not data.get(field) and gpt_data.get(field):
                    data[field] = gpt_data[field]

    return data


# ==========================================
# GPT EXTRACTION
# ==========================================

def gpt_extract(text):
    try:
        prompt = f"""
        Extract the following fields from this CBC Release Order.
        Return STRICT JSON only.

        Fields:
        - CLIENT_NAME
        - SUBJECT

        Text:
        {text}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        print("GPT ERROR:", e)
        return {}


# ==========================================
# HELPERS
# ==========================================

def search(pattern, text):
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def clean_text(text):
    text = text.replace("\r", "\n")
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()
