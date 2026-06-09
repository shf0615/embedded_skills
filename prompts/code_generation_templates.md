# BSP 代码生成模板

## 使用说明

根据已提取的原理图信息和手册信息，按以下模板生成代码。
选择与目标平台匹配的风格。

---

## 通用头文件模板 (bsp_pin_map.h)

```c
/**
 * @file    bsp_pin_map.h
 * @brief   硬件引脚映射定义
 * @note    基于原理图 [FILE] 自动生成
 *          MCU: [PART_NUMBER] ([PACKAGE])
 * @date    [DATE]
 */

#ifndef BSP_PIN_MAP_H
#define BSP_PIN_MAP_H

/* ========== 电源域 ========== */
// VDD_MCU: 3.3V (来源: [SOURCE])
// VDD_IO:  3.3V (来源: [SOURCE])

/* ========== DEBUG UART ========== */
// 连接: MCU [PIN] <---> [TARGET_DEVICE] [TARGET_PIN]
// 手册: [REFERENCE_MANUAL] Table [X], AF[N]
#define DEBUG_UART_INSTANCE     [USART1]
#define DEBUG_UART_TX_PORT      [GPIO_PORT]
#define DEBUG_UART_TX_PIN       [GPIO_PIN_X]
#define DEBUG_UART_TX_AF        [GPIO_AFx_USARTx]
#define DEBUG_UART_RX_PORT      [GPIO_PORT]
#define DEBUG_UART_RX_PIN       [GPIO_PIN_X]
#define DEBUG_UART_RX_AF        [GPIO_AFx_USARTx]
#define DEBUG_UART_BAUDRATE     [115200]

/* ========== SENSOR I2C ========== */
// 连接: MCU [PIN] <---> [SENSOR] [PIN], 上拉 [VALUE]
// 手册: [REFERENCE_MANUAL] Table [X], AF[N]
#define SENSOR_I2C_INSTANCE     [I2C1]
#define SENSOR_I2C_SCL_PORT     [GPIO_PORT]
#define SENSOR_I2C_SCL_PIN      [GPIO_PIN_X]
#define SENSOR_I2C_SCL_AF       [GPIO_AFx_I2Cx]
#define SENSOR_I2C_SDA_PORT     [GPIO_PORT]
#define SENSOR_I2C_SDA_PIN      [GPIO_PIN_X]
#define SENSOR_I2C_SDA_AF       [GPIO_AFx_I2Cx]
#define SENSOR_I2C_SPEED        [400000]  // Hz, 手册最大: [MAX]Hz
#define SENSOR_I2C_ADDR         [0x76]    // 器件: [DEVICE], [7bit/8bit]

/* ========== GPIO ========== */
// [FUNCTION]: [DESCRIPTION]
#define [NAME]_PORT             [GPIO_PORT]
#define [NAME]_PIN              [GPIO_PIN_X]
#define [NAME]_ACTIVE_LEVEL     [0/1]     // 原理图: [上拉/下拉/浮空]

#endif /* BSP_PIN_MAP_H */
```

---

## 外设初始化模板

### UART 模板

```c
/**
 * @file    bsp_uart.c
 * @brief   UART BSP 驱动
 * @note    外设: [INSTANCE]
 *          TX: [PIN] -> [TARGET]
 *          RX: [PIN] -> [TARGET]
 *          波特率: [BAUD]
 */

#include "bsp_uart.h"
#include "bsp_pin_map.h"

static [HANDLE_TYPE] huart;

/**
 * @brief  初始化 UART 外设
 * @retval 0 成功, -1 失败
 */
int BSP_UART_Init(void)
{
    // 1. 使能时钟
    [CLK_ENABLE_GPIO]();
    [CLK_ENABLE_UART]();

    // 2. 配置 GPIO
    [GPIO_CONFIG_CODE]

    // 3. 配置 UART
    huart.Instance = [INSTANCE];
    huart.Init.BaudRate = DEBUG_UART_BAUDRATE;
    huart.Init.WordLength = [WORD_LEN];
    huart.Init.StopBits = [STOP_BITS];
    huart.Init.Parity = [PARITY];
    huart.Init.Mode = [MODE];
    huart.Init.HwFlowCtl = [FLOW_CTL];

    if ([INIT_FUNCTION](&huart) != [SUCCESS]) {
        return -1;
    }

    return 0;
}

/**
 * @brief  发送数据
 * @param  data: 数据缓冲区
 * @param  len: 数据长度
 * @param  timeout_ms: 超时时间
 * @retval 实际发送字节数, -1 表示错误
 */
int BSP_UART_Send(const uint8_t *data, uint16_t len, uint32_t timeout_ms)
{
    if (data == NULL || len == 0) return -1;
    [SEND_IMPLEMENTATION]
}

/**
 * @brief  接收数据
 */
int BSP_UART_Receive(uint8_t *data, uint16_t len, uint32_t timeout_ms)
{
    if (data == NULL || len == 0) return -1;
    [RECEIVE_IMPLEMENTATION]
}
```

