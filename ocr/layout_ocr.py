import cv2
import pytesseract
from ultralytics import YOLO
from pdf2image import convert_from_path

MODEL_PATH = "models/doclayout_yolo.pt"
layout_model = YOLO(MODEL_PATH)

def extract_layout_zones(pdf_path):
    pages = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
    page = pages[0]
    img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)

    results = layout_model(img)

    zones = {}
    for r in results:
        for box, cls in zip(r.boxes.xyxy, r.boxes.cls):
            label = layout_model.names[int(cls)]
            zones.setdefault(label, []).append(box.tolist())

    return img, zones


def extract_text_by_zones(img, zones):
    zone_text = {}

    for label, boxes in zones.items():
        texts = []
        for x1, y1, x2, y2 in boxes:
            crop = img[int(y1):int(y2), int(x1):int(x2)]
            txt = pytesseract.image_to_string(crop, lang="eng", config="--psm 6")
            texts.append(txt)
        zone_text[label] = "\n".join(texts)

    return zone_text
