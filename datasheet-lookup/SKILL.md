---
name: datasheet-lookup
description: 从芯片手册PDF中查找硬件参数信息，基于事实回答，不捏造。
---

# 芯片手册查阅技能

用户指定一份芯片手册PDF，提出问题，AI按需查找并给出**基于事实的回答**。

## 核心原则

1. **不捏造** — 找不到就说"未找到"
2. **引用出处** — 标注页码、表格编号
3. **准确性优先** — 宁可多读几页确认，不要跳过重要上下文

---

## 执行流程

根据问题类型选择不同路径：

### 概述类问题（"这是什么芯片"、"主要特性"）

直接读取前20-30页（Introduction/Overview章节），通读后总结：

```python
import fitz
doc = fitz.open(pdf_path)
for i in range(min(30, doc.page_count)):
    text = doc[i].get_text()
    print(f'=== Page {i+1} ===')
    print(text)
doc.close()
```

不需要索引，不需要关键词搜索，直接读前面的章节最快最准。

### 精确查询（"LPUART如何初始化"、"PTA0复用功能"）

**Step 1: 获取目录定位章节**

```python
import fitz
doc = fitz.open(pdf_path)

# 方法A: 用PyMuPDF的TOC功能
toc = doc.get_toc()
for level, title, page in toc:
    if any(k in title.upper() for k in keywords):
        print(f'  [{page}] {title}')

# 方法B: 如果TOC为空，读前5页文字找目录
if not toc:
    for i in range(5):
        print(doc[i].get_text())
doc.close()
```

**Step 2: 关键词搜索定位具体页码**

在目标章节范围内搜索：

```python
doc = fitz.open(pdf_path)
keywords = ['LPUART', 'initialization']

for i in range(start_page, end_page):
    text = doc[i].get_text()
    if any(k.upper() in text.upper() for k in keywords):
        print(f'Page {i+1}: hit')
doc.close()
```

**Step 3: 精确读取目标页面**

读取命中页面的**完整文字**，通读理解后提取答案：

```python
doc = fitz.open(pdf_path)
for page_num in hit_pages:
    text = doc[page_num - 1].get_text()
    print(f'=== Page {page_num} ===')
    print(text)
doc.close()
```

**注意：** 如果内容跨页（如表格、配置步骤），顺序读取相邻页面直到内容完整。

**Step 4: 视觉补充（仅表格/框图结构丢失时）**

当文字提取丢失了表格结构（如引脚复用表的列对齐），渲染为图片辅助理解：

```python
doc = fitz.open(pdf_path)
page = doc[page_num - 1]
mat = fitz.Matrix(3, 3)
pix = page.get_pixmap(matrix=mat)
pix.save('table_view.png')
doc.close()
```

---

## 回答格式

```
### 答案
[简明回答]

### 证据
- **Page X, Table Y**: [原文]
- **Page Z, Section W**: [原文]

### 补充说明（如适用）
[配置建议、注意事项等，必须基于手册内容]
```

---

## 注意事项

1. **不捏造** — 找不到就说找不到
2. **标注手册版本** — 开头说明使用的手册版本
3. **表格跨页** — 注意翻页读完整
4. **概述类直接读前30页** — 不需要先建索引
5. **精确查询先用TOC定位** — PyMuPDF的`get_toc()`比全文搜索快得多
