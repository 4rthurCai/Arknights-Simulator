#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import numpy as np
from skill_system import Skill, SkillManager
from operation_result import OperationResult


class Direction(Enum):
    """方向枚举"""
    RIGHT = 0
    DOWN = 1
    LEFT = 2
    UP = 3


class Position:
    """位置类"""
    
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
    
    def __str__(self):
        return f"({self.row}, {self.col})"
    
    def __eq__(self, other):
        if isinstance(other, Position):
            return self.row == other.row and self.col == other.col
        return False
    
    def __hash__(self):
        return hash((self.row, self.col))
    
    def distance_to(self, other: 'Position') -> float:
        """计算到另一位置的距离"""
        return ((self.row - other.row) ** 2 + (self.col - other.col) ** 2) ** 0.5


class GameEntity:
    """游戏实体基类"""
    
    def __init__(self, entity_id: str, name: str = ""):
        self.entity_id = entity_id
        self.name = name
        self.position: Optional[Position] = None
        self.max_hp = 0
        self.current_hp = 0
        self.atk = 0
        self.def_ = 0  # def是Python关键字，使用def_
        self.magic_resistance = 0.0
        self.move_speed = 1.0
        self.attack_speed = 1.0
        self.base_attack_time = 1.0
        self.block_count = 0
        self.is_alive = True
        
        # 状态效果
        self.buffs: List['Buff'] = []
        self.debuffs: List['Buff'] = []
    
    def take_damage(self, damage: int, is_arts: bool = False) -> int:
        """
        受到伤害
        
        Args:
            damage: 伤害值
            is_arts: 是否为法术伤害
            
        Returns:
            实际受到的伤害
        """
        if is_arts:
            # 法术伤害
            actual_damage = max(1, int(damage * (1 - self.magic_resistance)))
        else:
            # 物理伤害
            actual_damage = max(1, damage - self.def_)
        
        self.current_hp = max(0, self.current_hp - actual_damage)
        
        if self.current_hp <= 0:
            self.is_alive = False
        
        return actual_damage
    
    def heal(self, heal_amount: int) -> int:
        """
        治疗
        
        Args:
            heal_amount: 治疗量
            
        Returns:
            实际治疗量
        """
        old_hp = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + heal_amount)
        return self.current_hp - old_hp
    
    def apply_buff(self, buff: 'Buff'):
        """应用增益效果"""
        self.buffs.append(buff)
        buff.apply(self)
    
    def apply_debuff(self, debuff: 'Buff'):
        """应用减益效果"""
        self.debuffs.append(debuff)
        debuff.apply(self)
    
    def update_buffs(self, delta_time: float):
        """更新buff效果"""
        # 更新增益效果
        active_buffs = []
        for buff in self.buffs:
            buff.update(delta_time)
            if buff.is_active:
                active_buffs.append(buff)
            else:
                buff.remove(self)
        self.buffs = active_buffs
        
        # 更新减益效果
        active_debuffs = []
        for debuff in self.debuffs:
            debuff.update(delta_time)
            if debuff.is_active:
                active_debuffs.append(debuff)
            else:
                debuff.remove(self)
        self.debuffs = active_debuffs


