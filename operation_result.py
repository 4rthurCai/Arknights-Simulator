#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional
from dataclasses import dataclass


@dataclass
class OperationResult:
    """操作结果类"""
    success: bool
    reason: Optional[str] = None
    
    @classmethod
    def success_result(cls):
        """创建成功结果"""
        return cls(success=True)
    
    @classmethod
    def failure_result(cls, reason: str):
        """创建失败结果"""
        return cls(success=False, reason=reason)
