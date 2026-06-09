---
name: schematic-reader
description: 从原理图PDF中查找硬件设计信息，基于事实回答，不捏造。
---

# 原理图识别技能

用户指定一份原理图PDF，提出问题，AI查找后给出**基于事实的回答**。

## 核心原则

1. **不捏造** — 找不到就说"未找到"，不根据经验脑补
2. **引用出处** — 回答中标注页码和原文
3. **缓存复用** — 同一份PDF的分析结果缓存，避免重复提取
4. **文字优先** — 必须先用文字提取（Step 1-3）尝试回答，只有文字提取**确实无法回答**时才使用视觉识别（Step 4）

---

## 执行流程

**严格按顺序执行 Step 1→2→3，绝大多数问题到 Step 3 即可回答。仅当 Step 3 无法给出答案时才执行 Step 4。**

### Step 1: 生成缓存（首次）

如果同目录下不存在 `<pdf名>.sch.json`，运行：

```bash
python3 scripts/extract_sch.py <pdf路径>
```

生成缓存文件，包含每页的全部文字（带坐标）和自动识别的MCU引脚列表。

### Step 2: 关键词搜索

加载缓存JSON，搜索与问题相关的文字：

```python
import json

with open('xxx.sch.json') as f:
    cache = json.load(f)

keyword = 'BAT'  # 从用户问题提取
for page in cache['pages']:
    for t in page['texts']:
        if keyword.upper() in t['text'].upper():
            print(f"Page {page['page']}, [{t['x']:.0f},{t['y']:.0f}]: {t['text']}")
```

**大多数问题（如MCU型号、接口引脚、网络名）到这一步就能找到答案。**

### Step 3: 坐标关联（确认引脚连接）

当需要确认"某信号连接到哪个引脚"时，在同一页中找Y坐标相近的引脚描述：

```python
target_y = ...  # Step 2中找到的目标信号Y坐标
tolerance = 5

for t in page['texts']:
    if abs(t['y'] - target_y) < tolerance and '/' in t['text']:
        print(f"Pin: {t['text']}")
```

**引脚连接问题到这一步就能回答。**

### Step 4: 视觉识别（仅当以上步骤无法回答时）

**仅在以下情况才使用：**
- Step 2 搜索到了相关文字，但无法仅凭文字理解电路拓扑（如分压比、滤波器结构）
- 目标页面是纯位图（缓存中 `page.type == "bitmap"`）
- 用户明确要求"画出电路"或"看一下连接方式"

```python
import fitz

doc = fitz.open(pdf_path)
page = doc[page_index]

# 以Step 2找到的坐标为中心，裁剪周围区域
clip = fitz.Rect(target_x - 100, target_y - 50, target_x + 300, target_y + 50)
mat = fitz.Matrix(8, 8)
pix = page.get_pixmap(matrix=mat, clip=clip)
pix.save('region.png')
doc.close()
# 然后用 Read 工具查看 region.png
```

**禁止跳过 Step 2/3 直接使用视觉识别。**

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

1. 不捏造，找不到就说找不到
2. 视觉识别结果与文字提取矛盾时，以文字为准
3. 多MCU系统需指明是哪个MCU的引脚
4. **禁止**在文字搜索能解决问题时使用视觉识别（浪费token、速度慢、不如文字精确）
