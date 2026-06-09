---
name: schematic-reader
description: 从原理图PDF中提取MCU引脚映射、外设接口连接、电源域等硬件信息，输出结构化JSON。优先使用矢量文字坐标分析，穷举所有引脚不遗漏。
---

# 原理图识别技能

从原理图PDF中提取硬件连接信息（MCU引脚映射、外设接口、电源域等）。

## 触发条件

当用户请求涉及以下场景时激活：
- 识别原理图PDF中的MCU型号
- 提取引脚与网络名的对应关系
- 分析UART/SPI/I2C/CAN等接口的引脚分配
- 分析电源域划分
- 从原理图生成引脚配置代码

## 核心原理

EDA工具（Altium/KiCad/立创EDA等）导出的原理图PDF通常包含**矢量文字**，每个文字元素都有精确的坐标位置。通过提取文字+坐标，利用空间关系（同一行=同一连接）可以还原出引脚与网络名的对应关系。

**优先使用文字提取+坐标分析，比视觉识别更精确、更快速。**

---

## 分析流程

### Step 1: 判断PDF类型

```python
import fitz
doc = fitz.open('schematic.pdf')
for i in range(doc.page_count):
    page = doc[i]
    images = page.get_images()
    text = page.get_text()
    drawings = page.get_drawings()
    print(f'Page {i+1}: images={len(images)}, text_len={len(text)}, drawings={len(drawings)}')
```

判断规则：
- `drawings > 100` 且 `images == 0` → **纯矢量原理图**（最佳，直接提取文字）
- `images > 0` 且 `text_len < 100` → **纯位图**（需视觉识别，效果受限）
- `images > 0` 且 `text_len > 100` → **混合型**（位图+标题栏矢量文字）

### Step 2: 提取全部文字（快速总览）

```python
all_text = {}
for i in range(doc.page_count):
    page = doc[i]
    all_text[i+1] = page.get_text()
```

用途：
- 确认MCU型号（搜索芯片型号关键词）
- 列出所有信号网络名
- 识别关键标注（电源域、时钟频率、设计说明等）

### Step 3: 提取所有页面的带坐标文字

```python
all_texts_with_pos = {}
for i in range(doc.page_count):
    page = doc[i]
    blocks = page.get_text('dict')['blocks']
    page_texts = []
    for block in blocks:
        if 'lines' in block:
            for line in block['lines']:
                for span in line['spans']:
                    text = span['text'].strip()
                    if text:
                        bbox = span['bbox']
                        page_texts.append((bbox[0], bbox[1], bbox[2], bbox[3], text))
    all_texts_with_pos[i+1] = page_texts
```

### Step 4: 识别所有MCU引脚描述（穷举，不遗漏）

MCU引脚描述的特征：包含 `/` 分隔的多个复用功能名（如 `PTC3/LPSPI1_SCK/LPUART1_TX/...`）。

```python
import re

# 匹配MCU引脚描述的模式：
# - NXP: PTx{digit}/... 
# - STM32: PA{digit}/...
# - 通用: GPIO{digit}/...
pin_pattern = re.compile(r'^(PT[A-Z]\d+|P[A-Z]\d+|GPIO\d+)/')

mcu_pins = []  # 存储所有MCU引脚: (page, x, y, pin_name, full_description)

for page_num, texts in all_texts_with_pos.items():
    for x, y, x2, y2, text in texts:
        if pin_pattern.match(text):
            pin_name = text.split('/')[0]
            mcu_pins.append((page_num, x, y, pin_name, text))
```

### Step 5: 对每个MCU引脚，查找同行的网络名（关键步骤）

**这一步必须穷举所有引脚，确保无遗漏。**

```python
pin_net_mapping = []  # 最终结果

for page_num, pin_x, pin_y, pin_name, pin_desc in mcu_pins:
    texts = all_texts_with_pos[page_num]
    tolerance = 5  # Y坐标容差
    
    # 找同一行（Y坐标相近）且在引脚描述右侧（X坐标更大）的网络名
    candidates = []
    for x, y, x2, y2, text in texts:
        if abs(y - pin_y) < tolerance and text != pin_desc:
            if not pin_pattern.match(text) and not text.replace('.','').isdigit():
                candidates.append((x, y, text))
    
    # 还要找引脚描述左侧的引脚编号（纯数字）
    pin_number = None
    for x, y, x2, y2, text in texts:
        if abs(y - pin_y) < tolerance and text.isdigit():
            pin_number = int(text)
    
    # 取同行中最可能是网络名的文字
    net_name = None
    if candidates:
        # 网络名通常是同行中最远离引脚描述的非数字文字
        candidates.sort(key=lambda c: abs(c[0] - pin_x), reverse=True)
        net_name = candidates[0][2]
    
    pin_net_mapping.append({
        "page": page_num,
        "pin_name": pin_name,
        "pin_number": pin_number,
        "net_name": net_name,
        "full_description": pin_desc
    })
```

