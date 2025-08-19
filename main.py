#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
明日方舟关卡计算器主程序
用于加载作战方案并模拟战斗过程
"""

import sys
import json
import argparse
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, '.')

from data_loader import DataLoader
from battle_simulator import BattleSimulator


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="明日方舟关卡计算器")
    parser.add_argument("battle_plan", help="作战方案JSON文件路径")
    parser.add_argument("--data-root", default="../ArknightsGameData/zh_CN/gamedata", 
                       help="游戏数据根目录 (默认: ../ArknightsGameData/zh_CN/gamedata)")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细日志")
    parser.add_argument("--output", "-o", help="输出结果到文件")
    
    args = parser.parse_args()
    
    # 检查作战方案文件是否存在
    battle_plan_path = Path(args.battle_plan)
    if not battle_plan_path.exists():
        print(f"错误: 作战方案文件不存在: {battle_plan_path}")
        return 1
    
    try:
        # 初始化数据加载器
        data_loader = DataLoader(args.data_root)
        print("数据加载器初始化成功")
        
        # 初始化战斗模拟器
        simulator = BattleSimulator(data_loader)
        print("战斗模拟器初始化成功")
        
        # 运行模拟
        print(f"开始模拟作战方案: {battle_plan_path}")
        result = simulator.run_simulation(str(battle_plan_path))
        
        # 输出结果
        print("\n" + "="*50)
        print("模拟结果")
        print("="*50)
        print(f"模拟成功: {'是' if result['success'] else '否'}")
        print(f"结果原因: {result['reason']}")
        print(f"最终生命点数: {result['final_life_points']}")
        print(f"战斗时间: {result['battle_time']:.2f}秒")
        print(f"部署的干员: {', '.join(result['operators_deployed'])}")
        print(f"击败敌人数: {result['enemies_defeated']}")
        
        # 详细日志
        if args.verbose and result['detailed_log']:
            print("\n详细战斗日志:")
            print("-" * 30)
            for log_entry in result['detailed_log']:
                print(f"[{log_entry['time']:6.2f}s] {log_entry['message']}")
        
        # 输出到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存到: {args.output}")
        
        return 0 if result['success'] else 1
        
    except Exception as e:
        print(f"错误: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def create_example():
    """创建示例作战方案"""
    try:
        data_loader = DataLoader()
        simulator = BattleSimulator(data_loader)
        simulator.create_example_battle_plan("example_battle_plan.json")
        print("示例作战方案已创建: example_battle_plan.json")
        return 0
    except Exception as e:
        print(f"创建示例失败: {e}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--create-example":
        exit_code = create_example()
    else:
        exit_code = main()
    sys.exit(exit_code)