### I2C 模板

```c
/**
 * @file    bsp_i2c.c
 * @brief   I2C BSP 驱动
 * @note    外设: [INSTANCE]
 *          SCL: [PIN] (开漏, 外部上拉 [VALUE])
 *          SDA: [PIN] (开漏, 外部上拉 [VALUE])
 *          总线设备: [DEVICE_LIST]
 */

#include "bsp_i2c.h"
#include "bsp_pin_map.h"

static [HANDLE_TYPE] hi2c;

int BSP_I2C_Init(void)
{
    // 1. 使能时钟
    [CLK_ENABLE_GPIO]();
    [CLK_ENABLE_I2C]();

    // 2. GPIO: 开漏 + 无内部上拉（外部已有）
    [GPIO_CONFIG_CODE]
    // 注意: Pull = NOPULL，因为原理图 [REF] 已有 [VALUE] 外部上拉

    // 3. I2C 配置
    hi2c.Instance = [INSTANCE];
    [I2C_CONFIG_CODE]
    // 速度: [SPEED]Hz (手册最大: [MAX]Hz, 器件最大: [DEVICE_MAX]Hz)

    if ([INIT_FUNCTION](&hi2c) != [SUCCESS]) {
        return -1;
    }

    return 0;
}

/**
 * @brief  向指定设备写入数据
 * @param  dev_addr: 7位设备地址（不含R/W位）
 * @param  reg: 寄存器地址
 * @param  data: 写入数据
 * @param  len: 数据长度
 */
int BSP_I2C_WriteReg(uint8_t dev_addr, uint8_t reg,
                     const uint8_t *data, uint16_t len)
{
    [WRITE_IMPLEMENTATION]
}

/**
 * @brief  从指定设备读取数据
 */
int BSP_I2C_ReadReg(uint8_t dev_addr, uint8_t reg,
                    uint8_t *data, uint16_t len)
{
    [READ_IMPLEMENTATION]
}

/**
 * @brief  I2C 总线恢复（当总线被锁死时）
 * @note   通过手动 toggle SCL 9次释放从设备
 */
void BSP_I2C_BusRecovery(void)
{
    // 将 SCL/SDA 切换为 GPIO 输出
    // 发送 9 个 SCL 脉冲
    // 检查 SDA 是否释放
    // 重新配置为 AF 模式
    [BUS_RECOVERY_IMPLEMENTATION]
}
```

### SPI 模板

```c
/**
 * @file    bsp_spi.c
 * @brief   SPI BSP 驱动
 * @note    外设: [INSTANCE]
 *          SCK:  [PIN] (AF[N])
 *          MISO: [PIN] (AF[N])
 *          MOSI: [PIN] (AF[N])
 *          CS:   [PIN] (GPIO, 软件控制)
 *          连接: [TARGET_DEVICE]
 *          模式: CPOL=[X] CPHA=[X] (参考器件手册时序图)
 */

#include "bsp_spi.h"
#include "bsp_pin_map.h"

static [HANDLE_TYPE] hspi;

int BSP_SPI_Init(void)
{
    [SPI_INIT_IMPLEMENTATION]
}

/**
 * @brief  SPI 全双工传输
 */
int BSP_SPI_TransmitReceive(const uint8_t *tx, uint8_t *rx,
                            uint16_t len, uint32_t timeout_ms)
{
    [TRANSFER_IMPLEMENTATION]
}

static inline void BSP_SPI_CS_Low(void)  { [CS_LOW]; }
static inline void BSP_SPI_CS_High(void) { [CS_HIGH]; }
```

---

## 代码生成规则

1. **占位符替换**：所有 `[PLACEHOLDER]` 必须根据实际提取的信息替换
2. **不留空实现**：如果某个函数无法确定实现，写清楚注释说明缺少什么信息
3. **注释溯源**：关键配置值旁标注来源（手册页码/原理图位号）
4. **防御性编程**：参数检查、超时保护、错误返回
5. **不过度抽象**：一个外设一个文件，不搞"通用外设框架"
