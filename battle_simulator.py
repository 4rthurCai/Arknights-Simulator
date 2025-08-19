#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
战斗模拟器
负责执行用户指定的作战方案并模拟战斗过程
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum

from data_loader import DataLoader
from game_entities import Operator, Direction, Position, Skill
from game_map import GameMap
from skill_system import SkillManager


class ActionType(Enum):
    """操作类型"""
    DEPLOY = "DEPLOY"           # 部署干员
    RETREAT = "RETREAT"         # 撤退干员
    ACTIVATE_SKILL = "ACTIVATE_SKILL"  # 激活技能
    PAUSE = "PAUSE"            # 暂停
    SPEED_UP = "SPEED_UP"      # 加速
    END = "END"                # 结束


class BattleAction:
    """战斗操作类"""
    
    def __init__(self, action_data: Dict[str, Any]):
        self.action_type = ActionType(action_data.get("type", "DEPLOY"))
        self.time = action_data.get("time", 0.0)  # 执行时间
        self.operator_id = action_data.get("operator_id", "")
        
        # 部署相关参数
        self.position = None
        if "position" in action_data:
            pos_data = action_data["position"]
            self.position = Position(pos_data["row"], pos_data["col"])
        
        self.direction = Direction.RIGHT
        if "direction" in action_data:
            direction_map = {
                "RIGHT": Direction.RIGHT,
                "DOWN": Direction.DOWN,
                "LEFT": Direction.LEFT,
                "UP": Direction.UP
            }
            self.direction = direction_map.get(action_data["direction"], Direction.RIGHT)
        
        # 技能相关参数
        self.skill_index = action_data.get("skill_index", 0)
        
        # 操作状态
        self.is_executed = False


class BattlePlan:
    """作战方案类"""
    
    def __init__(self, plan_data: Dict[str, Any]):
        self.stage_id = plan_data.get("stage_id", "")
        self.operators = plan_data.get("operators", [])
        self.actions: List[BattleAction] = []
        
        # 解析操作列表
        for action_data in plan_data.get("actions", []):
            self.actions.append(BattleAction(action_data))
        
        # 按时间排序
        self.actions.sort(key=lambda x: x.time)


