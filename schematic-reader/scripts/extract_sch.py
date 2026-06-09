#!/usr/bin/env python3
"""
原理图PDF文字提取与缓存工具

用法: python3 extract_sch.py <pdf_path>
输出: <pdf_name>.sch.json（与PDF同目录）

功能:
1. 判断每页类型（矢量/位图/混合）
2. 提取所有矢量文字及坐标
3. 自动识别MCU引脚描述（含/的多功能文字）
4. 结果缓存为JSON，后续提问直接加载
"""

import fitz
import json
import sys
import os
import re


def analyze_page_type(page):
    """判断页面类型"""
    images = page.get_images()
    drawings = len(page.get_drawings())
    text_len = len(page.get_text())

    if drawings > 100 and len(images) == 0:
        return "vector"
    elif len(images) > 0 and text_len < 100:
        return "bitmap"
    else:
        return "mixed"


def extract_texts_with_position(page):
    """提取页面所有文字及坐标"""
    texts = []
    blocks = page.get_text('dict')['blocks']
    for block in blocks:
        if 'lines' in block:
            for line in block['lines']:
                for span in line['spans']:
                    text = span['text'].strip()
                    if text:
                        bbox = span['bbox']
                        texts.append({
                            "x": round(bbox[0], 1),
                            "y": round(bbox[1], 1),
                            "x2": round(bbox[2], 1),
                            "y2": round(bbox[3], 1),
                            "text": text
                        })
    return texts


def detect_mcu_pins(texts):
    """自动识别MCU引脚描述文字（含/分隔的多功能描述）"""
    # 通用模式: 以字母+数字开头，后面有/分隔的多个功能
    pin_pattern = re.compile(
        r'^(PT[A-Z]\d+|P[A-Z]\d+|GPIO\d+|IO\d+|P\d+_\d+)'  # 引脚名
        r'/'  # 至少一个/
    )
    pins = []
    for t in texts:
        if pin_pattern.match(t["text"]):
            pin_name = t["text"].split('/')[0]
            pins.append({
                "pin_name": pin_name,
                "full_desc": t["text"],
                "x": t["x"],
                "y": t["y"]
            })
    return pins


def extract_schematic(pdf_path):
    """主提取函数"""
    doc = fitz.open(pdf_path)

    result = {
        "file": os.path.basename(pdf_path),
        "page_count": doc.page_count,
        "pages": []
    }

    for i in range(doc.page_count):
        page = doc[i]
        page_type = analyze_page_type(page)
        texts = extract_texts_with_position(page) if page_type != "bitmap" else []
        pins = detect_mcu_pins(texts) if texts else []

        page_data = {
            "page": i + 1,
            "type": page_type,
            "text_count": len(texts),
            "pin_count": len(pins),
            "texts": texts,
            "pins": pins
        }

        # 位图页面记录图片信息
        if page_type in ("bitmap", "mixed"):
            images = page.get_images()
            page_data["images"] = []
            for img in images:
                xref = img[0]
                base = doc.extract_image(xref)
                page_data["images"].append({
                    "width": base["width"],
                    "height": base["height"],
                    "format": base["ext"]
                })

        result["pages"].append(page_data)

    doc.close()
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 extract_sch.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}")
        sys.exit(1)

    result = extract_schematic(pdf_path)

    # 输出到同目录下的 .sch.json
    base = os.path.splitext(pdf_path)[0]
    out_path = base + ".sch.json"

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print(f"已生成: {out_path}")
    print(f"总页数: {result['page_count']}")
    for p in result['pages']:
        print(f"  Page {p['page']}: {p['type']}, {p['text_count']} texts, {p['pin_count']} pins")
