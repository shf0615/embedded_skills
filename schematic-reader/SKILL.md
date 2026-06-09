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
4. **上下文理解** — 通过语义理解确认连接关系，而非仅靠坐标数值
5. **一次读完** — 原理图通常不超过20页，直接一次提取全文比反复搜索更快更准

---

## 执行流程

### 所有问题的统一入口：一次性提取全文

原理图PDF通常只有几页到十几页。**不论什么问题，第一步都是提取全部页面文字：**

```python
import fitz
doc = fitz.open(pdf_path)
all_text = {}
for i in range(doc.page_count):
    all_text[i+1] = doc[i].get_text()
    print(f'=== Page {i+1} ===')
    print(all_text[i+1])
doc.close()
```

**然后根据问题类型决定是否需要进一步分析：**

### 概述类问题 → 直接从全文总结

通读全文即可回答，无需额外操作。

### 精确查询（引脚、电路方案等） → 从全文中定位 + 坐标辅助

从已有全文中找到相关内容后，如需确认引脚对应关系，**再对目标页面做坐标分析**：

```python
# 仅对需要确认引脚对应的页面做坐标提取
page = doc[hit_page_index]
blocks = page.get_text('dict')['blocks']
texts = []
for block in blocks:
    if 'lines' in block:
        for line in block['lines']:
            for span in line['spans']:
                t = span['text'].strip()
                if t:
                    texts.append((span['bbox'][0], span['bbox'][1], t))

# 打印目标信号同行所有文字，由AI语义判断对应关系
target_y = ...
for x, y, t in sorted(texts, key=lambda i: i[0]):
    if abs(y - target_y) < 8:
        print(f'  [{x:.0f},{y:.0f}] {t}')
```

### 包含表格数据的问题（如天线切换真值表） → pdfplumber提取表格

当全文中看到表格相关内容但格式混乱时，用pdfplumber提取结构化表格：

```python
import pdfplumber
with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[hit_page_index]
    tables = page.extract_tables()
    for table in tables:
        for row in table:
            print(row)
```

### 视觉验证 → 仅当有歧义或纯位图时

```python
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
2. **不盲信坐标** — 坐标匹配只是辅助，最终靠语义理解
3. **一次读完全文** — 原理图几页到十几页，一次读完比反复搜索更快
4. **表格用pdfplumber** — 真值表/配置表等结构化数据用pdfplumber提取更准确
5. **有歧义时说明** — 列出所有候选并说明不确定性
