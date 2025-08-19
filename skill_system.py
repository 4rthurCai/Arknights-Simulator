#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技能系统实现
处理干员技能的SP积累、触发条件、效果计算等
"""

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import copy


class SPType(Enum):
    """SP恢复类型"""
    INCREASE_WITH_TIME = "INCREASE_WITH_TIME"      # 自动恢复
    INCREASE_WHEN_ATTACK = "INCREASE_WHEN_ATTACK"  # 攻击回复
    INCREASE_WHEN_TAKEN_DAMAGE = "INCREASE_WHEN_TAKEN_DAMAGE"  # 受击回复


class SkillType(Enum):
    """技能触发类型"""
    MANUAL = "MANUAL"    # 手动触发
    AUTO = "AUTO"        # 自动触发
    PASSIVE = "PASSIVE"  # 被动技能


class DurationType(Enum):
    """技能持续类型"""
    NONE = "NONE"        # 瞬发技能
    SECONDS = "SECONDS"  # 持续时间（秒）
    AMMO = "AMMO"        # 弹药数


class SkillEffect:
    """技能效果"""
    
    def __init__(self, blackboard_data: List[Dict[str, Any]]):
        """
        初始化技能效果
        
        Args:
            blackboard_data: 技能黑板数据
        """
        self.effects = {}
        for item in blackboard_data:
            key = item.get("key", "")
            value = item.get("value", 0.0)
            self.effects[key] = value
    
    def get_effect(self, key: str, default: float = 0.0) -> float:
        """获取技能效果值"""
        return self.effects.get(key, default)
    
    def has_effect(self, key: str) -> bool:
        """检查是否有指定效果"""
        return key in self.effects


class SkillLevel:
    """技能等级数据"""
    
    def __init__(self, level_data: Dict[str, Any]):
        """
        初始化技能等级数据
        
        Args:
            level_data: 技能等级JSON数据
        """
        self.name = level_data.get("name", "")
        self.description = level_data.get("description", "")
        self.skill_type = SkillType(level_data.get("skillType", "MANUAL"))
        self.duration_type = DurationType(level_data.get("durationType", "NONE"))
        self.duration = level_data.get("duration", 0.0)
        self.range_id = level_data.get("rangeId")
        
        # SP数据
        sp_data = level_data.get("spData", {})
        self.sp_type = SPType(sp_data.get("spType", "INCREASE_WITH_TIME"))
        self.sp_cost = sp_data.get("spCost", 0)
        self.init_sp = sp_data.get("initSp", 0)
        self.max_charge_time = sp_data.get("maxChargeTime", 1)
        self.increment = sp_data.get("increment", 1.0)
        
        # 技能效果
        blackboard = level_data.get("blackboard", [])
        self.effects = SkillEffect(blackboard)


class Skill:
    """干员技能"""
    
    def __init__(self, skill_id: str, skill_data: Dict[str, Any], skill_level: int = 0):
        """
        初始化技能
        
        Args:
            skill_id: 技能ID
            skill_data: 技能JSON数据
            skill_level: 技能等级 (0-9, 对应level 1-10)
        """
        self.skill_id = skill_id
        self.levels = []
        
        # 解析所有等级数据
        for level_data in skill_data.get("levels", []):
            self.levels.append(SkillLevel(level_data))
        
        # 当前技能等级
        self.current_level = min(skill_level, len(self.levels) - 1) if self.levels else 0
        
        # 技能状态
        self.current_sp = 0
        self.charge_count = 0  # 当前充能数
        self.is_active = False
        self.remaining_duration = 0.0
        self.remaining_ammo = 0
        
        # 初始化SP
        if self.levels:
            self.current_sp = self.get_current_level().init_sp
            self.max_charge_count = self.get_current_level().max_charge_time
            self.charge_count = 0
    
    def get_current_level(self) -> SkillLevel:
        """获取当前等级的技能数据"""
        if not self.levels:
            raise ValueError(f"技能 {self.skill_id} 没有等级数据")
        return self.levels[self.current_level]
    
    def can_activate(self) -> bool:
        """检查是否可以激活技能"""
        level = self.get_current_level()
        
        # 被动技能不能手动激活
        if level.skill_type == SkillType.PASSIVE:
            return False
        
        # 检查充能
        if level.max_charge_time > 1:
            return self.charge_count > 0
        else:
            return self.current_sp >= level.sp_cost
    
    def should_auto_activate(self) -> bool:
        """检查是否应该自动激活"""
        level = self.get_current_level()
        
        if level.skill_type != SkillType.AUTO:
            return False
        
        # 自动技能在SP满时自动触发
        if level.max_charge_time > 1:
            return self.charge_count >= level.max_charge_time
        else:
            return self.current_sp >= level.sp_cost
    
    def activate(self) -> bool:
        """
        激活技能
        
        Returns:
            是否成功激活
        """
        if not self.can_activate() and not self.should_auto_activate():
            return False
        
        level = self.get_current_level()
        
        # 消耗SP或充能
        if level.max_charge_time > 1:
            self.charge_count -= 1
        else:
            self.current_sp = 0
        
        # 设置技能状态
        self.is_active = True
        
        if level.duration_type == DurationType.SECONDS:
            self.remaining_duration = level.duration
        elif level.duration_type == DurationType.AMMO:
            self.remaining_ammo = int(level.effects.get_effect("times", level.duration))
        
        return True
    
    def update_sp(self, delta_time: float, sp_gain_rate: float = 1.0):
        """
        更新SP
        
        Args:
            delta_time: 时间增量
            sp_gain_rate: SP获得倍率
        """
        if not self.levels:
            return
        
        level = self.get_current_level()
        
        # 只有自动恢复SP类型才会随时间增加
        if level.sp_type == SPType.INCREASE_WITH_TIME:
            sp_gain = level.increment * delta_time * sp_gain_rate
            
            if level.max_charge_time > 1:
                # 充能类技能
                self.current_sp += sp_gain
                while self.current_sp >= level.sp_cost and self.charge_count < level.max_charge_time:
                    self.current_sp -= level.sp_cost
                    self.charge_count += 1
            else:
                # 普通技能
                self.current_sp = min(self.current_sp + sp_gain, level.sp_cost)
    
    def gain_sp_on_attack(self, sp_gain: float = 1.0):
        """攻击时获得SP"""
        if not self.levels:
            return
        
        level = self.get_current_level()
        if level.sp_type == SPType.INCREASE_WHEN_ATTACK:
            self._gain_sp(sp_gain * level.increment)
    
    def gain_sp_on_damage(self, sp_gain: float = 1.0):
        """受击时获得SP"""
        if not self.levels:
            return
        
        level = self.get_current_level()
        if level.sp_type == SPType.INCREASE_WHEN_TAKEN_DAMAGE:
            self._gain_sp(sp_gain * level.increment)
    
    def _gain_sp(self, sp_amount: float):
        """内部SP获得方法"""
        level = self.get_current_level()
        
        if level.max_charge_time > 1:
            # 充能类技能
            self.current_sp += sp_amount
            while self.current_sp >= level.sp_cost and self.charge_count < level.max_charge_time:
                self.current_sp -= level.sp_cost
                self.charge_count += 1
        else:
            # 普通技能
            self.current_sp = min(self.current_sp + sp_amount, level.sp_cost)
    
    def update_duration(self, delta_time: float):
        """
        更新技能持续时间
        
        Args:
            delta_time: 时间增量
        """
        if not self.is_active:
            return
        
        level = self.get_current_level()
        
        if level.duration_type == DurationType.SECONDS:
            self.remaining_duration -= delta_time
            if self.remaining_duration <= 0:
                self.deactivate()
        elif level.duration_type == DurationType.NONE:
            # 瞬发技能立即结束
            self.deactivate()
    
    def consume_ammo(self) -> bool:
        """
        消耗弹药
        
        Returns:
            是否还有弹药剩余
        """
        level = self.get_current_level()
        
        if level.duration_type == DurationType.AMMO and self.is_active:
            self.remaining_ammo -= 1
            if self.remaining_ammo <= 0:
                self.deactivate()
                return False
        
        return True
    
    def deactivate(self):
        """停用技能"""
        self.is_active = False
        self.remaining_duration = 0.0
        self.remaining_ammo = 0
    
    def get_skill_modifier(self, attribute: str) -> float:
        """
        获取技能对属性的修正值
        
        Args:
            attribute: 属性名称
            
        Returns:
            修正值
        """
        if not self.is_active or not self.levels:
            return 0.0
        
        level = self.get_current_level()
        return level.effects.get_effect(attribute, 0.0)
    
    def get_attack_multiplier(self) -> float:
        """获取攻击力倍率"""
        if not self.is_active:
            return 1.0
        
        # 常见的攻击力倍率效果键名
        multiplier_keys = ["atk_scale", "attack_scale", "atk", "attack_power"]
        
        for key in multiplier_keys:
            modifier = self.get_skill_modifier(key)
            if modifier > 0:
                return modifier
        
        return 1.0
    
    def has_effect(self, effect_name: str) -> bool:
        """检查是否有指定效果"""
        if not self.is_active or not self.levels:
            return False
        
        level = self.get_current_level()
        return level.effects.has_effect(effect_name)


class SkillManager:
    """技能管理器"""
    
    def __init__(self, data_loader):
        """
        初始化技能管理器
        
        Args:
            data_loader: 数据加载器
        """
        self.data_loader = data_loader
        self.skill_table = None
    
    def load_skill_table(self):
        """加载技能表"""
        if self.skill_table is None:
            self.skill_table = self.data_loader.load_skill_table()
    
    def create_skill(self, skill_id: str, skill_level: int = 0) -> Optional[Skill]:
        """
        创建技能实例
        
        Args:
            skill_id: 技能ID
            skill_level: 技能等级
            
        Returns:
            技能实例
        """
        self.load_skill_table()
        
        if skill_id not in self.skill_table:
            return None
        
        skill_data = self.skill_table[skill_id]
        return Skill(skill_id, skill_data, skill_level)
    
    def get_skill_info(self, skill_id: str, skill_level: int = 0) -> Optional[Dict[str, Any]]:
        """
        获取技能信息
        
        Args:
            skill_id: 技能ID
            skill_level: 技能等级
            
        Returns:
            技能信息字典
        """
        skill = self.create_skill(skill_id, skill_level)
        if not skill:
            return None
        
        level = skill.get_current_level()
        return {
            "skill_id": skill_id,
            "name": level.name,
            "description": level.description,
            "skill_type": level.skill_type.value,
            "sp_type": level.sp_type.value,
            "sp_cost": level.sp_cost,
            "init_sp": level.init_sp,
            "max_charge": level.max_charge_time,
            "duration": level.duration,
            "duration_type": level.duration_type.value,
            "effects": level.effects.effects
        }
