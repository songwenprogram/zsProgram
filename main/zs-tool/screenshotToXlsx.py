"""
速卖通店铺截图商品价格提取工具 (稳定版)
适配 PaddleOCR 2.7.0.3
"""

import os
import re
import cv2
import numpy as np
import pandas as pd
from paddleocr import PaddleOCR


class AliExpressScreenshotParser:
    def __init__(self):
        # PaddleOCR 2.7.x 参数
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en')

    def preprocess_image(self, image_path: str) -> np.ndarray:
        if isinstance(image_path, str):
            img = cv2.imread(image_path)
        else:
            img = image_path
        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15, C=10
        )
        return binary

    def extract_text_from_image(self, image_path: str) -> list:
        processed_img = self.preprocess_image(image_path)
        result = self.ocr.ocr(processed_img, cls=True)
        texts = []
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                confidence = line[1][1]
                if confidence > 0.6:
                    texts.append(text.strip())
        return texts

    def extract_prices(self, texts: list) -> list:
        price_pattern = re.compile(
            r'(?:US\s*)?\$'
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?'
            r'|\.\d{1,2})',
            re.IGNORECASE
        )
        prices = []
        for text in texts:
            match = price_pattern.search(text)
            if match:
                price_str = match.group(1).replace(',', '')
                try:
                    price_float = float(price_str)
                    prices.append(f"${price_float:.2f}")
                except ValueError:
                    continue
        return prices

    def extract_product_names(self, texts: list, prices: list) -> list:
        price_texts = set()
        for text in texts:
            if re.search(r'\$\s*\d', text, re.IGNORECASE):
                price_texts.add(text)
        name_candidates = [t for t in texts if t not in price_texts and len(t) > 3]
        if len(name_candidates) >= len(prices):
            product_names = name_candidates[:len(prices)]
        else:
            product_names = name_candidates + [""] * (len(prices) - len(name_candidates))
        return product_names

    def parse_screenshot(self, image_path: str) -> dict:
        print(f"正在处理: {image_path}")
        texts = self.extract_text_from_image(image_path)
        print(f"  识别到 {len(texts)} 条文本")
        prices = self.extract_prices(texts)
        print(f"  提取到 {len(prices)} 个价格")
        product_names = self.extract_product_names(texts, prices)
        return {
            "file": os.path.basename(image_path),
            "product_names": product_names,
            "prices": prices
        }

    def export_to_excel(self, results: list, output_path: str = "products.xlsx"):
        all_names, all_prices, all_sources = [], [], []
        for result in results:
            names = result["product_names"]
            prices = result["prices"]
            source = result["file"]
            min_len = min(len(names), len(prices))
            for i in range(min_len):
                all_names.append(names[i])
                all_prices.append(prices[i])
                all_sources.append(source)
        df = pd.DataFrame({
            "商品名称": all_names,
            "价格(USD)": all_prices,
            "来源截图": all_sources
        })
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"\n✅ 已导出 {len(df)} 条商品记录到: {output_path}")
        return df


def process_single_screenshot(image_path: str, output_path: str = "products.xlsx"):
    parser = AliExpressScreenshotParser()
    result = parser.parse_screenshot(image_path)
    df = parser.export_to_excel([result], output_path)
    print("\n--- 提取结果预览 ---")
    for name, price in zip(result["product_names"], result["prices"]):
        print(f"  {name}: {price}")
    return df


def process_multiple_screenshots(image_folder: str, output_path: str = "products.xlsx"):
    parser = AliExpressScreenshotParser()
    supported_formats = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp')
    results = []
    for filename in os.listdir(image_folder):
        if filename.lower().endswith(supported_formats):
            image_path = os.path.join(image_folder, filename)
            try:
                result = parser.parse_screenshot(image_path)
                results.append(result)
            except Exception as e:
                print(f"❌ 处理 {filename} 时出错: {e}")
    if results:
        df = parser.export_to_excel(results, output_path)
        return df
    else:
        print("⚠️ 未找到任何可处理的图片")
        return None


if __name__ == "__main__":
    print("=" * 50)
    print("速卖通店铺截图商品价格提取工具")
    print("=" * 50)
    mode = input("请选择模式:\n1 - 处理单张截图\n2 - 处理文件夹内所有截图\n输入 (1/2): ").strip()
    if mode == "1":
        img_path = input("请输入截图路径: ").strip()
        out_path = input("请输入输出文件路径 (默认: products.xlsx): ").strip()
        if not out_path:
            out_path = "products.xlsx"
        process_single_screenshot(img_path, out_path)
    elif mode == "2":
        folder_path = input("请输入截图文件夹路径: ").strip()
        out_path = input("请输入输出文件路径 (默认: products.xlsx): ").strip()
        if not out_path:
            out_path = "products.xlsx"
        process_multiple_screenshots(folder_path, out_path)
    else:
        print("无效选择，请重新运行")