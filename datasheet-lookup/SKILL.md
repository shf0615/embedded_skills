---
name: datasheet-lookup
description: 从芯片用户手册/数据手册PDF中按需查询引脚复用表、寄存器定义、外设配置参数、时钟树、电气特性等信息。采用目录定位+分页读取策略，避免一次性加载大型PDF。
---

# 芯片用户手册查阅技能

从芯片用户手册/数据手册（PDF）中按需提取寄存器定义、引脚复用表、外设配置参数等信息。

## 触发条件

当用户请求涉及以下场景时激活：
- 查询某芯片的引脚复用表（AF mapping）
- 查询某外设的寄存器定义和配置流程
- 查询时钟树和分频关系
- 查询电气特性（驱动能力、电压阈值等）
- 校验BSP代码中的外设参数是否与手册一致

## 核心原理

芯片用户手册通常几百页PDF。采用**按需查找**策略，不要一次性全读。先读目录定位章节，再精确读取所需页面。

---

## 查找流程

### Step 1: 读取目录（前3-5页）

```python
import fitz
doc = fitz.open('reference_manual.pdf')

# 读取目录页（通常前3-5页）
for i in range(min(5, doc.page_count)):
    page = doc[i]
    text = page.get_text()
    print(f'=== Page {i+1} ===')
    print(text)
```

从目录中定位关键章节页码：
- Pin definitions / Pinout（引脚定义）
- Alternate function mapping（复用功能表）
- Memory map（内存映射/外设基地址）
- 各外设章节（USART, I2C, SPI, TIM, ADC...）
- Clock tree（时钟树）
- Electrical characteristics（电气特性）

### Step 2: 引脚复用表（最关键）

通常标题为 "Alternate function mapping" 或 "Pin mux table"。

**读取策略：**
- 如果表格跨多页，只读取涉及到的引脚所在页
- 使用 `page.get_text()` 提取文字，然后解析表格结构
- 记录完整的 AF 编号（AF0~AF15），不要省略

```python
# 定位到引脚复用表页面后
page = doc[pin_mux_page_index]
text = page.get_text()
# 解析表格...
```

### Step 3: 具体外设章节（按需）

仅当需要配置某个外设时才读取。提取：
- 外设特性（最大频率、缓冲区大小、模式支持）
- 寄存器列表和关键寄存器说明
- 典型配置流程（手册中的 "Configuration procedure"）
- 时钟要求（哪个总线、是否需要特定时钟源）

### Step 4: 时钟树（按需）

当需要配置时钟或确认外设时钟频率时：
- PLL 配置范围
- 各总线（AHB, APB1, APB2）最大频率
- 外设时钟选择器

### Step 5: 电气特性（校验时）

- GPIO 驱动能力（mA）
- 输入电压阈值（VIH, VIL）
- 5V tolerant 引脚列表
- ADC 参考电压范围

---

## 信息记录格式

提取的信息按以下格式记录：

```json
{
  "source": "RM0090 Rev 19",
  "chapter": "8.3 GPIO alternate function",
  "page": 272,
  "extracted": {
    "pin": "PA9",
    "af_table": {"AF7": "USART1_TX"},
    "notes": "5V tolerant when configured as GPIO"
  }
}
```

---

## 常见芯片手册结构

### STM32 系列
- **Reference Manual (RM)**: 寄存器细节、外设配置
- **Datasheet (DS)**: 引脚定义、电气特性、封装
- **注意**：引脚复用表在 Datasheet 中，外设细节在 Reference Manual 中

### NXP KW45/K系列
- **Reference Manual**: 所有外设、引脚复用（Port MUX）
- **Datasheet**: 电气特性
- 引脚复用通过 PORT 模块的 PCR 寄存器配置（MUX field）

### ESP32 系列
- **Technical Reference Manual**: 所有外设
- **Datasheet**: 引脚定义
- IO_MUX 功能表在 TRM 中

### 博流 BL602/BL616 系列
- **Reference Manual**: 所有信息集中
- 引脚复用通过 GLB 寄存器配置

### 通用 RISC-V（如全志D1）
- **User Manual**: 所有信息集中
- 引脚复用通过 PIO 控制器寄存器

---

## 注意事项

1. **不猜测**：如果手册中找不到对应信息，明确说明，不要编造
2. **引用来源**：每个配置决策标注来源（"手册 Table 9, Page 63"）
3. **保守配置**：不确定时选择安全值（更低速度、更强驱动）
4. **版本敏感**：注意手册版本号，不同版本可能有差异
5. **大型PDF优化**：几百页的手册不要一次性读取，按需分页读取关键章节
