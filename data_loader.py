#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
明日方舟游戏数据加载器
负责从ArknightsGameData文件夹中加载各种JSON数据
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path


class DataLoader:
    """游戏数据加载器"""
    
    def __init__(self, data_root: str = "../ArknightsGameData/zh_CN/gamedata"):
        """
        初始化数据加载器
        
        Args:
            data_root: 游戏数据根目录路径
        """
        self.data_root = Path(data_root)
        self.cache = {}  # 数据缓存
        
        # 验证数据目录是否存在
        if not self.data_root.exists():
            raise FileNotFoundError(f"游戏数据目录不存在: {self.data_root}")
    
    def load_json(self, file_path: str) -> Dict[str, Any]:
        """
        加载JSON文件
        
        Args:
            file_path: 相对于data_root的文件路径
            
        Returns:
            解析后的JSON数据
        """
        cache_key = file_path
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        full_path = self.data_root / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {full_path}")
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.cache[cache_key] = data
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败 {full_path}: {e}")
    
    def load_character_table(self) -> Dict[str, Any]:
        """加载角色数据表"""
        return self.load_json("excel/character_table.json")
    
    def load_skill_table(self) -> Dict[str, Any]:
        """加载技能数据表"""
        return self.load_json("excel/skill_table.json")
    
    def load_stage_table(self) -> Dict[str, Any]:
        """加载关卡数据表"""
        return self.load_json("excel/stage_table.json")
    
    def load_enemy_database(self) -> Dict[str, Any]:
        """加载敌人数据库"""
        return self.load_json("levels/enemydata/enemy_database.json")
    
    def load_buff_table(self) -> Dict[str, Any]:
        """加载buff数据表"""
        return self.load_json("buff_table.json")
    
    def load_range_table(self) -> Dict[str, Any]:
        """加载攻击范围数据表"""
        return self.load_json("excel/range_table.json")
    
    def load_level_data(self, level_id: str) -> Dict[str, Any]:
        """
        加载关卡数据
        
        Args:
            level_id: 关卡ID，例如 "Obt/Main/level_main_00-01"
            
        Returns:
            关卡数据
        """
        # 构建文件路径
        # 将 "Obt/Main/level_main_00-01" 转换为 "levels/obt/main/level_main_00-01.json"
        parts = level_id.split('/')
        if len(parts) >= 3:
            category = parts[0].lower()  # Obt -> obt
            subcategory = parts[1].lower()  # Main -> main  
            filename = parts[2]  # level_main_00-01
            file_path = f"levels/{category}/{subcategory}/{filename}.json"
        else:
            # 如果格式不匹配，直接使用原始格式
            file_path = f"levels/{level_id.lower()}.json"
        
        return self.load_json(file_path)
    
    def get_character_by_id(self, char_id: str) -> Optional[Dict[str, Any]]:
        """
        根据角色ID获取角色数据
        
        Args:
            char_id: 角色ID
            
        Returns:
            角色数据，如果不存在返回None
        """
        character_table = self.load_character_table()
        return character_table.get(char_id)
    
    def get_stage_by_id(self, stage_id: str) -> Optional[Dict[str, Any]]:
        """
        根据关卡ID获取关卡数据
        
        Args:
            stage_id: 关卡ID
            
        Returns:
            关卡数据，如果不存在返回None
        """
        stage_table = self.load_stage_table()
        return stage_table.get("stages", {}).get(stage_id)
    
    def get_enemy_by_id(self, enemy_id: str, level: int = 0) -> Optional[Dict[str, Any]]:
        """
        根据敌人ID获取敌人数据
        
        Args:
            enemy_id: 敌人ID
            level: 敌人等级
            
        Returns:
            敌人数据，如果不存在返回None
        """
        enemy_db = self.load_enemy_database()
        enemies = enemy_db.get("enemies", [])
        
        for enemy in enemies:
            if enemy.get("Key") == enemy_id:
                enemy_levels = enemy.get("Value", [])
                for enemy_level in enemy_levels:
                    if enemy_level.get("level") == level:
                        return enemy_level
        return None
    
    def get_skill_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        根据技能ID获取技能数据
        
        Args:
            skill_id: 技能ID
            
        Returns:
            技能数据，如果不存在返回None
        """
        skill_table = self.load_skill_table()
        return skill_table.get(skill_id)
    
    def list_available_stages(self) -> List[str]:
        """
        获取所有可用的关卡列表
        
        Returns:
            关卡ID列表
        """
        stage_table = self.load_stage_table()
        return list(stage_table.get("stages", {}).keys())
    
    def list_available_characters(self) -> List[str]:
        """
        获取所有可用的角色列表
        
        Returns:
            角色ID列表
        """
        character_table = self.load_character_table()
        return list(character_table.keys())


if __name__ == "__main__":
    # 测试数据加载器
    loader = DataLoader()
    
    print("测试数据加载器...")
    
    # 测试加载角色数据
    stages = loader.list_available_stages()
    print(f"找到 {len(stages)} 个关卡")
    
    characters = loader.list_available_characters()
    print(f"找到 {len(characters)} 个角色")
    
    # 测试加载特定关卡
    stage_data = loader.get_stage_by_id("main_00-01")
    if stage_data:
        print(f"成功加载关卡: {stage_data.get('name', 'Unknown')}")
    
    print("数据加载器测试完成！")