class Operator(GameEntity):
    """干员类"""
    
    def __init__(self, operator_id: str, operator_data: Dict[str, Any]):
        super().__init__(operator_id, operator_data.get("name", ""))
        
        self.profession = operator_data.get("profession", "PIONEER")
        self.rarity = operator_data.get("rarity", "TIER_1")
        self.position = operator_data.get("position", "MELEE")  # MELEE or RANGED
        
        # 当前等级和精英化
        self.level = 1
        self.elite = 0
        self.potential = 0
        
        # 技能相关
        self.skills: List[Skill] = []
        self.active_skill_index = 0
        self.skill_manager: Optional[SkillManager] = None
        
        # 攻击相关
        self.attack_range: List[List[int]] = []
        self.direction = Direction.RIGHT
        self.target: Optional['Enemy'] = None
        self.attack_cooldown = 0.0
        
        # 部署相关
        self.deploy_cost = 0
        self.is_deployed = False
        self.deploy_time = 0.0
        
        # 阻挡相关
        self.blocked_enemies: List['Enemy'] = []
        self.max_block_count = 1
    
    def set_level_and_elite(self, level: int, elite: int, operator_data: Dict[str, Any]):
        """
        设置干员等级和精英化
        
        Args:
            level: 等级
            elite: 精英化等级 (0, 1, 2)
            operator_data: 干员完整数据
        """
        self.level = level
        self.elite = elite
        
        # 获取对应精英化阶段的数据
        phases = operator_data.get("phases", [])
        if elite < len(phases):
            phase_data = phases[elite]
            
            # 获取等级对应的属性
            key_frames = phase_data.get("attributesKeyFrames", [])
            for i, key_frame in enumerate(key_frames):
                if key_frame.get("level") == level or i == len(key_frames) - 1:
                    attributes = key_frame.get("data", {})
                    self.max_hp = attributes.get("maxHp", 100)
                    self.current_hp = self.max_hp
                    self.atk = attributes.get("atk", 0)
                    self.def_ = attributes.get("def", 0)
                    self.magic_resistance = attributes.get("magicResistance", 0.0)
                    self.deploy_cost = attributes.get("cost", 10)
                    self.block_count = attributes.get("blockCnt", 1)
                    self.max_block_count = self.block_count
                    self.base_attack_time = attributes.get("baseAttackTime", 1.0)
                    self.attack_speed = attributes.get("attackSpeed", 100.0)
                    break
            
            # 加载攻击范围
            range_id = phase_data.get("rangeId")
            if range_id:
                self._load_attack_range(range_id)
    
    def _load_attack_range(self, range_id: str):
        """
        加载攻击范围数据
        
        Args:
            range_id: 攻击范围ID
        """
        try:
            from data_loader import DataLoader
            data_loader = DataLoader()
            range_table = data_loader.load_range_table()
            
            if range_id in range_table:
                range_data = range_table[range_id]
                grids = range_data.get("grids", [])
                
                # 转换为相对位置列表
                self.attack_range = []
                for grid in grids:
                    row = grid.get("row", 0)
                    col = grid.get("col", 0)
                    self.attack_range.append([row, col])
                
                print(f"[DEBUG] 加载攻击范围 {self.name}: {range_id} -> {len(self.attack_range)}个格子")
            else:
                print(f"[WARNING] 找不到攻击范围ID: {range_id}")
                self.attack_range = [[0, 0]]  # 默认只能攻击自身位置
        except Exception as e:
            print(f"[ERROR] 加载攻击范围失败: {e}")
            self.attack_range = [[0, 0]]
    
    def initialize_skills(self, operator_data: Dict[str, Any], skill_manager: SkillManager, skill_levels: List[int] = None):
        """
        初始化干员技能
        
        Args:
            operator_data: 干员完整数据
            skill_manager: 技能管理器
            skill_levels: 技能等级列表，默认为[7, 7, 7]
        """
        self.skill_manager = skill_manager
        
        if skill_levels is None:
            skill_levels = [7, 7, 7]  # 默认技能等级
        
        skills_data = operator_data.get("skills", [])
        
        for i, skill_data in enumerate(skills_data):
            skill_id = skill_data.get("skillId")
            if skill_id:
                skill_level = skill_levels[i] if i < len(skill_levels) else 7
                skill = skill_manager.create_skill(skill_id, skill_level - 1)  # 技能等级从0开始
                if skill:
                    self.skills.append(skill)
                    print(f"[DEBUG] {self.name}成功加载技能: {skill_id}, 等级{skill_level}, 技能数={len(self.skills)}")
                else:
                    print(f"[DEBUG] {self.name}技能加载失败: {skill_id}")
    
    def add_skill(self, skill: Skill):
        """添加技能"""
        self.skills.append(skill)
    
    def can_attack(self, target_pos: Position) -> bool:
        """
        检查是否能攻击指定位置
        
        Args:
            target_pos: 目标位置
            
        Returns:
            是否能攻击
        """
        if not self.position or not self.is_deployed:
            return False
        
        # 计算相对位置
        rel_row = target_pos.row - self.position.row
        rel_col = target_pos.col - self.position.col
        
        # 根据朝向调整攻击范围
        rotated_range = self.get_rotated_attack_range()
        
        # 检查目标是否在攻击范围内
        for range_row in rotated_range:
            for range_col in range_row:
                if rel_row == range_col[0] and rel_col == range_col[1]:
                    return True
        return False
    
    def get_rotated_attack_range(self) -> List[List[Tuple[int, int]]]:
        """
        根据朝向获取旋转后的攻击范围
        
        Returns:
            旋转后的攻击范围坐标列表
        """
        # 这里需要根据实际的攻击范围数据和朝向计算
        # 暂时返回简单的攻击范围
        if self.position == "MELEE":
            # 近战单位攻击相邻格子
            return [[(0, 1), (0, -1), (1, 0), (-1, 0)]]
        else:
            # 远程单位攻击前方几格
            return [[(i, 0) for i in range(1, 4)]]
    
    def deploy(self, position: Position, direction: Direction):
        """
        部署干员
        
        Args:
            position: 部署位置
            direction: 朝向
        """
        self.position = position
        self.direction = direction
        self.is_deployed = True
        self.deploy_time = 0.0
    
    def retreat(self):
        """撤退干员"""
        self.is_deployed = False
        self.position = None
        self.target = None
        self.blocked_enemies.clear()
        self.current_sp = 0
    
    def update(self, delta_time: float):
        """更新干员状态"""
        if not self.is_deployed:
            return
        
        # 更新buff效果
        self.update_buffs(delta_time)
        
        # 更新技能系统
        self.update_skills(delta_time)
        
        # 更新攻击冷却
        if self.attack_cooldown > 0:
            self.attack_cooldown -= delta_time
        
        # 更新部署时间
        self.deploy_time += delta_time
    
    def update_skills(self, delta_time: float):
        """更新技能状态"""
        for skill in self.skills:
            # 更新SP
            skill.update_sp(delta_time)
            
            # # 调试：显示技能SP状态（只对芬显示）
            # if self.name == "芬" and skill.levels:
            #     level = skill.get_current_level()
            #     print(f"[DEBUG] 芬技能SP: {skill.current_sp:.1f}/{level.sp_cost} (自动技能: {level.skill_type == 'AUTO'})")
            
            # 更新技能持续时间
            skill.update_duration(delta_time)
            
            # 检查自动技能
            if skill.should_auto_activate():
                print(f"[DEBUG] {self.name}自动激活技能: {skill.get_current_level().name} (SP: {skill.current_sp}/{skill.get_current_level().sp_cost})")
                self.activate_skill_by_index(self.skills.index(skill))
    
    def activate_skill(self, skill_index: int = None) -> OperationResult:
        """
        激活技能
        
        Args:
            skill_index: 技能索引，None则使用当前激活的技能
        
        Returns:
            操作结果
        """
        if skill_index is None:
            skill_index = self.active_skill_index
        
        return self.activate_skill_by_index(skill_index)
    
    def activate_skill_by_index(self, skill_index: int) -> OperationResult:
        """
        按索引激活技能
        
        Args:
            skill_index: 技能索引
        
        Returns:
            操作结果
        """
        if not self.skills:
            return OperationResult.failure_result("干员没有技能")
        
        if skill_index >= len(self.skills):
            return OperationResult.failure_result(f"技能索引超出范围: {skill_index} >= {len(self.skills)}")
        
        skill = self.skills[skill_index]
        if skill.can_activate():
            if skill.activate():
                skill_name = skill.get_current_level().name if skill.levels else f"技能{skill_index + 1}"
                return OperationResult.success_result()
            else:
                return OperationResult.failure_result("技能激活失败")
        else:
            current_sp = skill.current_sp
            required_sp = skill.get_current_level().sp_cost
            return OperationResult.failure_result(f"SP不足: {current_sp}/{required_sp}")
    
    def can_activate_skill(self, skill_index: int = None) -> bool:
        """检查是否可以激活技能"""
        if skill_index is None:
            skill_index = self.active_skill_index
        
        if not self.skills or skill_index >= len(self.skills):
            return False
        
        return self.skills[skill_index].can_activate()
    
    def gain_sp_on_attack(self):
        """攻击时获得SP"""
        for skill in self.skills:
            skill.gain_sp_on_attack()
    
    def gain_sp_on_damage(self):
        """受伤时获得SP"""
        for skill in self.skills:
            skill.gain_sp_on_damage()
    
    def get_skill_attack_multiplier(self) -> float:
        """获取技能攻击力倍率"""
        multiplier = 1.0
        for skill in self.skills:
            if skill.is_active:
                multiplier *= skill.get_attack_multiplier()
        return multiplier


