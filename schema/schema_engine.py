import json
import re
from datetime import datetime

def load_schema(schema_path):
    with open(schema_path, "r") as f:
        return json.load(f)

def extract_fields(layout_blocks, schema):
    extracted = {}

    full_text = " ".join(b["text"] for b in layout_blocks)

    for field, rules in schema.items():
        value = ""
        confidence = 0

        for label in rules.get("labels", []):
            for block in layout_blocks:
                if label.lower() in block["text"].lower():
                    idx = layout_blocks.index(block)
                    if idx + 1 < len(layout_blocks):
                        candidate = layout_blocks[idx + 1]["text"]
                        value = candidate
                        confidence = layout_blocks[idx + 1]["conf"]
                        break

        if "pattern" in rules and value:
            m = re.search(rules["pattern"], value)
            if m:
                value = m.group()

        if rules.get("date") and value:
            try:
                value = datetime.strptime(value, "%d-%m-%Y")
            except:
                value = None

        extracted[field] = {
            "value": value,
            "confidence": confidence
        }

    return extracted
