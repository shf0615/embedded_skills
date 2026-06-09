---
name: schematic-reader
description: 从原理图PDF中查找硬件设计信息，基于事实回答，不捏造。
---

# 原理图识别技能

用户指定一份原理图PDF，提出问题，AI查找后给出**基于事实的回答**。

## 核心原则

1. **不捏造** — 找不到就说"未找到"，不根据经验脑补
2. **引用出处** — 回答中标注页码和原文
3. **准确性优先于速度** — 宁可多读一页确认，不要因为坐标匹配"看起来对"就下结论
4. **上下文理解** — 读取目标信号周围的完整文字块，通过语义理解确认连接关系，而非仅靠坐标数值

---

## 执行流程

根据问题类型选择不同路径：

### 概述类问题（"这是什么板子"、"有哪些模块"）

直接用 PyMuPDF 提取所有页面的全文，通读后总结：

```python
import fitz
doc = fitz.open(pdf_path)
for i in range(doc.page_count):
    text = doc[i].get_text()
    print(f'=== Page {i+1} ===')
    print(text)
doc.close()
```

不需要缓存，不需要关键词搜索，直接读全文最快最准。

### 精确查询（"UART用什么引脚"、"BAT怎么检测"）

**Step 1: 关键词定位页面**

```python
import fitz
doc = fitz.open(pdf_path)
keywords = ['UART', 'DEBUG', 'TXD', 'RXD']  # 从问题提取
for i in range(doc.page_count):
    text = doc[i].get_text()
    if any(k.upper() in text.upper() for k in keywords):
        print(f'Page {i+1}: hit')
doc.close()
```

**Step 2: 读取命中页面的完整文字**

对命中页面，提取完整文本内容，**通读理解**而非仅搜索关键词：

```python
page = doc[hit_page_index]
text = page.get_text()
print(text)  # 完整阅读该页所有文字
```

**Step 3: 如需确认引脚对应关系，提取带坐标文字做辅助验证**

仅当Step 2的纯文本无法明确确认"哪个引脚连哪个网络"时，才用坐标辅助：

```python
blocks = page.get_text('dict')['blocks']
texts = []
for block in blocks:
    if 'lines' in block:
        for line in block['lines']:
            for span in line['spans']:
                t = span['text'].strip()
                if t:
                    texts.append((span['bbox'][0], span['bbox'][1], t))

# 找目标网络名的位置
target = 'BLE_DEBUG_TXD'
target_y = None
for x, y, t in texts:
    if target in t:
        target_y = y

# 查看同行附近的所有文字（±8pt容差），人工判断哪个是对应引脚
if target_y:
    for x, y, t in sorted(texts, key=lambda i: i[0]):
        if abs(y - target_y) < 8:
            print(f'  [{x:.0f},{y:.0f}] {t}')
```

**关键：打印出同行所有文字后，由AI通过语义理解判断对应关系，而非盲目取第一个含"/"的文字。**

**Step 4: 视觉验证（可选，非必需）**

仅当上述步骤的结论存在歧义（如同行有多个引脚描述），或页面为纯位图时使用：

```python
# 以目标坐标为中心渲染局部区域
clip = fitz.Rect(target_x - 150, target_y - 30, target_x + 400, target_y + 30)
mat = fitz.Matrix(8, 8)
pix = page.get_pixmap(matrix=mat, clip=clip)
pix.save('verify.png')
```

---

## 回答格式

```
### 答案
[简明回答]

### 证据
- **Page X**: [原文文字]

### 补充说明（如适用）
[电路描述、连接关系、设计意图等，必须基于原理图内容]
```

---

## 注意事项

1. **不捏造** — 找不到就说找不到
2. **不盲信坐标** — 坐标匹配只是辅助手段，最终判断靠语义理解上下文
3. **概述类直接读全文** — 不要逐关键词搜索，一次性读完所有页面全文最快
4. **多MCU系统** — 需指明是哪个MCU的引脚
5. **有歧义时说明** — 如果坐标匹配出现多个候选，列出所有候选并说明不确定性
