# SpinQLabLink

SpinQLabLink是一个Python库，用于与SpinQ量子计算实验平台进行交互。它提供了一套简单的API，允许用户启动实验、上传数据、获取实验结果等。

## 安装

### 从PyPI安装

```bash
pip install spinqlablink
```

### 从源代码安装

```bash
# 克隆仓库
git clone https://github.com/spinqtech/spinqlablink.git
cd spinqlablink

# 安装依赖
pip install -r requirements.txt

# 安装
pip install .

# 或者安装开发模式
pip install -e .
```

## 使用方法

### 使用Python API

```python
from spinqlablink import api

# 启动实验
experiment_id = "exp-001"
experiment_type = "circuit"
config = {
    "circuit": {...},
    "shots": 1000,
    # 其他配置
}

success = api.start_experiment(
    experiment_id=experiment_id,
    experiment_type=experiment_type,
    config=config
)

# 上传数据
data = {...}  # 实验数据
api.upload_experiment_data(experiment_id, data)

# 结束实验
api.finish_experiment(experiment_id, status="completed")

# 获取结果
result = api.get_experiment_result(experiment_id)
print(f"实验结果: {result}")
```

### 直接使用SpinQLabLink类

对于需要更细粒度控制的场景，可以直接使用`SpinQLabLink`类：

```python
from spinqlablink import SpinQLabLink
from utils.types import ExperimentType

# 创建连接
spinqlablink = SpinQLabLink("192.168.9.92", 8181, "username", "password")
spinqlablink.connect()

# 等待登录完成
if not spinqlablink.wait_for_login():
    print("登录失败")
    exit(1)

# 注册实验
experiment, experiment_params = spinqlablink.register_experiment(ExperimentType.RABI_OSCILLATIONS)

# 设置实验参数
experiment_params.freq_h = 37.852105  # 氢共振频率 (MHz)
experiment_params.freq_p = 15.322872  # 磷共振频率 (MHz)
experiment_params.makePps = False     # 生成 PPS 信号
experiment_params.samplePath = 0      # 采样路径：0=氢通道，1=磷通道

# 运行实验
spinqlablink.run_experiment()

# 等待实验完成
spinqlablink.wait_for_experiment_completion()

# 获取结果
result = spinqlablink.get_experiment_result()

# 断开连接
spinqlablink.disconnect()
```

### 使用命令行

安装后，可以使用命令行工具`spinqlablink`进行操作：

```bash
# 启动实验
spinqlablink start --type circuit --config config.json

# 上传数据
spinqlablink upload --id exp-001 --data data.json

# 结束实验
spinqlablink finish --id exp-001 --status completed

# 获取结果
spinqlablink result --id exp-001 --format json --output result.json

# 获取状态
spinqlablink status --id exp-001

# 获取实验列表
spinqlablink list --limit 10 --offset 0
```

## 日志配置

可以通过以下方式配置日志：

```python
from spinqlablink.utils import setup_default_logger

# 设置日志级别和日志目录
logger = setup_default_logger(log_level='debug', log_dir='logs')

# 直接使用导出的日志函数
from spinqlablink.utils import info, error

info("这是一条信息日志")
error("这是一条错误日志")
```

## 支持的实验类型

SpinQLabLink支持多种量子计算实验类型，可以通过`ExperimentType`枚举类使用：

```python
from utils.types import ExperimentType

# 模块一实验
ExperimentType.NMR_PHENOMENON_AND_SIGNAL  # NMR现象与信号
ExperimentType.RABI_OSCILLATIONS          # 拉比振荡
ExperimentType.QUANTUM_BIT                # 量子比特
ExperimentType.QUANTUM_DECOHERENCE_T1     # 量子退相干T1
ExperimentType.QUANTUM_DECOHERENCE_T2     # 量子退相干T2
ExperimentType.QUANTUM_CONTROL            # 量子控制
ExperimentType.QUANTUM_SYSTEM_INITIALIZATION  # 量子系统初始化
ExperimentType.QUANTUM_GATES_AND_CIRCUIT_PULSE    # 量子门与电路 (脉冲模式)
ExperimentType.QUANTUM_GATES_AND_CIRCUIT_CIRCUIT  # 量子门与电路 (电路模式)
ExperimentType.QUANTUM_STATE_TOMOGRAPHY           # 量子态层析

# 模块二实验
ExperimentType.QUANTUM_COMPUTING_TASK      # 量子计算任务
ExperimentType.INTRODUCTION_TO_QUANTUM_COMPUTING  # 量子计算导论
ExperimentType.DEUTSCH_ALGORITHM           # Deutsch算法
ExperimentType.BERNSTEIN_VARIRANI_ALGORITHM  # Bernstein-Varirani算法
ExperimentType.GROVER_ALGORITHM            # Grover算法
ExperimentType.QFT_ALGORITHM               # 量子傅里叶变换
ExperimentType.HHL_ALGORITHM               # HHL算法
ExperimentType.VQE_ALGORITHM               # 变分量子特征求解器
ExperimentType.QAOA_ALGORITHM              # 量子近似优化算法

# 模块三实验
ExperimentType.SPIN_ECHO                   # 自旋回波
ExperimentType.DYNAMIC_DECOUPLING          # 动态解耦
ExperimentType.SHAPE_PULSE                 # 形状脉冲
ExperimentType.NUMERICAL_OPTIMIZATION_PULSE  # 数值优化脉冲

# 模块四实验
ExperimentType.PHYSICAL_LAYER_EXPERIMENT         # 物理层实验
ExperimentType.CIRCUIT_LAYER_EXPERIMENT_PULSE    # 电路层实验 (脉冲模式)
ExperimentType.CIRCUIT_LAYER_EXPERIMENT_CIRCUIT  # 电路层实验 (电路模式)
```

