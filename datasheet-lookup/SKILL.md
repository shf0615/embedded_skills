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

### 单章节精确查询（"LPUART如何初始化"、"PTA0复用功能"）

信息集中在一个章节内，用TOC快速定位后连续读取：

**Step 1: TOC定位章节起止页**

```python
import fitz
doc = fitz.open(pdf_path)
toc = doc.get_toc()
for level, title, page in toc:
    if any(k in title.upper() for k in keywords):
        print(f'  [{page}] {title}')
doc.close()
```

**Step 2: 连续读取目标章节**

定位到章节起始页后，**连续读取该章节的所有页面**（不要逐页搜索再逐页读取）：

```python
doc = fitz.open(pdf_path)
# 一次性读取章节范围内的所有页面
for i in range(chapter_start, chapter_end):
    text = doc[i].get_text()
    print(f'=== Page {i+1} ===')
    print(text)
doc.close()
```

**关键：找到章节后直接连续读，不要再做关键词搜索来逐页判断要不要读。**

### 多章节综合查询（"低功耗模式"、"时钟树"等涉及多个章节的问题）

信息分散在多个章节，**按相关章节顺序依次读取**：

**Step 1: TOC定位所有相关章节**

```python
toc = doc.get_toc()
# 一次找到所有相关章节
related_keywords = ['POWER', 'CMC', 'SPC', 'WUU', 'SLEEP']  # 根据问题列出
for level, title, page in toc:
    if any(k in title.upper() for k in related_keywords):
        print(f'  [{page}] {title}')
```

**Step 2: 对每个相关章节，读取开头的概述/介绍部分（通常5-10页）**

不需要读完整个章节（可能上百页），只读每个章节的前几页概述和关键表格：

```python
# 对每个相关章节，读前5-10页获取核心信息
for chapter_start in related_chapters:
    for i in range(chapter_start, min(chapter_start + 10, doc.page_count)):
        text = doc[i].get_text()
        print(f'=== Page {i+1} ===')
        print(text)
```

**Step 3: 如果需要更多细节，再针对性读取特定小节**

### 视觉补充（仅表格结构丢失时）

```python
page = doc[page_num - 1]
mat = fitz.Matrix(3, 3)
pix = page.get_pixmap(matrix=mat)
pix.save('table_view.png')
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
5. **单章节问题** — TOC定位后连续读取，不要逐页搜索
6. **多章节问题** — 先TOC列出所有相关章节，再每个读概述部分，避免反复定位
