---
name: schematic-reader
description: 从原理图PDF中按需查找硬件设计信息。用户指定原理图文件并提出问题，AI通过提取矢量文字+坐标分析给出准确答案。不生成文件，不捏造事实。
---

# 原理图识别技能

用户指定一份原理图PDF，提出硬件设计相关问题，AI通过分析PDF内容给出**基于事实的回答**。

## 触发条件

用户指定了一份原理图PDF，并提出类似以下的问题：
- "UART使用的是什么引脚？"
- "BAT电压是怎么检测的？"
- "I2C总线上挂了哪些设备？"
- "复位电路是怎么设计的？"
- "电源域有哪些？LDO还是DCDC？"
- "MCU型号是什么？"

## 核心原则

1. **不捏造事实** — 只回答从PDF中能提取到的信息，找不到就说"未找到"
2. **不生成文件** — 直接回答用户问题
3. **引用出处** — 回答中标注信息来源（页码、原文）
4. **按需查找** — 不需要分析整份原理图，只针对问题搜索相关内容

---

## 分析方法

### 方法1: 全文搜索（首选，快速）

针对用户问题中的关键词，在PDF全部文字中搜索：

```python
import fitz

doc = fitz.open(schematic_pdf_path)
results = []

# 从用户问题中提取搜索关键词
keywords = [...]  # 根据问题确定

for i in range(doc.page_count):
    page = doc[i]
    text = page.get_text()
    for keyword in keywords:
        if keyword.upper() in text.upper():
            results.append((i+1, text))
            break
```

### 方法2: 坐标关联分析（精确定位引脚连接）

当需要确认"某信号连接到MCU哪个引脚"时，提取带坐标的文字，利用**同一Y坐标=同一连接线**的原理：

```python
page = doc[page_index]
blocks = page.get_text('dict')['blocks']

texts = []
for block in blocks:
    if 'lines' in block:
        for line in block['lines']:
            for span in line['spans']:
                text = span['text'].strip()
                if text:
                    bbox = span['bbox']
                    texts.append((bbox[0], bbox[1], bbox[2], bbox[3], text))

# 找到目标网络名的Y坐标
target_y = None
for x, y, x2, y2, text in texts:
    if target_keyword in text:
        target_y = y
        break

# 找同行的引脚描述（含/的多功能描述）
if target_y:
    tolerance = 5
    for x, y, x2, y2, text in texts:
        if abs(y - target_y) < tolerance and '/' in text:
            print(f'Pin: {text}')
```

### 方法3: 上下文提取（理解电路设计意图）

当问题涉及"怎么设计的"时，提取目标信号周围的所有文字（标注、注释、元件值）：

```python
# 找到目标信号后，提取其附近±50pt范围内的所有文字
target_x, target_y = ...
context_range = 50

nearby_texts = []
for x, y, x2, y2, text in texts:
    if abs(y - target_y) < context_range and abs(x - target_x) < 200:
        nearby_texts.append(text)
```

---

## 回答格式

回答必须包含：

1. **直接答案** — 简明扼要回答用户问题
2. **证据引用** — 标注信息来源（页码、原文文字）
3. **电路描述**（如适用）— 说明相关元件的连接关系
4. **"未找到"声明**（如适用）— 如果搜索不到相关信息，明确说明

示例回答格式：

```
### 答案

BAT电压通过分压电阻+ADC的方式检测。

### 证据

- **Page 4**: 网络名 `BAT_ADC` 连接到MCU引脚 `PTA16`（具有ADC0_A12功能）
- **Page 4**: 标注文字 "VBAT ADC"、"KOA品牌"（分压电阻品牌要求）
- **Page 4**: 相关网络 `BLE_BAT_DET_EN`（电池检测使能信号）

### 电路描述

VBAT经过分压电阻网络（KOA品牌电阻）分压后，通过 `BAT_ADC` 网络连接到MCU的PTA16引脚（ADC0通道12）。MCU通过 `BLE_BAT_DET_EN` 信号控制检测使能。
```

---

## 注意事项

1. **不捏造** — 只说从PDF中实际提取到的内容，不要根据"一般经验"补充未出现的信息
2. **标注不确定性** — 如果坐标匹配有歧义，标注"[可能]"而非断言
3. **矢量优先** — 先检查页面是否有矢量文字（drawings>100且images==0），有则直接提取文字；纯位图页面才用视觉识别
4. **搜索策略** — 先用简单关键词全文搜索缩小范围，再用坐标分析精确定位
5. **多页关联** — 同一网络名可能出现在多页，需要跨页搜索
