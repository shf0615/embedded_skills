#!/usr/bin/env python3
"""
芯片手册目录提取与缓存工具

用法: python3 extract_ds_toc.py <pdf_path>
输出: <pdf_name>.ds.json（与PDF同目录）

功能:
1. 提取前10页文字作为目录索引
2. 对全文建立关键词→页码的倒排索引（仅索引，不存全文）
3. 后续查询时加载索引快速定位
"""

import fitz
import json
import sys
import os
import re
from collections import defaultdict


# 建立索引时使用的关键词列表
INDEX_KEYWORDS = [
    # 引脚相关
    "pin", "pinout", "alternate", "function", "mux", "port",
    # 外设
    "uart", "usart", "lpuart", "spi", "lpspi", "i2c", "lpi2c", "i3c",
    "can", "flexcan", "adc", "dac", "timer", "tpm", "pwm",
    "dma", "gpio", "usb", "ethernet", "sdio",
    # 时钟
    "clock", "pll", "oscillator", "xtal",
    # 电气
    "electrical", "characteristic", "absolute", "maximum",
    # 内存
    "memory", "map", "flash", "ram", "register",
    # 复位/启动
    "reset", "boot", "startup",
    # 中断
    "interrupt", "nvic", "vector",
]


def extract_toc(doc, max_pages=10):
    """提取前N页作为目录"""
    toc_texts = []
    for i in range(min(max_pages, doc.page_count)):
        page = doc[i]
        text = page.get_text()
        toc_texts.append({
            "page": i + 1,
            "text": text
        })
    return toc_texts


def build_keyword_index(doc):
    """建立关键词→页码列表的倒排索引"""
    index = defaultdict(list)

    for i in range(doc.page_count):
        page = doc[i]
        text = page.get_text().lower()

        for kw in INDEX_KEYWORDS:
            if kw in text:
                if (i + 1) not in index[kw]:
                    index[kw].append(i + 1)

    return dict(index)


def extract_datasheet(pdf_path):
    """主提取函数"""
    doc = fitz.open(pdf_path)

    result = {
        "file": os.path.basename(pdf_path),
        "page_count": doc.page_count,
        "toc": extract_toc(doc),
        "keyword_index": build_keyword_index(doc)
    }

    doc.close()
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 extract_ds_toc.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"文件不存在: {pdf_path}")
        sys.exit(1)

    result = extract_datasheet(pdf_path)

    # 输出到同目录
    base = os.path.splitext(pdf_path)[0]
    out_path = base + ".ds.json"

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"已生成: {out_path}")
    print(f"总页数: {result['page_count']}")
    print(f"索引关键词数: {len(result['keyword_index'])}")
    for kw, pages in sorted(result['keyword_index'].items()):
        print(f"  {kw}: {pages[:5]}{'...' if len(pages) > 5 else ''}")
