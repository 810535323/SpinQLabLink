"""
量子比特控制实验类模块

提供量子比特控制实验功能，包括单比特和多比特控制操作
"""

from typing import Dict, Any, Optional, List, Union, Tuple
import time
import numpy as np
from uuid import UUID

from .experiment_base import BaseExperiment
from ..utils import LoggerManager


# 创建logger
logger = LoggerManager.get_logger(name='exp_qcontrol')


class EXP_QControl(BaseExperiment):
    """量子比特控制实验类"""
    
    def __init__(self, experiment_id: Union[str, UUID], config: Dict[str, Any]):
        """
        初始化量子比特控制实验
        
        Args:
            experiment_id: 实验ID
            config: 实验配置
        """
        super().__init__(experiment_id=experiment_id, config=config)
        self.experiment_type = "QControl"
        
        # 解析配置
        self.qubit_ids = config.get('qubit_ids', [0])  # 控制的量子比特
        self.gate_sequence = config.get('gate_sequence', [])  # 门序列
        self.control_params = config.get('control_params', {})  # 控制参数
        self.shots = config.get('shots', 1024)  # 每个实验的测量次数
        self.repetitions = config.get('repetitions', 1)  # 实验重复次数
        
        logger.info(f"创建量子比特控制实验: {experiment_id}, 量子比特: {self.qubit_ids}")
        
    def start(self) -> bool:
        """
        启动实验
        
        Returns:
            bool: 是否成功启动
        """
        logger.info(f"启动量子比特控制实验: {self.experiment_id}")
        
        try:
            # 记录开始时间
            self.start_time = time.time()
            
            # 设置状态
            self.status = "running"
            
            # 验证配置
            if not self.qubit_ids:
                logger.error("量子比特控制实验缺少量子比特ID")
                self.status = "failed"
                return False
                
            if not self.gate_sequence:
                logger.error("量子比特控制实验缺少门序列")
                self.status = "failed"
                return False
                
            # 实际启动逻辑
            # ...
            
            logger.info(f"量子比特控制实验启动成功: {self.experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"量子比特控制实验启动失败: {e}")
            self.status = "failed"
            return False
    
    def upload_data(self, data: Dict[str, Any], timestamp: Optional[float] = None) -> bool:
        """
        上传实验数据
        
        Args:
            data: 实验数据
            timestamp: 数据时间戳
            
        Returns:
            bool: 是否成功上传
        """
        logger.info(f"上传量子比特控制实验数据: {self.experiment_id}")
        
        if self.status != "running":
            logger.warning(f"实验未运行，无法上传数据: {self.experiment_id}")
            return False
            
        try:
            # 添加时间戳
            if timestamp is None:
                timestamp = time.time()
                
            # 验证数据格式
            if 'sequence_index' not in data or 'counts' not in data:
                logger.error(f"数据格式错误: {data}")
                return False
                
            # 保存数据
            data_entry = {
                "timestamp": timestamp,
                "data": data
            }
            self.data_points.append(data_entry)
            
            logger.info(f"量子比特控制实验数据上传成功: {self.experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"量子比特控制实验数据上传失败: {e}")
            return False
    
    def finish(self, status: str, message: Optional[str] = None) -> Dict[str, Any]:
        """
        结束实验
        
        Args:
            status: 实验结束状态
            message: 附加信息
            
        Returns:
            Dict[str, Any]: 实验结果
        """
        logger.info(f"结束量子比特控制实验: {self.experiment_id}, 状态: {status}")
        
        # 设置状态
        self.status = status
        
        # 记录结束时间
        self.end_time = time.time()
        
        # 处理结果
        result = self._process_results()
        
        # 添加消息
        if message:
            result["message"] = message
            
        logger.info(f"量子比特控制实验结束: {self.experiment_id}")
        return result
    
    def _calculate_fidelity(self, target_state: Dict[str, float], measured_counts: Dict[str, int]) -> float:
        """
        计算测量结果与目标态的保真度
        
        Args:
            target_state: 目标态
            measured_counts: 测量计数
            
        Returns:
            float: 保真度
        """
        # 简化的保真度计算，实际应用中可能需要更复杂的计算
        total_count = sum(measured_counts.values())
        if total_count == 0:
            return 0.0
            
        fidelity = 0.0
        for state, prob in target_state.items():
            measured_prob = measured_counts.get(state, 0) / total_count
            fidelity += np.sqrt(prob * measured_prob)
            
        return min(fidelity ** 2, 1.0)
    
    def _process_results(self) -> Dict[str, Any]:
        """
        处理实验结果
        
        Returns:
            Dict[str, Any]: 处理后的结果
        """
        # 计算实验时长
        duration = self.end_time - self.start_time
        
        # 提取实验数据并按序列索引排序
        data_points = sorted(self.data_points, key=lambda x: x["data"]["sequence_index"])
        
        # 处理每个序列步骤的结果
        sequence_results = []
        
        for point in data_points:
            sequence_index = point["data"]["sequence_index"]
            counts = point["data"]["counts"]
            
            # 如果有目标态，计算保真度
            target_state = point["data"].get("target_state")
            fidelity = None
            if target_state:
                fidelity = self._calculate_fidelity(target_state, counts)
                
            # 收集此序列步骤的结果
            step_result = {
                "sequence_index": sequence_index,
                "counts": counts,
                "target_state": target_state,
                "fidelity": fidelity,
                "timestamp": point["timestamp"]
            }
            
            sequence_results.append(step_result)
        
        # 计算平均保真度
        valid_fidelities = [
            result["fidelity"] for result in sequence_results 
            if result["fidelity"] is not None
        ]
        
        avg_fidelity = sum(valid_fidelities) / len(valid_fidelities) if valid_fidelities else None
        
        # 构建结果
        result = {
            "experiment_id": self.experiment_id,
            "experiment_type": self.experiment_type,
            "qubit_ids": self.qubit_ids,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": duration,
            "data_points_count": len(self.data_points),
            "config": self.config,
            "result": {
                "sequence_results": sequence_results,
                "average_fidelity": avg_fidelity
            }
        }
        
        return result 