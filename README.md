# 明日方舟关卡模拟器

这是一个基于Python的明日方舟关卡模拟器，能够根据用户提供的作战方案模拟战斗过程，并判断是否能够通过指定关卡。

这个项目**刚刚开始**

## 功能特点

- 🎮 完整的明日方舟战斗系统模拟
- 📊 基于官方游戏数据 (ArknightsGameData)
- 🚀 支持干员部署、技能释放、撤退等操作
- 📝 详细的战斗日志记录
- 🔧 灵活的作战方案配置
- 📈 战斗结果分析和统计

## 系统架构

### 核心模块

1. **DataLoader** (`data_loader.py`)
   - 负责加载游戏数据文件 (JSON)
   - 提供角色、敌人、技能、关卡等数据访问接口
   - 支持数据缓存以提高性能

2. **GameEntities** (`game_entities.py`)
   - 定义游戏实体类：干员(Operator)、敌人(Enemy)、技能(Skill)等
   - 实现游戏逻辑：战斗、移动、buff效果等
   - 支持完整的属性系统和状态管理

3. **GameMap** (`game_map.py`)
   - 处理关卡地图数据和地块信息
   - 管理敌人生成和移动路径
   - 处理干员部署和阻挡逻辑
   - 实现完整的战斗循环

4. **BattleSimulator** (`battle_simulator.py`)
   - 执行用户定义的作战方案
   - 管理战斗时间轴和操作执行
   - 生成详细的模拟结果和日志

## 快速开始

### 环境要求

- Python 3.12
- numpy
- typing

### 安装依赖

```bash
cd {Directory}
pip install numpy typing
```

### 创建示例作战方案

```bash
python main.py --create-example
```

这将生成一个 `example_battle_plan.json` 文件，包含示例作战方案。

### 运行模拟

```bash
python main.py example_battle_plan.json
```

### 命令行参数

```bash
python main.py <作战方案文件> [选项]

参数:
  作战方案文件          作战方案JSON文件路径

选项:
  --data-root PATH     游戏数据根目录 (默认: ../ArknightsGameData/zh_CN/gamedata)
  --verbose, -v        显示详细日志
  --output FILE, -o    输出结果到文件
  --create-example     创建示例作战方案文件
```

## 作战方案格式

作战方案使用JSON格式定义，包含以下部分：

```json
{
  "stage_id": "main_00-01",
  "operators": [
    {
      "operator_id": "char_002_amiya",
      "custom_id": "amiya_1",
      "level": 50,
      "elite": 1,
      "potential": 0,
      "skill_level": 7
    }
  ],
  "actions": [
    {
      "type": "DEPLOY",
      "time": 2.0,
      "operator_id": "amiya_1",
      "position": {"row": 2, "col": 1},
      "direction": "RIGHT"
    },
    {
      "type": "ACTIVATE_SKILL",
      "time": 15.0,
      "operator_id": "amiya_1",
      "skill_index": 0
    },
    {
      "type": "RETREAT",
      "time": 30.0,
      "operator_id": "amiya_1"
    }
  ]
}
```

### 字段说明

#### 干员配置 (`operators`)

- `operator_id`: 官方干员ID (如 "char_002_amiya")
- `custom_id`: 自定义ID，用于在操作中引用
- `level`: 干员等级
- `elite`: 精英化等级 (0, 1, 2)
- `potential`: 潜能等级 (0-5)
- `skill_level`: 技能等级 (1-10)

#### 操作列表 (`actions`)

支持的操作类型：

1. **DEPLOY** - 部署干员
   - `time`: 执行时间（秒）
   - `operator_id`: 干员ID
   - `position`: 部署位置 `{"row": 行, "col": 列}`
   - `direction`: 朝向 ("RIGHT", "DOWN", "LEFT", "UP")

2. **RETREAT** - 撤退干员
   - `time`: 执行时间
   - `operator_id`: 干员ID

3. **ACTIVATE_SKILL** - 激活技能
   - `time`: 执行时间
   - `operator_id`: 干员ID
   - `skill_index`: 技能索引 (0, 1, 2)

## 数据依赖

本项目需要 [ArknightsGameData](https://github.com/Kengxxiao/ArknightsGameData) 提供的游戏数据。

确保数据目录结构如下：
```
Directory/
├── ArknightsGameData/
│   └── zh_CN/
│       └── gamedata/
│           ├── excel/
│           │   ├── character_table.json
│           │   ├── skill_table.json
│           │   ├── stage_table.json
│           │   └── ...
│           └── levels/
│               └── ...
└── Calculator/
    ├── main.py
    └── ...
```

## 支持的关卡

目前支持所有主线关卡和大部分活动关卡。关卡ID格式：
- 主线关卡: `main_XX-XX` (如 "main_00-01")
- 物资关卡: `sub_XX-X-X` (如 "sub_02-1-1")
- 危机合约等其他关卡

## 使用示例

### 基础使用

```python
from Calculator import DataLoader, BattleSimulator

# 初始化
data_loader = DataLoader()
simulator = BattleSimulator(data_loader)

# 运行模拟
result = simulator.run_simulation("my_battle_plan.json")

# 查看结果
if result['success']:
    print("模拟成功！")
else:
    print(f"模拟失败：{result['reason']}")
```

### 程序化创建作战方案

```python
import json

battle_plan = {
    "stage_id": "main_01-01",
    "operators": [
        {
            "operator_id": "char_123_fang",
            "custom_id": "fang",
            "level": 40,
            "elite": 1,
            "potential": 6,
            "skill_level": 4
        }
    ],
    "actions": [
        {
            "type": "DEPLOY",
            "time": 1.0,
            "operator_id": "fang",
            "position": {"row": 3, "col": 2},
            "direction": "RIGHT"
        }
    ]
}

with open("custom_plan.json", "w", encoding="utf-8") as f:
    json.dump(battle_plan, f, ensure_ascii=False, indent=2)
```
