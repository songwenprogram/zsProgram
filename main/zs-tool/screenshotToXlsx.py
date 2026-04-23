"""
速卖通店铺截图商品价格提取工具
功能：输入店铺产品界面截图，提取商品名称和美元价格，输出xlsx文件
"""

import os
import re
import cv2
import numpy as np
import pandas as pd
from PIL import Image
from paddleocr import PaddleOCR


class AliExpressScreenshotParser:
    """速卖通截图解析器"""

    def __init__(self):
        # 初始化PaddleOCR（中英文混合识别）
        self.ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        图像预处理：灰度化 + 自适应阈值二值化，提升OCR准确率
        [reference:1][reference:2]
        """
        # 读取图像
        if isinstance(image_path, str):
            img = cv2.imread(image_path)
        else:
            img = image_path

        if img is None:
            raise ValueError(f"无法读取图片: {image_path}")

        # 1. 灰度化：减少数据量，提升处理速度
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. 自适应阈值二值化：处理光照不均问题[reference:3]
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,  # 邻域大小，越大越能忽略细小纹理
            C=10           # 常数，使图像保留更多前景文字
        )

        return binary

    def extract_text_from_image(self, image_path: str) -> list:
        """使用OCR提取图片中的文字"""
        # 预处理图像
        processed_img = self.preprocess_image(image_path)

        # OCR识别
        result = self.ocr.ocr(processed_img, cls=True)

        # 提取所有识别到的文字
        texts = []
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]  # 识别的文字
                confidence = line[1][1]  # 置信度
                # 只保留置信度较高的结果（>0.6）
                if confidence > 0.6:
                    texts.append(text.strip())

        return texts

    def extract_prices(self, texts: list) -> list:
        """
        从OCR识别结果中提取美元价格
        支持格式：$19.99、$1,234.56、US $45.99、$12 等
        [reference:4][reference:5]
        """
        # 美元价格正则：$后跟数字（可能含千分位逗号），可选小数点和小数部分
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
                # 提取数值部分并标准化
                price_str = match.group(1).replace(',', '')
                try:
                    price_float = float(price_str)
                    # 保留两位小数格式
                    prices.append(f"${price_float:.2f}")
                except ValueError:
                    continue

        return prices

    def extract_product_names(self, texts: list, prices: list) -> list:
        """
        提取商品名称
        策略：排除价格文本，保留较长的文本（通常是商品名称）
        """
        # 构建价格文本集合，用于过滤
        price_texts = set()
        for text in texts:
            if re.search(r'\$\s*\d', text, re.IGNORECASE):
                price_texts.add(text)

        # 过滤出非价格的文本作为商品名称候选
        name_candidates = [t for t in texts if t not in price_texts and len(t) > 3]

        # 配对数量与价格一致（如果截图中有多个商品）
        # 由于截图可能包含多个商品，取与价格数量一致的前N个名称
        if len(name_candidates) >= len(prices):
            product_names = name_candidates[:len(prices)]
        else:
            # 如果名称不足，用价格对应的行数补充
            product_names = name_candidates + [""] * (len(prices) - len(name_candidates))

        return product_names

    def parse_screenshot(self, image_path: str) -> dict:
        """解析单张截图，返回商品名称和价格列表"""
        print(f"正在处理: {image_path}")

        # 1. OCR提取文字
        texts = self.extract_text_from_image(image_path)
        print(f"  识别到 {len(texts)} 条文本")

        # 2. 提取价格
        prices = self.extract_prices(texts)
        print(f"  提取到 {len(prices)} 个价格")

        # 3. 提取商品名称
        product_names = self.extract_product_names(texts, prices)

        return {
            "file": os.path.basename(image_path),
            "product_names": product_names,
            "prices": prices
        }

    def export_to_excel(self, results: list, output_path: str = "products.xlsx"):
        """
        将结果导出为xlsx文件
        使用pandas配合openpyxl引擎[reference:6]
        """
        all_names = []
        all_prices = []
        all_sources = []

        for result in results:
            names = result["product_names"]
            prices = result["prices"]
            source = result["file"]

            # 确保名称和价格一一对应
            min_len = min(len(names), len(prices))
            for i in range(min_len):
                all_names.append(names[i])
                all_prices.append(prices[i])
                all_sources.append(source)

        # 创建DataFrame
        df = pd.DataFrame({
            "商品名称": all_names,
            "价格(USD)": all_prices,
            "来源截图": all_sources
        })

        # 导出为xlsx
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"\n✅ 已导出 {len(df)} 条商品记录到: {output_path}")
        return df


def process_single_screenshot(image_path: str, output_path: str = "products.xlsx"):
    """处理单张截图的主函数"""
    parser = AliExpressScreenshotParser()
    result = parser.parse_screenshot(image_path)
    df = parser.export_to_excel([result], output_path)

    # 打印预览
    print("\n--- 提取结果预览 ---")
    for name, price in zip(result["product_names"], result["prices"]):
        print(f"  {name}: {price}")

    return df


def process_multiple_screenshots(image_folder: str, output_path: str = "products.xlsx"):
    """处理文件夹内多张截图"""
    parser = AliExpressScreenshotParser()

    # 支持的图片格式
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


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 方式一：处理单张截图
    # process_single_screenshot("screenshot.png", "aliexpress_products.xlsx")

    # 方式二：处理文件夹内所有截图
    # process_multiple_screenshots("./screenshots", "aliexpress_products.xlsx")

    # 交互式输入
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