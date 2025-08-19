#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏地图和关卡逻辑
处理关卡地图数据、路径寻找、敌人生成等
"""

from typing import Dict, List, Any, Optional, Tuple
import json
from enum import Enum

from game_entities import Position, Enemy, Operator, Direction
from data_loader import DataLoader
from operation_result import OperationResult


class TileType(Enum):
    """地块类型"""
    FORBIDDEN = "tile_forbidden"  # 禁止通行
    ROAD = "tile_road"            # 道路
    WALL = "tile_wall"            # 高台
    GRASS = "tile_grass"          # 草地
    HOLE = "tile_hole"            # 洞
    TELIN = "tile_telin"          # 传送入口
    TELOUT = "tile_telout"        # 传送出口


class BuildableType(Enum):
    """可部署类型"""
    NONE = "NONE"           # 不可部署
    MELEE = "MELEE"         # 近战位
    RANGED = "RANGED"       # 远程位
    ALL = "ALL"             # 全部可部署


class Tile:
    """地块类"""
    
    def __init__(self, tile_data: Dict[str, Any]):
        self.tile_key = tile_data.get("tileKey", "tile_forbidden")
        self.height_type = tile_data.get("heightType", "LOWLAND")
        self.buildable_type = BuildableType(tile_data.get("buildableType", "NONE"))
        self.passable_mask = tile_data.get("passableMask", "NONE")
        self.player_side_mask = tile_data.get("playerSideMask", "ALL")
        self.blackboard = tile_data.get("blackboard", {})
        self.effects = tile_data.get("effects", [])
        
        # 状态
        self.deployed_operator: Optional[Operator] = None
        self.enemies_on_tile: List[Enemy] = []
    
    def can_deploy_operator(self, operator: Operator) -> bool:
        """
        检查是否可以部署干员
        
        Args:
            operator: 要部署的干员
            
        Returns:
            是否可以部署
        """
        if self.deployed_operator is not None:
            return False
        
        if self.buildable_type == BuildableType.NONE:
            return False
        
        if self.buildable_type == BuildableType.MELEE and operator.position != "MELEE":
            return False
            
        if self.buildable_type == BuildableType.RANGED and operator.position != "RANGED":
            return False
        
        return True
    
    def deploy_operator(self, operator: Operator) -> bool:
        """
        部署干员到此地块
        
        Args:
            operator: 要部署的干员
            
        Returns:
            是否成功部署
        """
        if not self.can_deploy_operator(operator):
            return False
        
        self.deployed_operator = operator
        return True
    
    def remove_operator(self):
        """移除部署的干员"""
        if self.deployed_operator:
            self.deployed_operator.retreat()
            self.deployed_operator = None


class Route:
    """敌人移动路径类"""
    
    def __init__(self, route_data: Dict[str, Any]):
        self.motion_mode = route_data.get("motionMode", "WALK")
        self.start_position = Position(
            route_data.get("startPosition", {}).get("row", 0),
            route_data.get("startPosition", {}).get("col", 0)
        )
        self.end_position = Position(
            route_data.get("endPosition", {}).get("row", 0),
            route_data.get("endPosition", {}).get("col", 0)
        )
        self.checkpoints = route_data.get("checkpoints", [])
        self.allow_diagonal_move = route_data.get("allowDiagonalMove", False)
        
        # 生成完整路径
        self.path: List[Position] = self._generate_path()
    
    def _generate_path(self) -> List[Position]:
        """生成从起点到终点的完整路径"""
        path = [self.start_position]
        
        # 如果有检查点，先经过所有检查点
        current_pos = self.start_position
        checkpoints = self.checkpoints or []  # 处理None的情况
        for checkpoint in checkpoints:
            # 正确解析检查点位置数据
            position_data = checkpoint.get("position", {})
            checkpoint_pos = Position(position_data.get("row", 0), position_data.get("col", 0))
            path.extend(self._find_path(current_pos, checkpoint_pos))
            current_pos = checkpoint_pos
        
        # 最后到达终点
        path.extend(self._find_path(current_pos, self.end_position))
        
        return path
    
    def _find_path(self, start: Position, end: Position) -> List[Position]:
        """
        从起点到终点寻路，支持对角移动
        
        Args:
            start: 起点
            end: 终点
            
        Returns:
            路径点列表
        """
        path = []
        
        if self.allow_diagonal_move:
            # 对角移动：直接从起点到终点，但需要生成中间经过的地块
            path.extend(self._generate_line_path(start, end))
        else:
            # 非对角移动：逐格移动
            current = Position(start.row, start.col)
            while current != end:
                next_pos = Position(current.row, current.col)
                
                # 简单的直线寻路
                if current.row < end.row:
                    next_pos.row += 1
                elif current.row > end.row:
                    next_pos.row -= 1
                elif current.col < end.col:
                    next_pos.col += 1
                elif current.col > end.col:
                    next_pos.col -= 1
                
                path.append(next_pos)
                current = next_pos
        
        return path
    
    def _generate_line_path(self, start: Position, end: Position) -> List[Position]:
        """
        生成从起点到终点的直线路径，包括经过的所有地块
        使用Bresenham算法生成直线上的所有点
        
        Args:
            start: 起点
            end: 终点
            
        Returns:
            路径点列表
        """
        path = []
        
        x0, y0 = start.col, start.row
        x1, y1 = end.col, end.row
        
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        x, y = x0, y0
        
        while True:
            # 添加当前位置到路径（除了起点）
            if x != x0 or y != y0:
                path.append(Position(y, x))
            
            # 检查是否到达终点
            if x == x1 and y == y1:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy
        
        return path


class Wave:
    """敌人波次类"""
    
    def __init__(self, wave_data: Dict[str, Any]):
        self.pre_delay = wave_data.get("preDelay", 0.0)
        self.post_delay = wave_data.get("postDelay", 0.0)
        self.max_time_waiting = wave_data.get("maxTimeWaitingForNextWave", -1.0)
        
        self.fragments = []
        for fragment_data in wave_data.get("fragments", []):
            self.fragments.append(WaveFragment(fragment_data))
        
        # 状态
        self.is_active = False
        self.is_completed = False
        self.current_time = 0.0


class WaveFragment:
    """波次片段类"""
    
    def __init__(self, fragment_data: Dict[str, Any]):
        self.pre_delay = fragment_data.get("preDelay", 0.0)
        self.actions = []
        
        for action_data in fragment_data.get("actions", []):
            self.actions.append(WaveAction(action_data))
        
        # 状态
        self.is_active = False
        self.is_completed = False
        self.current_time = 0.0


class WaveAction:
    """波次动作类"""
    
    def __init__(self, action_data: Dict[str, Any]):
        self.action_type = action_data.get("actionType", "SPAWN")
        self.enemy_key = action_data.get("key", "")
        self.count = action_data.get("count", 1)
        self.pre_delay = action_data.get("preDelay", 0.0)
        self.interval = action_data.get("interval", 1.0)
        self.route_index = action_data.get("routeIndex", 0)
        
        # 状态
        self.is_completed = False
        self.spawned_count = 0
        self.current_time = 0.0


class GameMap:
    """游戏地图类"""
    
    def __init__(self, level_data: Dict[str, Any], data_loader: DataLoader):
        self.data_loader = data_loader
        
        # 地图基础信息
        map_data = level_data.get("mapData", {})
        self.map_layout = map_data.get("map", [])
        self.rows = len(self.map_layout)
        self.cols = len(self.map_layout[0]) if self.map_layout else 0
        
        # 地块数据
        self.tiles: Dict[int, Tile] = {}
        for i, tile_data in enumerate(map_data.get("tiles", [])):
            self.tiles[i] = Tile(tile_data)
        
        # 路径数据
        self.routes: List[Route] = []
        for route_data in level_data.get("routes", []):
            self.routes.append(Route(route_data))
        
        # 敌人数据引用
        self.enemy_db_refs = level_data.get("enemyDbRefs", [])
        
        # 波次数据
        self.waves: List[Wave] = []
        for wave_data in level_data.get("waves", []):
            self.waves.append(Wave(wave_data))
        
        # 关卡选项
        options = level_data.get("options", {})
        self.character_limit = options.get("characterLimit", 8)
        self.max_life_point = options.get("maxLifePoint", 3)
        self.initial_cost = options.get("initialCost", 10)
        self.max_cost = options.get("maxCost", 99)
        self.cost_increase_time = options.get("costIncreaseTime", 1.0)
        
        # 游戏状态
        self.current_cost = self.initial_cost
        self.current_life_points = self.max_life_point
        self.initial_life_points = self.max_life_point  # 记录实际的初始生命点数
        self.deployed_operators: List[Operator] = []
        self.active_enemies: List[Enemy] = []
        self.current_wave_index = 0
        self.game_time = 0.0
        self.is_victory = False
        self.is_defeat = False
    
    def get_tile_at(self, position: Position) -> Optional[Tile]:
        """
        获取指定位置的地块
        
        Args:
            position: 位置
            
        Returns:
            地块对象，如果位置无效返回None
        """
        if not self.is_valid_position(position):
            return None
        
        # 修正行索引：JSON中的地图布局是上下颠倒的
        # 位置(row, col)应该对应map_layout[rows-1-row][col]
        corrected_row = self.rows - 1 - position.row
        tile_index = self.map_layout[corrected_row][position.col]
        return self.tiles.get(tile_index)
    
    def is_valid_position(self, position: Position) -> bool:
        """
        检查位置是否有效
        
        Args:
            position: 位置
            
        Returns:
            是否有效
        """
        return (0 <= position.row < self.rows and 
                0 <= position.col < self.cols)
    
    def can_deploy_at(self, position: Position, operator: Operator) -> bool:
        """
        检查是否可以在指定位置部署干员
        
        Args:
            position: 部署位置
            operator: 干员
            
        Returns:
            是否可以部署
        """
        tile = self.get_tile_at(position)
        if not tile:
            return False
        
        return tile.can_deploy_operator(operator)
    
    def deploy_operator(self, operator: Operator, position: Position, direction: Direction = Direction.RIGHT) -> OperationResult:
        """
        部署干员
        
        Args:
            operator: 干员
            position: 部署位置
            direction: 朝向
            
        Returns:
            操作结果
        """
        # 检查位置是否有效
        if not self.is_valid_position(position):
            return OperationResult.failure_result(f"位置无效: ({position.row}, {position.col})")
        
        # 检查地块是否可部署
        tile = self.get_tile_at(position)
        if not tile:
            return OperationResult.failure_result(f"无法获取地块信息: ({position.row}, {position.col})")
        
        if tile.deployed_operator is not None:
            return OperationResult.failure_result(f"位置已被占用: ({position.row}, {position.col})")
        
        # 检查干员类型与地块类型匹配
        if not self._check_operator_tile_compatibility(operator, tile):
            tile_type = tile.buildable_type.value
            operator_position = operator.position if hasattr(operator, 'position') else "UNKNOWN"
            return OperationResult.failure_result(f"干员类型不匹配: {operator.name}({operator_position}) 无法部署到 {tile_type} 位置")
        
        # 检查费用是否足够
        if self.current_cost < operator.deploy_cost:
            return OperationResult.failure_result(f"费用不足: 需要{operator.deploy_cost}，当前{self.current_cost}")
        
        # 检查人数限制
        if len(self.deployed_operators) >= self.character_limit:
            return OperationResult.failure_result(f"已达到人数上限: {self.character_limit}")
        
        # 执行部署
        if tile.deploy_operator(operator):
            operator.deploy(position, direction)
            self.deployed_operators.append(operator)
            self.current_cost -= operator.deploy_cost
            return OperationResult.success_result()
        else:
            return OperationResult.failure_result("地块拒绝部署")
    
    def _check_operator_tile_compatibility(self, operator: Operator, tile: 'Tile') -> bool:
        """
        检查干员与地块的兼容性
        
        Args:
            operator: 干员
            tile: 地块
            
        Returns:
            是否兼容
        """
        # 获取干员的位置类型
        operator_position = getattr(operator, 'position', 'MELEE')
        
        # 检查兼容性
        if tile.buildable_type == BuildableType.NONE:
            return False
        elif tile.buildable_type == BuildableType.ALL:
            return True
        elif tile.buildable_type == BuildableType.MELEE:
            return operator_position == 'MELEE'
        elif tile.buildable_type == BuildableType.RANGED:
            return operator_position == 'RANGED'
        
        return False
    
    def retreat_operator(self, operator: Operator) -> bool:
        """
        撤退干员
        
        Args:
            operator: 要撤退的干员
            
        Returns:
            是否成功撤退
        """
        if operator not in self.deployed_operators:
            return False
        
        # 移除部署
        if operator.position:
            tile = self.get_tile_at(operator.position)
            if tile:
                tile.remove_operator()
        
        self.deployed_operators.remove(operator)
        operator.retreat()
        return True
    
    def spawn_enemy(self, enemy_id: str, route_index: int = 0) -> Optional[Enemy]:
        """
        生成敌人
        
        Args:
            enemy_id: 敌人ID
            route_index: 路径索引
            
        Returns:
            生成的敌人对象
        """
        # 从敌人数据库获取敌人数据
        enemy_data = self.data_loader.get_enemy_by_id(enemy_id, 0)
        if not enemy_data:
            return None
        
        enemy = Enemy(enemy_id, enemy_data)
        
        # 设置移动路径
        if route_index < len(self.routes):
            route = self.routes[route_index]
            enemy.set_path(route.path)
        
        self.active_enemies.append(enemy)
        return enemy
    
    def update(self, delta_time: float):
        """
        更新游戏地图状态
        
        Args:
            delta_time: 时间增量
        """
        self.game_time += delta_time
        
        # 更新费用
        self.current_cost = min(self.max_cost, 
                              self.current_cost + delta_time / self.cost_increase_time)
        
        # 更新部署的干员
        for operator in self.deployed_operators[:]:
            operator.update(delta_time)
            
            if not operator.is_alive:
                self.retreat_operator(operator)
        
        # 更新敌人
        for enemy in self.active_enemies[:]:
            enemy.update(delta_time)
            
            # 检查敌人是否到达终点
            if enemy.has_reached_goal:
                self.current_life_points -= 1
                self.active_enemies.remove(enemy)
                
                if self.current_life_points <= 0:
                    self.is_defeat = True
            
            # 检查敌人是否死亡
            elif not enemy.is_alive:
                self.active_enemies.remove(enemy)
        
        # 处理战斗逻辑
        self._process_combat(delta_time)
        
        # 处理阻挡逻辑
        self._process_blocking()
        
        # 更新波次
        self._update_waves(delta_time)
        
        # 检查胜利条件
        # 胜利条件：所有波次完成 且 没有活跃敌人 且 生命点数大于0 且 未失败
        if (self.current_wave_index >= len(self.waves) and 
            not self.active_enemies and 
            self.current_life_points > 0 and
            not self.is_defeat):
            self.is_victory = True
    
    def _process_combat(self, delta_time: float):
        """处理战斗逻辑"""
        # 干员攻击敌人
        for operator in self.deployed_operators:
            if operator.attack_cooldown <= 0:
                # 寻找目标
                target = self._find_attack_target(operator)
                if target:
                    damage = operator.atk
                    actual_damage = target.take_damage(damage)
                    # 重置攻击冷却时间
                    operator.attack_cooldown = operator.base_attack_time / operator.attack_speed
        
        # 敌人攻击干员
        for enemy in self.active_enemies:
            if enemy.is_blocked and enemy.attack_cooldown <= 0:
                if enemy.blocked_by:
                    damage = enemy.atk
                    actual_damage = enemy.blocked_by.take_damage(damage)
                    # 重置攻击冷却时间
                    enemy.attack_cooldown = enemy.base_attack_time / enemy.attack_speed
    
    def _find_attack_target(self, operator: Operator) -> Optional[Enemy]:
        """
        为干员寻找攻击目标
        
        Args:
            operator: 干员
            
        Returns:
            目标敌人，如果没有返回None
        """
        if not operator.position:
            return None
        
        # 优先攻击阻挡的敌人
        for enemy in operator.blocked_enemies:
            if enemy.is_alive:
                return enemy
        
        # 寻找攻击范围内的敌人
        closest_enemy = None
        closest_distance = float('inf')
        
        for enemy in self.active_enemies:
            if not enemy.is_alive or not enemy.position:
                continue
            
            if operator.can_attack(enemy.position):
                distance = operator.position.distance_to(enemy.position)
                if distance < closest_distance:
                    closest_distance = distance
                    closest_enemy = enemy
        
        return closest_enemy
    
    def _process_blocking(self):
        """处理阻挡逻辑"""
        # 检查每个敌人是否可以被阻挡
        for enemy in self.active_enemies:
            if enemy.is_blocked or not enemy.position:
                continue
            
            tile = self.get_tile_at(enemy.position)
            if tile and tile.deployed_operator:
                operator = tile.deployed_operator
                
                # 检查干员是否还能阻挡更多敌人
                if len(operator.blocked_enemies) < operator.max_block_count:
                    enemy.get_blocked_by(operator)
                    operator.blocked_enemies.append(enemy)
        
        # 清理已死亡敌人的阻挡关系
        for operator in self.deployed_operators:
            operator.blocked_enemies = [e for e in operator.blocked_enemies if e.is_alive]
        
        # 清理被已死亡或撤退干员阻挡的敌人
        for enemy in self.active_enemies:
            if enemy.is_blocked and enemy.blocked_by:
                # 检查阻挡该敌人的干员是否还在部署列表中且还活着
                if (enemy.blocked_by not in self.deployed_operators or 
                    not enemy.blocked_by.is_alive):
                    enemy.release_block()
    
    def _update_waves(self, delta_time: float):
        """更新波次状态"""
        if self.current_wave_index >= len(self.waves):
            return
        
        current_wave = self.waves[self.current_wave_index]
        
        if not current_wave.is_active:
            current_wave.is_active = True
        
        current_wave.current_time += delta_time
        
        # 更新波次中的片段
        for fragment in current_wave.fragments:
            if not fragment.is_active and current_wave.current_time >= fragment.pre_delay:
                fragment.is_active = True
            
            if fragment.is_active and not fragment.is_completed:
                fragment.current_time += delta_time
                
                # 处理片段中的动作
                for action in fragment.actions:
                    if not action.is_completed:
                        action.current_time += delta_time
                        
                        if action.current_time >= action.pre_delay:
                            if action.action_type == "SPAWN":
                                if action.spawned_count < action.count:
                                    self.spawn_enemy(action.enemy_key, action.route_index)
                                    action.spawned_count += 1
                                    
                                    if action.spawned_count >= action.count:
                                        action.is_completed = True
                            else:
                                # 对于非SPAWN操作（如STORY、DISPLAY_ENEMY_INFO等），直接标记为完成
                                action.is_completed = True
                
                # 检查片段是否完成
                if all(action.is_completed for action in fragment.actions):
                    fragment.is_completed = True
        
        # 检查波次是否完成
        if all(fragment.is_completed for fragment in current_wave.fragments):
            current_wave.is_completed = True
            self.current_wave_index += 1
