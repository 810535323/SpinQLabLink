"""
量子电路实验类模块

提供量子电路实验功能，支持执行量子电路并获取测量结果
"""

from typing import Dict, Any, Optional, List, Union
import time
import json
from uuid import UUID

from .experiment_base import BaseExperiment
from ..utils import LoggerManager


# 创建logger
logger = LoggerManager.get_logger(name='exp_qcircuit')


class EXP_QCircuit(BaseExperiment):
    """量子电路实验类"""
    
    def __init__(self, experiment_id: Union[str, UUID], config: Dict[str, Any]):
        """
        初始化量子电路实验
        
        Args:
            experiment_id: 实验ID
            config: 实验配置
        """
        super().__init__(experiment_id=experiment_id, config=config)
        self.experiment_type = "QCircuit"
        
        # 解析配置
        self.circuit = config.get('circuit', {})  # 量子电路定义
        self.shots = config.get('shots', 1024)   # 电路执行次数
        self.optimization_level = config.get('optimization_level', 1)  # 优化级别
        self.noise_model = config.get('noise_model')  # 噪声模型
        self.backend = config.get('backend', 'default')  # 后端
        
        logger.info(f"创建量子电路实验: {experiment_id}")
        
    def start(self) -> bool:
        """
        启动实验
        
        Returns:
            bool: 是否成功启动
        """
        logger.info(f"启动量子电路实验: {self.experiment_id}")
        
        try:
            # 记录开始时间
            self.start_time = time.time()
            
            # 设置状态
            self.status = "running"
            
            # 验证电路
            if not self.circuit:
                logger.error("量子电路实验缺少电路定义")
                self.status = "failed"
                return False
                
            # 验证电路格式（这里假设有特定格式要求）
            required_fields = ['qubits', 'gates']
            if not all(field in self.circuit for field in required_fields):
                logger.error(f"电路定义缺少必要字段: {required_fields}")
                self.status = "failed"
                return False
            
            # 实际启动逻辑
            # ...
            
            logger.info(f"量子电路实验启动成功: {self.experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"量子电路实验启动失败: {e}")
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
        logger.info(f"上传量子电路实验数据: {self.experiment_id}")
        
        if self.status != "running":
            logger.warning(f"实验未运行，无法上传数据: {self.experiment_id}")
            return False
            
        try:
            # 添加时间戳
            if timestamp is None:
                timestamp = time.time()
                
            # 验证数据格式
            if 'counts' not in data:
                logger.error(f"数据格式错误: {data}")
                return False
                
            # 保存数据
            data_entry = {
                "timestamp": timestamp,
                "data": data
            }
            self.data_points.append(data_entry)
            
            logger.info(f"量子电路实验数据上传成功: {self.experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"量子电路实验数据上传失败: {e}")
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
        logger.info(f"结束量子电路实验: {self.experiment_id}, 状态: {status}")
        
        # 设置状态
        self.status = status
        
        # 记录结束时间
        self.end_time = time.time()
        
        # 处理结果
        result = self._process_results()
        
        # 添加消息
        if message:
            result["message"] = message
            
        logger.info(f"量子电路实验结束: {self.experiment_id}")
        return result
    
    def get_circuit_depth(self) -> int:
        """
        计算电路深度
        
        Returns:
            int: 电路深度
        """
        # 简化的电路深度计算
        # 实际应用中可能需要更复杂的计算
        try:
            gates = self.circuit.get('gates', [])
            if not gates:
                return 0
                
            # 按时间层次分组的门
            time_layers = {}
            
            for gate in gates:
                # 假设每个门有一个time_step属性表示它的时间层
                # 如果没有，可以基于依赖关系计算
                time_step = gate.get('time_step', 0)
                if time_step not in time_layers:
                    time_layers[time_step] = []
                time_layers[time_step].append(gate)
                
            # 深度是最大时间层 + 1
            return max(time_layers.keys()) + 1 if time_layers else 1
            
        except Exception as e:
            logger.warning(f"计算电路深度失败: {e}")
            return 0
    
    def _process_results(self) -> Dict[str, Any]:
        """
        处理实验结果
        
        Returns:
            Dict[str, Any]: 处理后的结果
        """
        # 计算实验时长
        duration = self.end_time - self.start_time
        
        # 合并所有数据点的计数
        combined_counts = {}
        
        for point in self.data_points:
            counts = point["data"]["counts"]
            for state, count in counts.items():
                if state in combined_counts:
                    combined_counts[state] += count
                else:
                    combined_counts[state] = count
        
        # 计算总测量次数
        total_shots = sum(combined_counts.values())
        
        # 计算每个态的概率
        probabilities = {
            state: count / total_shots if total_shots > 0 else 0
            for state, count in combined_counts.items()
        }
        
        # 计算电路深度
        circuit_depth = self.get_circuit_depth()
        
        # 构建结果
        result = {
            "experiment_id": self.experiment_id,
            "experiment_type": self.experiment_type,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": duration,
            "data_points_count": len(self.data_points),
            "config": self.config,
            "result": {
                "counts": combined_counts,
                "probabilities": probabilities,
                "total_shots": total_shots,
                "circuit_depth": circuit_depth,
                "backend": self.backend
            }
        }
        
        return result
    
    def to_json(self) -> str:
        """
        将结果转换为JSON字符串
        
        Returns:
            str: JSON字符串
        """
        result = self._process_results()
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    def to_csv(self) -> str:
        """
        将结果转换为CSV格式
        
        Returns:
            str: CSV字符串
        """
        result = self._process_results()
        counts = result["result"]["counts"]
        
        # 构建CSV
        csv_lines = ["state,count,probability"]
        for state, count in counts.items():
            prob = count / result["result"]["total_shots"] if result["result"]["total_shots"] > 0 else 0
            csv_lines.append(f"{state},{count},{prob:.6f}")
            
        return "\n".join(csv_lines) 