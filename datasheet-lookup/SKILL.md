---
name: datasheet-lookup
description: 从芯片手册PDF中查找硬件参数信息，基于事实回答，不捏造。
---

# 芯片手册查阅技能

用户指定一份芯片手册/数据手册PDF，提出问题，AI按需查找并给出**基于事实的回答**。

## 核心原则

1. **不捏造** — 手册中找不到就说"未找到"，不根据经验补充
2. **引用出处** — 回答标注页码和原文（"Table 9, Page 63"）
3. **按需查找** — 几百页手册不要一次读完，先目录定位再精确翻页

---

## 分析方法

### 方法1: 目录定位（首选，大型PDF必用）

先读前3-5页目录，确定目标章节页码：

```python
import fitz
doc = fitz.open('reference_manual.pdf')

for i in range(min(5, doc.page_count)):
    page = doc[i]
    text = page.get_text()
    print(f'=== Page {i+1} ===')
    print(text)
```

常见章节关键词：
- Pin definitions / Pinout / Alternate function mapping（引脚复用）
- Memory map（内存映射/外设基地址）
- 各外设章节（USART, I2C, SPI, TIM, ADC...）
- Clock tree（时钟树）
- Electrical characteristics（电气特性）

### 方法2: 关键词搜索（快速定位）

对整份PDF做关键词搜索，找到相关页面后再精确读取：

```python
keywords = [...]  # 从用户问题提取

for i in range(doc.page_count):
    page = doc[i]
    text = page.get_text()
    for kw in keywords:
        if kw.upper() in text.upper():
            print(f'Page {i+1}: found "{kw}"')
            break
```

### 方法3: 精确页面读取

定位到目标页后，提取完整文字内容：

```python
page = doc[target_page_index]
text = page.get_text()
print(text)
```

如果是表格（引脚复用表、寄存器定义表），可能需要连续读取多页。

### 方法4: 视觉识别（表格/框图）

当页面包含复杂表格或框图（如时钟树图）时，文字提取可能丢失结构信息，需渲染为图片后视觉识别：

```python
page = doc[target_page_index]
mat = fitz.Matrix(3, 3)  # 3x渲染即可看清
pix = page.get_pixmap(matrix=mat)
pix.save('page_view.png')
# 然后用 Read 工具查看图片
```

---

## 回答格式

```
### 答案

[简明回答用户问题]

### 证据

- **Page X, Table Y**: [原文内容]
- **Page Z, Section W**: [原文内容]

### 补充说明（如适用）

[配置建议、注意事项等，必须基于手册内容]
```

---

## 常见芯片手册结构

| 芯片系列 | 引脚复用在哪 | 外设配置在哪 | 复用配置方式 |
|---------|------------|------------|------------|
| STM32 | Datasheet | Reference Manual | GPIO AF寄存器 |
| NXP KW45/K | Reference Manual | Reference Manual | PORT PCR寄存器MUX字段 |
| ESP32 | TRM | TRM | IO_MUX寄存器 |
| 博流BL602/BL616 | Reference Manual | Reference Manual | GLB寄存器 |
| 全志D1 | User Manual | User Manual | PIO控制器寄存器 |

---

## 注意事项

1. **不捏造** — 找不到就说找不到
2. **引用来源** — 标注页码、表格编号、章节号
3. **版本敏感** — 注意手册版本号，开头回答中说明使用的手册版本
4. **按需读取** — 不要一次性读完几百页，只读与问题相关的页面
5. **表格跨页** — 引脚复用表等大表格常跨多页，注意翻页读取完整
