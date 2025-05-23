"""
量子比特实验类模块

提供量子比特特性测量实验功能，如T1、T2测量等
"""

from typing import Dict, Any, Optional, List, Union, Tuple
import time
import numpy as np
from uuid import UUID

from .experiment_base import BaseExperiment
from ..utils import LoggerManager


# 创建logger
logger = LoggerManager.get_logger(name='exp_qbit')


class EXP_QBit(BaseExperiment):
    """量子比特实验类"""
    
    # 支持的实验类型
    EXPERIMENT_TYPES = ['T1', 'T2', 'T2Star', 'Frequency', 'Anharmonicity']
    
    def __init__(self, experiment_id: Union[str, UUID], config: Dict[str, Any]):
        """
        初始化量子比特实验
        
        Args:
            experiment_id: 实验ID
            config: 实验配置
        """
        super().__init__(experiment_id=experiment_id, config=config)
        self.experiment_type = "QBit"
        
        # 解析配置
        self.qubit_id = config.get('qubit_id', 0)  # 量子比特ID
        self.meas_type = config.get('meas_type', '')  # 测量类型，如T1、T2等
        self.delays = config.get('delays', [])  # 时间延迟点
        self.repetitions = config.get('repetitions', 1)  # 每个点的重复次数
        self.shots = config.get('shots', 1024)  # 每次测量的次数
        
        if self.meas_type not in self.EXPERIMENT_TYPES:
            logger.warning(f"未知的测量类型: {self.meas_type}，支持的类型: {self.EXPERIMENT_TYPES}")
        
        logger.info(f"创建量子比特实验: {experiment_id}, 类型: {self.meas_type}, 量子比特: {self.qubit_id}")
        
    def start(self) -> bool:
        """
        启动实验
        
        Returns:
            bool: 是否成功启动
        """
        logger.info(f"启动量子比特实验: {self.experiment_id}")
        
        try:
            # 记录开始时间
            self.start_time = time.time()
            
            # 设置状态
            self.status = "running"
            
            # 验证配置
            if not self.meas_type:
                logger.error("未指定测量类型")
                self.status = "failed"
                return False
                
            if not self.delays:
                logger.error("未指定时间延迟点")
                self.status = "failed"
                return False
                
            # 实际启动逻辑
            # ...
            
            logger.info(f"量子比特实验启动成功: {self.experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"量子比特实验启动失败: {e}")
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
        logger.info(f"上传量子比特实验数据: {self.experiment_id}")
        
        if self.status != "running":
            logger.warning(f"实验未运行，无法上传数据: {self.experiment_id}")
            return False
            
        try:
            # 添加时间戳
            if timestamp is None:
                timestamp = time.time()
                
            # 验证数据格式
            if 'delay_index' not in data or 'counts' not in data:
                logger.error(f"数据格式错误: {data}")
                return False
                
            # 保存数据
            data_entry = {
                "timestamp": timestamp,
                "data": data
            }
            self.data_points.append(data_entry)
            
            logger.info(f"量子比特实验数据上传成功: {self.experiment_id}")
            return True
            
        except Exception as e:
            logger.error(f"量子比特实验数据上传失败: {e}")
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
        logger.info(f"结束量子比特实验: {self.experiment_id}, 状态: {status}")
        
        # 设置状态
        self.status = status
        
        # 记录结束时间
        self.end_time = time.time()
        
        # 处理结果
        result = self._process_results()
        
        # 添加消息
        if message:
            result["message"] = message
            
        logger.info(f"量子比特实验结束: {self.experiment_id}")
        return result
    
    def _exponential_fit(self, x_data: np.ndarray, y_data: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        指数衰减拟合
        
        Args:
            x_data: x轴数据（时间）
            y_data: y轴数据（测量值）
            
        Returns:
            Tuple[np.ndarray, float]: 拟合参数和时间常数
        """
        try:
            from scipy import optimize
            
            def exp_decay(x, a, t, c):
                return a * np.exp(-x / t) + c
            
            # 初始猜测
            p0 = [max(y_data) - min(y_data), np.mean(x_data), min(y_data)]
            
            # 拟合
            popt, _ = optimize.curve_fit(exp_decay, x_data, y_data, p0=p0)
            
            # 提取时间常数
            time_constant = popt[1]
            
            return popt, time_constant
            
        except Exception as e:
            logger.warning(f"指数拟合失败: {e}")
            return np.array([0, 0, 0]), 0
    
    def _process_results(self) -> Dict[str, Any]:
        """
        处理实验结果
        
        Returns:
            Dict[str, Any]: 处理后的结果
        """
        # 计算实验时长
        duration = self.end_time - self.start_time
        
        # 提取实验数据并按延迟索引排序
        data_points = sorted(self.data_points, key=lambda x: x["data"]["delay_index"])
        
        # 提取延迟和测量结果
        delays = self.delays
        measurements = []
        
        for point in data_points:
            delay_index = point["data"]["delay_index"]
            counts = point["data"]["counts"]
            
            # 计算|1⟩态的概率
            prob_1 = counts.get('1', 0) / self.shots if self.shots > 0 else 0
            measurements.append(prob_1)
        
        # 转换为numpy数组
        x_data = np.array(delays)
        y_data = np.array(measurements)
        
        # 根据测量类型进行相应的数据处理和拟合
        fit_params = None
        time_constant = None
        frequency = None
        
        if len(measurements) >= 3:
            try:
                if self.meas_type in ['T1', 'T2', 'T2Star']:
                    # 指数衰减拟合
                    fit_params, time_constant = self._exponential_fit(x_data, y_data)
                    
                elif self.meas_type == 'Frequency':
                    # 正弦拟合
                    from scipy import optimize
                    
                    def sine_model(x, a, f, phi, c):
                        return a * np.sin(2 * np.pi * f * x + phi) + c
                    
                    # 初始猜测
                    amplitude = (max(y_data) - min(y_data)) / 2
                    offset = np.mean(y_data)
                    freq_guess = 1 / (x_data[1] - x_data[0]) / 10  # 初始频率猜测
                    p0 = [amplitude, freq_guess, 0, offset]
                    
                    popt, _ = optimize.curve_fit(sine_model, x_data, y_data, p0=p0)
                    fit_params = popt
                    frequency = popt[1]  # 提取频率
                    
            except Exception as e:
                logger.warning(f"拟合失败: {e}")
        
        # 构建结果
        result = {
            "experiment_id": self.experiment_id,
            "experiment_type": self.experiment_type,
            "qubit_id": self.qubit_id,
            "meas_type": self.meas_type,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": duration,
            "data_points_count": len(self.data_points),
            "config": self.config,
            "result": {
                "delays": delays,
                "measurements": measurements,
                "fit_params": fit_params.tolist() if fit_params is not None else None
            }
        }
        
        # 根据测量类型添加特定结果
        if self.meas_type in ['T1', 'T2', 'T2Star'] and time_constant is not None:
            result["result"][self.meas_type] = time_constant
            
        if self.meas_type == 'Frequency' and frequency is not None:
            result["result"]["frequency"] = frequency
            
        return result 