from paddleocr import PaddleOCR

# 初始化 OCR
ocr = PaddleOCR(
    lang="ch",
    use_doc_orientation_classify=True,
    use_doc_unwarping=True,
    use_textline_orientation=True
)

# 图片路径
image_path = "1.png"

# OCR
result = ocr.predict(image_path)

# 输出识别结果
for res in result:
    data = res.json

    # 提取文字
    if "res" in data:
        rec_texts = data["res"].get("rec_texts", [])
        rec_scores = data["res"].get("rec_scores", [])

        for text, score in zip(rec_texts, rec_scores):
            print(f"{score:.2f}  {text}")