class BattleSimulator:
    """战斗模拟器"""
    
    def __init__(self, data_loader: DataLoader):
        self.data_loader = data_loader
        self.skill_manager = SkillManager(data_loader)
        self.game_map: Optional[GameMap] = None
        self.operators: Dict[str, Operator] = {}
        self.battle_plan: Optional[BattlePlan] = None
        self.action_index = 0
        
        # 模拟参数
        self.time_step = 0.1  # 每次更新的时间步长（秒）
        self.max_simulation_time = 60.0  # 最大模拟时间（1分钟）
        
        # 战斗结果
        self.result = {
            "success": False,
            "reason": "",
            "final_life_points": 0,
            "battle_time": 0.0,
            "operators_deployed": [],
            "enemies_defeated": 0,
            "detailed_log": []
        }
    
    def load_battle_plan(self, plan_file_path: str) -> bool:
        """
        加载作战方案
        
        Args:
            plan_file_path: 作战方案文件路径
            
        Returns:
            是否成功加载
        """
        try:
            with open(plan_file_path, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)
            
            self.battle_plan = BattlePlan(plan_data)
            self.plan_data = plan_data  # 保存原始数据以便后续使用
            return True
        except Exception as e:
            print(f"加载作战方案失败: {e}")
            return False
    
    def setup_stage(self, stage_id: str) -> bool:
        """
        设置关卡
        
        Args:
            stage_id: 关卡ID
            
        Returns:
            是否成功设置
        """
        try:
            # 获取关卡数据
            stage_data = self.data_loader.get_stage_by_id(stage_id)
            if not stage_data:
                print(f"关卡不存在: {stage_id}")
                return False
            
            # 获取关卡地图数据
            level_id = stage_data.get("levelId", "")
            level_data = self.data_loader.load_level_data(level_id)
            
            # 创建游戏地图
            self.game_map = GameMap(level_data, self.data_loader)
            
            # 设置初始生命点数（如果作战方案中有指定）
            if hasattr(self, 'plan_data') and 'initial_life_points' in self.plan_data:
                initial_life_points = self.plan_data['initial_life_points']
                self.game_map.current_life_points = initial_life_points
                self.game_map.initial_life_points = initial_life_points
            
            return True
        except Exception as e:
            print(f"设置关卡失败: {e}")
            return False
    
    def setup_operators(self, operator_configs: List[Dict[str, Any]]) -> bool:
        """
        设置干员
        
        Args:
            operator_configs: 干员配置列表
            
        Returns:
            是否成功设置
        """
        try:
            self.operators.clear()
            
            for config in operator_configs:
                operator_id = config.get("operator_id", "")
                custom_id = config.get("custom_id", operator_id)
                level = config.get("level", 1)
                elite = config.get("elite", 0)
                potential = config.get("potential", 0)
                skill_level = config.get("skill_level", 1)
                
                # 获取干员数据
                operator_data = self.data_loader.get_character_by_id(operator_id)
                if not operator_data:
                    print(f"干员不存在: {operator_id}")
                    continue
                
                # 创建干员对象
                operator = Operator(operator_id, operator_data)
                operator.set_level_and_elite(level, elite, operator_data)
                operator.potential = potential
                
                # 加载技能
                self._setup_operator_skills(operator, operator_data, skill_level)
                
                self.operators[custom_id] = operator
            
            return True
        except Exception as e:
            print(f"设置干员失败: {e}")
            return False
    
    def _setup_operator_skills(self, operator: Operator, operator_data: Dict[str, Any], skill_level: int):
        """
        设置干员技能
        
        Args:
            operator: 干员对象
            operator_data: 干员数据
            skill_level: 技能等级
        """
        # 使用新的技能系统初始化技能
        skill_levels = [skill_level] * 3  # 假设所有技能同等级
        operator.initialize_skills(operator_data, self.skill_manager, skill_levels)
    
    def run_simulation(self, battle_plan_file: str) -> Dict[str, Any]:
        """
        运行战斗模拟
        
        Args:
            battle_plan_file: 作战方案文件路径
            
        Returns:
            模拟结果
        """
        # 重置结果
        self.result = {
            "success": False,
            "reason": "",
            "final_life_points": 0,
            "battle_time": 0.0,
            "operators_deployed": [],
            "enemies_defeated": 0,
            "detailed_log": []
        }
        
        try:
            # 加载作战方案
            if not self.load_battle_plan(battle_plan_file):
                self.result["reason"] = "无法加载作战方案"
                return self.result
            
            # 设置关卡
            if not self.setup_stage(self.battle_plan.stage_id):
                self.result["reason"] = f"无法设置关卡: {self.battle_plan.stage_id}"
                return self.result
            
            # 设置干员
            if not self.setup_operators(self.battle_plan.operators):
                self.result["reason"] = "无法设置干员"
                return self.result
            
            # 开始模拟
            self.action_index = 0
            current_time = 0.0
            
            self._log("战斗开始", current_time)
            
            while current_time < self.max_simulation_time:
                # 执行当前时间点的操作
                self._execute_actions_at_time(current_time)
                
                # 更新游戏状态
                self.game_map.update(self.time_step)
                current_time += self.time_step
                
                # 检查胜利条件
                if self.game_map.is_victory:
                    self.result["success"] = True
                    self.result["reason"] = "胜利！"
                    break
                
                # 检查失败条件
                if self.game_map.is_defeat:
                    self.result["success"] = False
                    self.result["reason"] = "失败！生命点数耗尽"
                    break
                
                # 每10秒输出一次状态信息用于调试
                if int(current_time) % 10 == 0 and current_time > 0:
                    active_enemy_count = len(self.game_map.active_enemies)
                    current_wave = self.game_map.current_wave_index
                    total_waves = len(self.game_map.waves)
                    life_points = self.game_map.current_life_points
                    
                    # 检查是否所有波次都完成
                    all_waves_completed = current_wave >= total_waves
                    
                    # 检查是否还有未完成的动作
                    pending_actions = 0
                    if current_wave < total_waves:
                        wave = self.game_map.waves[current_wave]
                        for fragment in wave.fragments:
                            if not fragment.is_completed:
                                for action in fragment.actions:
                                    if not action.is_completed:
                                        pending_actions += 1
                    
                    # 添加干员详细状态信息（包括所有干员，不仅仅是已部署的）
                    operator_status = []
                    for operator_id, operator in self.operators.items():
                        status = f"{operator.name}(hp:{operator.current_hp}/{operator.max_hp},pos:{operator.position},alive:{operator.is_alive},deployed:{operator.is_deployed},blocked_count:{len(operator.blocked_enemies) if hasattr(operator, 'blocked_enemies') else 0})"
                        operator_status.append(status)
                    
                    # 添加已部署干员状态
                    deployed_status = []
                    for operator in self.game_map.deployed_operators:
                        status = f"{operator.name}(hp:{operator.current_hp}/{operator.max_hp},pos:{operator.position},alive:{operator.is_alive})"
                        deployed_status.append(status)
                    
                    # 添加敌人详细状态信息
                    enemy_status = []
                    for enemy in self.game_map.active_enemies:
                        blocked_by = enemy.blocked_by.name if hasattr(enemy, 'blocked_by') and enemy.blocked_by else "None"
                        status = f"{enemy.name}(hp:{enemy.current_hp}/{enemy.max_hp},pos:{enemy.position},blocked:{enemy.is_blocked},blocked_by:{blocked_by},alive:{enemy.is_alive},goal:{enemy.has_reached_goal})"
                        enemy_status.append(status)
                    
                    # 添加攻击调试信息（每10秒一次）
                    # attack_debug = []
                    # for operator in self.game_map.deployed_operators:
                    #     attack_debug.append(f"{operator.name}(atk:{operator.atk},cooldown:{operator.attack_cooldown:.2f})")
                    # if attack_debug:
                    #     self._log(f"干员攻击状态: {', '.join(attack_debug)}", current_time)
                        
                    # enemy_attack_debug = []
                    # for enemy in self.game_map.active_enemies[:3]:  # 只显示前3个敌人避免过多输出
                    #     enemy_attack_debug.append(f"{enemy.name}(atk:{enemy.atk},cooldown:{enemy.attack_cooldown:.2f})")
                    # if enemy_attack_debug:
                    #     self._log(f"敌人攻击状态: {', '.join(enemy_attack_debug)}", current_time)
                    
                    current_cost = int(self.game_map.current_cost)
                    self._log(f"调试: 时间={current_time:.1f}s, 活跃敌人={active_enemy_count}, 波次={current_wave}/{total_waves}, 生命点={life_points}, 部署费用={current_cost}, 待处理动作={pending_actions}", current_time)
                    if operator_status:
                        self._log(f"所有干员状态: {', '.join(operator_status)}", current_time)
                    if deployed_status:
                        self._log(f"已部署干员: {', '.join(deployed_status)}", current_time)
                    # if enemy_status:
                    #     self._log(f"敌人状态: {', '.join(enemy_status)}", current_time)
            else:
                # 达到最大模拟时间仍未结束
                if not self.result["reason"]:  # 如果还没有设置原因
                    self.result["reason"] = "达到最大模拟时间限制"
            
            # 填充结果
            self.result["final_life_points"] = self.game_map.current_life_points
            self.result["battle_time"] = current_time
            self.result["operators_deployed"] = [op.name for op in self.game_map.deployed_operators]
            
            # 计算击败的敌人数量
            total_enemies = 0
            for wave in self.game_map.waves:
                for fragment in wave.fragments:
                    for action in fragment.actions:
                        # 只计算SPAWN类型的动作
                        if action.action_type == "SPAWN":
                            total_enemies += action.count
            
            initial_life_points = getattr(self.game_map, 'initial_life_points', self.game_map.max_life_point)
            escaped_enemies = initial_life_points - self.game_map.current_life_points
            self.result["enemies_defeated"] = total_enemies - escaped_enemies
            
            self._log(f"战斗结束: {self.result['reason']}", current_time)
            
        except Exception as e:
            self.result["reason"] = f"模拟过程中发生异常: {str(e)}"
            self._log(f"异常: {str(e)}", current_time if 'current_time' in locals() else 0.0)
        
        return self.result
    
    def _execute_actions_at_time(self, current_time: float):
        """
        执行当前时间点的操作
        
        Args:
            current_time: 当前时间
        """
        while (self.action_index < len(self.battle_plan.actions) and
               self.battle_plan.actions[self.action_index].time <= current_time and
               not self.battle_plan.actions[self.action_index].is_executed):
            
            action = self.battle_plan.actions[self.action_index]
            self._execute_action(action, current_time)
            action.is_executed = True
            self.action_index += 1
    
    def _execute_action(self, action: BattleAction, current_time: float):
        """
        执行单个操作
        
        Args:
            action: 要执行的操作
            current_time: 当前时间
        """
        if action.action_type == ActionType.DEPLOY:
            self._execute_deploy(action, current_time)
        elif action.action_type == ActionType.RETREAT:
            self._execute_retreat(action, current_time)
        elif action.action_type == ActionType.ACTIVATE_SKILL:
            self._execute_activate_skill(action, current_time)
        # 其他操作类型的处理...
    
    def _execute_deploy(self, action: BattleAction, current_time: float):
        """
        执行部署操作
        
        Args:
            action: 部署操作
            current_time: 当前时间
        """
        operator = self.operators.get(action.operator_id)
        if not operator:
            self._log(f"干员不存在: {action.operator_id}", current_time)
            return
        
        if not action.position:
            self._log(f"部署位置无效: {action.operator_id}", current_time)
            return
        
        deploy_result = self.game_map.deploy_operator(operator, action.position, action.direction)
        if deploy_result.success:
            self._log(f"部署干员 {operator.name} 到 {action.position}", current_time)
        else:
            self._log(f"部署失败: {operator.name} 到 {action.position} - {deploy_result.reason}", current_time)
    
    def _execute_retreat(self, action: BattleAction, current_time: float):
        """
        执行撤退操作
        
        Args:
            action: 撤退操作
            current_time: 当前时间
        """
        operator = self.operators.get(action.operator_id)
        if not operator:
            self._log(f"干员不存在: {action.operator_id}", current_time)
            return
        
        success = self.game_map.retreat_operator(operator)
        if success:
            self._log(f"撤退干员 {operator.name}", current_time)
        else:
            self._log(f"撤退失败: {operator.name}", current_time)
    
    def _execute_activate_skill(self, action: BattleAction, current_time: float):
        """
        执行技能激活操作
        
        Args:
            action: 技能激活操作
            current_time: 当前时间
        """
        operator = self.operators.get(action.operator_id)
        if not operator:
            self._log(f"干员不存在: {action.operator_id}", current_time)
            return
        
        if not operator.is_deployed:
            self._log(f"干员未部署，无法激活技能: {operator.name}", current_time)
            return
        
        # 使用新的技能系统
        skill_index = getattr(action, 'skill_index', 0)  # 默认使用第一个技能
        skill_result = operator.activate_skill(skill_index)
        
        if skill_result.success:
            if skill_index < len(operator.skills):
                skill = operator.skills[skill_index]
                skill_name = skill.get_current_level().name if skill.levels else "未知技能"
                self._log(f"激活 {operator.name} 的技能: {skill_name}", current_time)
            else:
                self._log(f"激活 {operator.name} 的技能", current_time)
        else:
            self._log(f"技能激活失败: {operator.name} - {skill_result.reason}", current_time)
    
    def _log(self, message: str, current_time: float):
        """
        记录日志
        
        Args:
            message: 日志消息
            current_time: 当前时间
        """
        log_entry = {
            "time": round(current_time, 2),
            "message": message
        }
        self.result["detailed_log"].append(log_entry)
        print(f"[{log_entry['time']:6.2f}s] {message}")
    
    def create_example_battle_plan(self, output_file: str = "example_battle_plan.json"):
        """
        创建示例作战方案
        
        Args:
            output_file: 输出文件路径
        """
        example_plan = {
            "stage_id": "main_00-01",
            "operators": [
                {
                    "operator_id": "char_002_amiya",
                    "custom_id": "amiya_1",
                    "level": 50,
                    "elite": 1,
                    "potential": 0,
                    "skill_level": 7
                },
                {
                    "operator_id": "char_123_fang",
                    "custom_id": "fang_1", 
                    "level": 30,
                    "elite": 0,
                    "potential": 5,
                    "skill_level": 4
                }
            ],
            "actions": [
                {
                    "type": "DEPLOY",
                    "time": 2.0,
                    "operator_id": "fang_1",
                    "position": {"row": 3, "col": 2},
                    "direction": "RIGHT"
                },
                {
                    "type": "DEPLOY", 
                    "time": 5.0,
                    "operator_id": "amiya_1",
                    "position": {"row": 2, "col": 1},
                    "direction": "RIGHT"
                },
                {
                    "type": "ACTIVATE_SKILL",
                    "time": 15.0,
                    "operator_id": "amiya_1",
                    "skill_index": 0
                }
            ]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(example_plan, f, ensure_ascii=False, indent=2)
        
        print(f"示例作战方案已生成: {output_file}")


if __name__ == "__main__":
    # 测试战斗模拟器
    data_loader = DataLoader()
    simulator = BattleSimulator(data_loader)
    
    # 生成示例作战方案
    simulator.create_example_battle_plan()
    
    # 运行模拟
    result = simulator.run_simulation("example_battle_plan.json")
    
    print("\n=== 模拟结果 ===")
    print(f"成功: {result['success']}")
    print(f"原因: {result['reason']}")
    print(f"最终生命点数: {result['final_life_points']}")
    print(f"战斗时间: {result['battle_time']:.2f}秒")
    print(f"部署的干员: {result['operators_deployed']}")
    print(f"击败敌人数: {result['enemies_defeated']}")
