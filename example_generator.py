#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
示例生成器
创建不同类型的作战方案示例
"""

import json
from pathlib import Path


class ExampleGenerator:
    """示例生成器"""
    
    def __init__(self):
        self.examples_dir = Path("examples")
        self.examples_dir.mkdir(exist_ok=True)
    
    def create_basic_example(self):
        """创建基础示例 - 0-1关卡"""
        plan = {
            "stage_id": "main_00-01",
            "description": "0-1关卡基础通关示例，使用芬阻挡敌人",
            "operators": [
                {
                    "operator_id": "char_123_fang",
                    "custom_id": "fang_1",
                    "level": 30,
                    "elite": 0,
                    "potential": 6,
                    "skill_level": 4
                }
            ],
            "actions": [
                {
                    "type": "DEPLOY",
                    "time": 1.0,
                    "operator_id": "fang_1",
                    "position": {"row": 3, "col": 3},
                    "direction": "RIGHT",
                    "comment": "在路径上部署芬阻挡敌人"
                }
            ]
        }
        
        file_path = self.examples_dir / "basic_0_1.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def create_advanced_example(self):
        """创建进阶示例 - 1-7关卡"""
        plan = {
            "stage_id": "main_01-07",
            "description": "1-7关卡进阶示例，使用多个干员配合",
            "operators": [
                {
                    "operator_id": "char_123_fang",
                    "custom_id": "fang_1",
                    "level": 40,
                    "elite": 1,
                    "potential": 6,
                    "skill_level": 7
                },
                {
                    "operator_id": "char_010_chen",
                    "custom_id": "chen_1",
                    "level": 60,
                    "elite": 2,
                    "potential": 1,
                    "skill_level": 7
                },
                {
                    "operator_id": "char_002_amiya",
                    "custom_id": "amiya_1",
                    "level": 50,
                    "elite": 1,
                    "potential": 0,
                    "skill_level": 7
                },
                {
                    "operator_id": "char_017_huang",
                    "custom_id": "huang_1",
                    "level": 45,
                    "elite": 1,
                    "potential": 2,
                    "skill_level": 6
                }
            ],
            "actions": [
                {
                    "type": "DEPLOY",
                    "time": 2.0,
                    "operator_id": "fang_1",
                    "position": {"row": 4, "col": 2},
                    "direction": "RIGHT",
                    "comment": "先锋芬部署在前排阻挡"
                },
                {
                    "type": "DEPLOY",
                    "time": 8.0,
                    "operator_id": "amiya_1", 
                    "position": {"row": 3, "col": 1},
                    "direction": "RIGHT",
                    "comment": "术师阿米娅部署在高台"
                },
                {
                    "type": "DEPLOY",
                    "time": 15.0,
                    "operator_id": "huang_1",
                    "position": {"row": 2, "col": 3},
                    "direction": "DOWN",
                    "comment": "重装黄部署补强防线"
                },
                {
                    "type": "ACTIVATE_SKILL",
                    "time": 25.0,
                    "operator_id": "amiya_1",
                    "skill_index": 0,
                    "comment": "激活阿米娅技能增强输出"
                },
                {
                    "type": "DEPLOY",
                    "time": 40.0,
                    "operator_id": "chen_1",
                    "position": {"row": 4, "col": 4},
                    "direction": "LEFT", 
                    "comment": "近卫陈部署处理漏过的敌人"
                },
                {
                    "type": "ACTIVATE_SKILL",
                    "time": 60.0,
                    "operator_id": "chen_1",
                    "skill_index": 0,
                    "comment": "激活陈技能清理残余敌人"
                }
            ]
        }
        
        file_path = self.examples_dir / "advanced_1_7.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def create_skill_showcase_example(self):
        """创建技能展示示例"""
        plan = {
            "stage_id": "main_00-01",
            "description": "技能使用示例，展示技能时机控制",
            "operators": [
                {
                    "operator_id": "char_123_fang",
                    "custom_id": "fang_tank",
                    "level": 30,
                    "elite": 0,
                    "potential": 6,
                    "skill_level": 4
                },
                {
                    "operator_id": "char_002_amiya",
                    "custom_id": "amiya_dps",
                    "level": 50,
                    "elite": 1,
                    "potential": 0,
                    "skill_level": 7
                }
            ],
            "actions": [
                {
                    "type": "DEPLOY",
                    "time": 1.0,
                    "operator_id": "fang_tank",
                    "position": {"row": 3, "col": 3},
                    "direction": "RIGHT"
                },
                {
                    "type": "DEPLOY",
                    "time": 3.0,
                    "operator_id": "amiya_dps",
                    "position": {"row": 2, "col": 2},
                    "direction": "RIGHT"
                },
                {
                    "type": "ACTIVATE_SKILL",
                    "time": 10.0,
                    "operator_id": "fang_tank",
                    "skill_index": 0,
                    "comment": "芬技能增加费用回复"
                },
                {
                    "type": "ACTIVATE_SKILL",
                    "time": 15.0,
                    "operator_id": "amiya_dps",
                    "skill_index": 0,
                    "comment": "阿米娅技能增强攻击力"
                },
                {
                    "type": "ACTIVATE_SKILL",
                    "time": 35.0,
                    "operator_id": "amiya_dps",
                    "skill_index": 0,
                    "comment": "再次激活阿米娅技能"
                }
            ]
        }
        
        file_path = self.examples_dir / "skill_showcase.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def create_retreat_example(self):
        """创建撤退示例"""
        plan = {
            "stage_id": "main_00-01",
            "description": "撤退操作示例，展示干员替换策略",
            "operators": [
                {
                    "operator_id": "char_123_fang",
                    "custom_id": "fang_early",
                    "level": 20,
                    "elite": 0,
                    "potential": 6,
                    "skill_level": 1
                },
                {
                    "operator_id": "char_010_chen",
                    "custom_id": "chen_strong",
                    "level": 60,
                    "elite": 2,
                    "potential": 1,
                    "skill_level": 7
                }
            ],
            "actions": [
                {
                    "type": "DEPLOY",
                    "time": 1.0,
                    "operator_id": "fang_early",
                    "position": {"row": 3, "col": 3},
                    "direction": "RIGHT",
                    "comment": "前期使用芬阻挡"
                },
                {
                    "type": "RETREAT",
                    "time": 20.0,
                    "operator_id": "fang_early",
                    "comment": "撤退芬为强力干员让位"
                },
                {
                    "type": "DEPLOY",
                    "time": 21.0,
                    "operator_id": "chen_strong",
                    "position": {"row": 3, "col": 3},
                    "direction": "RIGHT",
                    "comment": "部署陈接替防线"
                },
                {
                    "type": "ACTIVATE_SKILL",
                    "time": 30.0,
                    "operator_id": "chen_strong",
                    "skill_index": 0,
                    "comment": "激活陈技能"
                }
            ]
        }
        
        file_path = self.examples_dir / "retreat_example.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def generate_all_examples(self):
        """生成所有示例"""
        examples = []
        
        examples.append(self.create_basic_example())
        examples.append(self.create_advanced_example())
        examples.append(self.create_skill_showcase_example())
        examples.append(self.create_retreat_example())
        
        print("已生成示例文件:")
        for example in examples:
            print(f"  - {example}")
        
        return examples


if __name__ == "__main__":
    generator = ExampleGenerator()
    generator.generate_all_examples()
