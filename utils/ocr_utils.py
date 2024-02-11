from paddleocr import PaddleOCR

ocr_model = PaddleOCR(use_angle_cls=True, lang="en")


def do_ocr(file_path: str) -> list:
    texts = []

    result = ocr_model.ocr(file_path, cls=True)

    for idx in range(len(result)):
        res = result[idx]
        for line in res:
            texts.append(line[1][0])

    return texts