### Step 6: 分类整理为结构化JSON

根据引脚描述中的复用功能关键词，将引脚自动分类：

```python
def classify_pin(pin_desc, net_name):
    """根据引脚描述和网络名判断接口类型"""
    desc_upper = pin_desc.upper()
    net_upper = (net_name or '').upper()
    
    if 'LPUART' in desc_upper or 'USART' in desc_upper or 'UART' in desc_upper:
        if 'TX' in desc_upper or 'TXD' in net_upper:
            return 'uart_tx'
        if 'RX' in desc_upper or 'RXD' in net_upper:
            return 'uart_rx'
    if 'SPI' in desc_upper or 'LPSPI' in desc_upper:
        return 'spi'
    if 'I2C' in desc_upper or 'LPI2C' in desc_upper or 'I3C' in desc_upper:
        return 'i2c'
    if 'CAN' in desc_upper:
        return 'can'
    if 'ADC' in desc_upper:
        return 'adc'
    if 'TPM' in desc_upper or 'PWM' in net_upper:
        return 'pwm'
    if 'SWD' in desc_upper or 'JTAG' in desc_upper:
        return 'debug'
    return 'gpio'
```

### Step 7: 位图页面的备用方案

当PDF页面为纯位图时（如第1页框图），使用视觉识别：

```python
# 提取嵌入的原始位图
for img in page.get_images():
    xref = img[0]
    base_image = doc.extract_image(xref)

# 或者高倍率渲染矢量页面的局部区域
mat = fitz.Matrix(10, 10)
clip = fitz.Rect(x0, y0, x1, y1)
pix = page.get_pixmap(matrix=mat, clip=clip)
pix.save('region.png')
```

---

## 输出格式（强制要求）

**必须**以JSON格式输出分析结果。不要输出自然语言描述，不要输出表格，只输出JSON。

将分析结果写入与原理图PDF同目录下的 `schematic_analysis.json` 文件。

### 完整JSON结构

```json
{
  "schematic_file": "DK033-A1-BS_V1.3_SCH.pdf",
  "mcu": {
    "part_number": "KW45B41Z83",
    "package": "QFN48",
    "vendor": "NXP",
    "page": 4
  },
  "pages": [
    {"page": 1, "title": "BLOCK", "type": "block_diagram"},
    {"page": 2, "title": "MCU", "type": "mcu_pinout"}
  ],
  "pin_map": [
    {
      "pin_name": "PTC3",
      "pin_number": 42,
      "net_name": "BLE_DEBUG_TXD",
      "function": "LPUART1_TX",
      "category": "uart_tx",
      "page": 4
    },
    {
      "pin_name": "PTC2",
      "pin_number": 40,
      "net_name": "BLE_DEBUG_RXD",
      "function": "LPUART1_RX",
      "category": "uart_rx",
      "page": 4
    }
  ],
  "interfaces": {
    "uart": [
      {
        "instance": "LPUART1",
        "tx": {"pin": "PTC3", "number": 42, "net": "BLE_DEBUG_TXD"},
        "rx": {"pin": "PTC2", "number": 40, "net": "BLE_DEBUG_RXD"},
        "usage": "DEBUG UART",
        "page": 4
      }
    ],
    "spi": [],
    "i2c": [],
    "can": [],
    "adc": [],
    "pwm": [],
    "debug": []
  },
  "power_domains": [],
  "clock": {},
  "notes": [],
  "unresolved_pins": []
}
```

### 强制规则

1. **穷举所有MCU引脚** — `pin_map` 数组必须包含原理图中出现的**每一个**MCU引脚，不允许遗漏
2. **无法确认的用 `null`** — 如果某个引脚无法确定网络名，`net_name` 填 `null`，同时在 `unresolved_pins` 中记录
3. **每条必须标注页码** — 所有条目都有 `page` 字段
4. **自动分类** — 根据引脚描述中的复用功能自动判断 `category`
5. **接口聚合** — `interfaces` 中将相关引脚按外设实例聚合（如 LPUART1 的 TX/RX 放在一起）
6. **写入文件** — 分析完成后将JSON写入 `schematic_analysis.json`，告知用户路径

---

## 注意事项

1. **坐标容差**：不同EDA工具导出的PDF，文字间距略有不同。通常同一连接线上的文字Y坐标差在 ±5pt 以内
2. **引脚描述格式**：
   - NXP: `PTx/功能1/功能2/...`
   - STM32: `PAx`
   - 博流: `GPIOx`
3. **网络名前缀**：`#A#` 表示电源网络，`#H#` 可能表示高压网络
4. **多页关联**：MCU引脚定义可能跨多页，必须扫描所有矢量页面
5. **优先文字提取**：仅在位图页面才使用视觉识别
6. **不猜测**：如果文字提取无法确认某个连接，填 `null` 并记入 `unresolved_pins`，不要编造
7. **穷举优先**：先穷举所有MCU引脚，再分类，不要只搜索特定关键词
