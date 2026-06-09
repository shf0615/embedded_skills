# BSP Engineer Skills

本目录包含两个独立的AI技能，用于嵌入式BSP开发：

## 技能列表

| 技能 | 路径 | 用途 |
|------|------|------|
| **原理图识别** | `schematic-reader/SKILL.md` | 从原理图PDF提取引脚映射、接口分配、电源域等 |
| **芯片手册查阅** | `datasheet-lookup/SKILL.md` | 从芯片手册按需查询寄存器定义、引脚复用表等 |

## 典型工作流

```
1. 原理图识别 → 提取MCU型号、引脚-网络对应关系
2. 芯片手册查阅 → 确认引脚复用配置、外设参数范围
3. 交叉校验 → 验证原理图连接与手册定义一致
4. 代码生成 → 输出BSP初始化代码
```

## 辅助文件

- `prompts/code_generation_templates.md` — BSP代码生成模板
- `prompts/code_review_checklist.md` — BSP校验检查清单
