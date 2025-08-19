#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
明日方舟关卡计算器快速启动脚本
提供简化的用户交互界面
"""

import os
import sys
import json
from pathlib import Path
from data_loader import DataLoader
from battle_simulator import BattleSimulator
from example_generator import ExampleGenerator


def print_banner():
    """打印程序横幅"""
    print("=" * 60)
    print("           明日方舟关卡计算器")
    print("      Arknights Battle Calculator")
    print("=" * 60)
    print()


def list_examples():
    """列出所有可用的示例"""
    examples_dir = Path("examples")
    if not examples_dir.exists():
        print("未找到示例文件夹，正在生成示例...")
        generator = ExampleGenerator()
        generator.generate_all_examples()
        print()
    
    examples = list(examples_dir.glob("*.json"))
    if examples:
        print("可用的示例作战方案:")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example.name}")
        return examples
    else:
        print("未找到示例文件")
        return []


def list_stages():
    """列出部分常用关卡"""
    common_stages = [
        ("main_00-01", "0-1 坍塌"),
        ("main_00-02", "0-2 突围"), 
        ("main_01-01", "1-1 封锁"),
        ("main_01-07", "1-7"),
        ("main_02-01", "2-1"),
        ("sub_02-1-1", "空中威胁"),
        ("sub_02-2-1", "粉碎防御"),
    ]
    
    print("常用关卡ID:")
    for stage_id, stage_name in common_stages:
        print(f"  {stage_id} - {stage_name}")
    print()


def run_example():
    """运行示例"""
    examples = list_examples()
    if not examples:
        return
    
    print()
    try:
        choice = int(input("请选择要运行的示例 (输入数字): ")) - 1
        if 0 <= choice < len(examples):
            example_file = examples[choice]
            print(f"\n运行示例: {example_file.name}")
            print("-" * 40)
            
            # 运行模拟
            os.system(f"python main.py {example_file} --verbose")
        else:
            print("无效的选择")
    except (ValueError, KeyboardInterrupt):
        print("已取消")


def create_custom_plan():
    """创建自定义作战方案"""
    print("创建自定义作战方案")
    print("-" * 20)
    
    # 显示常用关卡
    list_stages()
    
    try:
        stage_id = input("请输入关卡ID: ").strip()
        if not stage_id:
            print("关卡ID不能为空")
            return
        
        print("\n请输入干员配置 (输入空行结束):")
        operators = []
        
        while True:
            print(f"\n干员 {len(operators) + 1}:")
            operator_id = input("  干员ID (如 char_123_fang): ").strip()
            if not operator_id:
                break
            
            custom_id = input("  自定义ID: ").strip() or f"op_{len(operators) + 1}"
            level = int(input("  等级 (默认30): ") or "30")
            elite = int(input("  精英化 (0-2, 默认0): ") or "0")
            skill_level = int(input("  技能等级 (默认4): ") or "4")
            
            operators.append({
                "operator_id": operator_id,
                "custom_id": custom_id,
                "level": level,
                "elite": elite,
                "potential": 0,
                "skill_level": skill_level
            })
        
        if not operators:
            print("至少需要一个干员")
            return
        
        print("\n请输入操作序列 (输入空行结束):")
        actions = []
        
        while True:
            print(f"\n操作 {len(actions) + 1}:")
            action_type = input("  操作类型 (DEPLOY/RETREAT/ACTIVATE_SKILL): ").strip().upper()
            if not action_type:
                break
            
            if action_type not in ["DEPLOY", "RETREAT", "ACTIVATE_SKILL"]:
                print("  无效的操作类型")
                continue
            
            time = float(input("  执行时间 (秒): "))
            operator_id = input("  干员ID: ").strip()
            
            action = {
                "type": action_type,
                "time": time,
                "operator_id": operator_id
            }
            
            if action_type == "DEPLOY":
                row = int(input("  位置行: "))
                col = int(input("  位置列: "))
                direction = input("  朝向 (RIGHT/DOWN/LEFT/UP, 默认RIGHT): ").strip() or "RIGHT"
                
                action["position"] = {"row": row, "col": col}
                action["direction"] = direction
            
            elif action_type == "ACTIVATE_SKILL":
                skill_index = int(input("  技能索引 (0-2, 默认0): ") or "0")
                action["skill_index"] = skill_index
            
            actions.append(action)
        
        if not actions:
            print("至少需要一个操作")
            return
        
        # 创建作战方案
        plan = {
            "stage_id": stage_id,
            "description": f"自定义方案 - {stage_id}",
            "operators": operators,
            "actions": actions
        }
        
        # 保存到文件
        filename = f"custom_{stage_id.replace('-', '_')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        
        print(f"\n作战方案已保存到: {filename}")
        
        # 询问是否立即运行
        if input("是否立即运行此方案? (y/N): ").strip().lower() == 'y':
            print(f"\n运行方案: {filename}")
            print("-" * 40)
            os.system(f"python main.py {filename} --verbose")
    
    except (ValueError, KeyboardInterrupt):
        print("\n已取消")


def main_menu():
    """主菜单"""
    while True:
        print_banner()
        print("请选择操作:")
        print("  1. 运行示例作战方案")
        print("  2. 创建自定义作战方案")
        print("  3. 生成新的示例")
        print("  4. 查看帮助")
        print("  0. 退出")
        print()
        
        try:
            choice = input("请输入选择 (0-4): ").strip()
            
            if choice == "1":
                run_example()
            elif choice == "2":
                create_custom_plan()
            elif choice == "3":
                generator = ExampleGenerator()
                generator.generate_all_examples()
                print("示例生成完成！")
            elif choice == "4":
                print("\n帮助信息:")
                print("- 查看 README.md 了解详细功能")
                print("- 查看 USER_GUIDE.md 了解使用方法")
                print("- 查看 examples/ 目录下的示例文件")
                print("- 命令行用法: python main.py <方案文件> [选项]")
            elif choice == "0":
                print("再见！")
                break
            else:
                print("无效的选择")
            
            if choice != "0":
                input("\n按回车键继续...")
                print()
        
        except KeyboardInterrupt:
            print("\n\n再见！")
            break


if __name__ == "__main__":
    main_menu()