class Enemy(GameEntity):
    """敌人类"""
    
    _next_id = 1  # 类变量，用于生成唯一ID
    
    def __init__(self, enemy_id: str, enemy_data: Dict[str, Any]):
        super().__init__(enemy_id)
        
        # 为每个敌人分配唯一ID
        self.unique_id = Enemy._next_id
        Enemy._next_id += 1
        
        self.enemy_data = enemy_data.get("enemyData", {})
        self.name = self.enemy_data.get("name", {}).get("m_value", "Unknown Enemy")
        
        # 从敌人数据中获取属性
        attributes = self.enemy_data.get("attributes", {})
        self.max_hp = attributes.get("maxHp", {}).get("m_value", 100)
        self.current_hp = self.max_hp
        self.atk = attributes.get("atk", {}).get("m_value", 0)
        self.def_ = attributes.get("def", {}).get("m_value", 0)
        self.magic_resistance = attributes.get("magicResistance", {}).get("m_value", 0.0)
        self.move_speed = attributes.get("moveSpeed", {}).get("m_value", 1.0)
        self.attack_speed = attributes.get("attackSpeed", {}).get("m_value", 1.0)
        self.base_attack_time = attributes.get("baseAttackTime", {}).get("m_value", 1.0)
        
        # 移动相关
        self.path: List[Position] = []
        self.path_index = 0
        self.move_progress = 0.0
        
        # 阻挡相关
        self.is_blocked = False
        self.blocked_by: Optional[Operator] = None
        
        # 攻击相关
        self.target: Optional[Operator] = None
        self.attack_cooldown = 0.0
        
        # 状态
        self.has_reached_goal = False
    
    def set_path(self, path: List[Position]):
        """设置移动路径"""
        self.path = path.copy()
        self.path_index = 0
        self.move_progress = 0.0
        if path:
            self.position = path[0]
    
    def move(self, delta_time: float) -> bool:
        """
        移动敌人
        
        Args:
            delta_time: 时间增量
            
        Returns:
            是否到达终点
        """
        if self.is_blocked or not self.path or self.path_index >= len(self.path) - 1:
            return False
        
        # 计算移动距离
        move_distance = self.move_speed * delta_time
        self.move_progress += move_distance
        
        # 检查是否到达下一个位置
        while self.move_progress >= 1.0 and self.path_index < len(self.path) - 1:
            self.move_progress -= 1.0
            self.path_index += 1
            self.position = self.path[self.path_index]
            
            # 检查是否到达终点
            if self.path_index == len(self.path) - 1:
                self.has_reached_goal = True
                return True
        
        return False
    
    def get_blocked_by(self, operator: Operator):
        """被干员阻挡"""
        self.is_blocked = True
        self.blocked_by = operator
        self.target = operator
    
    def release_block(self):
        """解除阻挡"""
        self.is_blocked = False
        self.blocked_by = None
        self.target = None
    
    def update(self, delta_time: float):
        """更新敌人状态"""
        # 更新buff效果
        self.update_buffs(delta_time)
        
        # 更新攻击冷却
        if self.attack_cooldown > 0:
            self.attack_cooldown -= delta_time
        
        # 如果没有被阻挡，尝试移动
        if not self.is_blocked:
            self.move(delta_time)


class Buff:
    """增益/减益效果类"""
    
    def __init__(self, buff_id: str, duration: float, effect_data: Dict[str, Any]):
        self.buff_id = buff_id
        self.duration = duration
        self.remaining_duration = duration
        self.effect_data = effect_data
        self.is_active = True
    
    def apply(self, target: GameEntity):
        """应用效果到目标"""
        # 根据effect_data应用具体效果
        pass
    
    def remove(self, target: GameEntity):
        """从目标移除效果"""
        # 移除之前应用的效果
        pass
    
    def update(self, delta_time: float):
        """更新buff状态"""
        if self.is_active and self.duration > 0:
            self.remaining_duration -= delta_time
            if self.remaining_duration <= 0:
                self.is_active = False