## 实验参数配置

不同类型的实验需要不同的参数配置。以下是一些常见实验的参数示例：

### Rabi振荡实验参数

```python
# 注册Rabi振荡实验
rabi, rabi_para = spinqlablink.register_experiment(ExperimentType.RABI_OSCILLATIONS)

# 设置磷脉冲序列
import json
rabi_para.set_pulse(json.dumps({
    "hPulse": [{"width": 30, "am": 100, "phase": 90, "freshift": 0}],
    "pPulse": []
}))

# 设置频率和采样参数
rabi_para.freq_h = 37.852105  # 氢共振频率 (MHz)
rabi_para.freq_p = 15.322872  # 磷共振频率 (MHz)
rabi_para.makePps = False     # 生成 PPS 信号
rabi_para.samplePath = 0      # 采样路径：0=氢通道，1=磷通道
rabi_para.custom_freq = False # 使用自定义频率
```

### NMR现象与信号实验参数

```python
# 注册NMR实验
nmr, nmr_para = spinqlablink.register_experiment(ExperimentType.NMR_PHENOMENON_AND_SIGNAL)

# 设置脉冲参数
nmr_para.set_pulse(json.dumps({
    "hPulse": [{"width": 20, "am": 100, "phase": 0, "freshift": 0}],
    "pPulse": []
}))

# 设置其他参数
nmr_para.freq_h = 37.852105   # 氢共振频率
nmr_para.freq_p = 15.322872   # 磷共振频率
nmr_para.samplePath = 0       # 采样路径
```

## 连接管理

SpinQLabLink提供了完善的连接管理功能：

```python
# 创建连接
spinqlablink = SpinQLabLink(host, port, account, password)

# 连接到服务器
spinqlablink.connect()

# 等待登录完成 (可设置超时时间，单位为秒)
spinqlablink.wait_for_login(timeout=10)

# 检查连接状态
is_connected = spinqlablink.get_connection()

# 登出并断开连接
spinqlablink.logout()
spinqlablink.disconnect()
```

## 命令行帮助

```bash
spinqlablink --help
```

## 许可证

Apache License 2.0

## 实验通信框架库结构图

![实验通信框架库结构图](实验通信框架库结构图.png)

## 实验通信框架业务流程图

![实验通信框架业务流程图](实验通信框架业务流程图.png)

## 开发指南

如果您想要扩展或修改SpinQLabLink，以下是一些指导原则：

### 项目结构

```
spinqlablink/
├── src/                      # 源代码目录
│   ├── __init__.py           # 包初始化
│   ├── cli.py                # 命令行接口
│   ├── spinqlablink.py       # 主要API实现
│   ├── connection/           # 连接相关模块
│   │   ├── connection.py     # 网络连接实现
│   │   ├── protocol.py       # 通信协议
│   │   └── heartbeat.py      # 心跳机制
│   ├── devices/              # 设备相关模块
│   │   └── device.py         # 设备实现
│   ├── experiment/           # 实验相关模块
│   │   ├── experiment_base.py # 实验基类
│   │   ├── ExperimentManager.py # 实验管理器
│   │   ├── exp_pulse.py      # 脉冲实验
│   │   └── exp_rabi.py       # Rabi实验
│   └── utils/                # 工具模块
│       ├── logger.py         # 日志工具
│       ├── types.py          # 类型定义
│       └── exceptions.py     # 异常定义
├── examples/                 # 示例代码
└── setup.py                  # 安装配置
```

## 贡献指南

我们欢迎各种形式的贡献，包括但不限于：

- 报告问题
- 提交功能请求
- 提交代码改进
- 改进文档

### 代码规范

- 遵循PEP 8代码风格
- 为所有新函数和类添加文档字符串
- 添加适当的测试
- 确保所有测试通过

### 问题报告

如果您发现问题，请通过GitHub Issues报告，并包含以下信息：

- 问题描述
- 重现步骤
- 预期行为
- 实际行为
- 环境信息（操作系统、Python版本等）