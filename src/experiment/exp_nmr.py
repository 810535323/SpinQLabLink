"""
NMR Experiment Module

Provides Nuclear Magnetic Resonance experiment functionality
"""

from typing import Dict, Any, Optional, List, Union
import time
import json

from experiment.experiment_base import Experiment, ExperimentParameter
from utils import LoggerManager
from pydantic import Field

# Create logger
logger = LoggerManager.get_logger(name='exp_nmr')

class ExpNMRParameters(ExperimentParameter):
    """NMR Experiment Parameters Class"""
    pulse_json: str = Field(default="", description="Pulse sequence in JSON format")
    h_freq: float = Field(default=27.0, gt=0, lt=100, description="Hydrogen resonance frequency (MHz)")
    p_freq: float = Field(default=11.0, gt=0, lt=100, description="Phosphorus resonance frequency (MHz)")
    makePps: bool = Field(default=False, description="Whether to generate PPS signal")
    samplePath: int = Field(default=0, ge=0, le=1, description="Sampling path selection: 0 for hydrogen channel, 1 for phosphorus channel")
    custom_freq: bool = Field(default=True, description="Whether to use custom frequency(h_freq or p_freq)")

    def set_pulse(self, pulse_json: str):
        """Set pulse sequence"""
        try:
            if not self._validate_pulse_json(pulse_json):
                raise ValueError("Invalid pulse sequence")
            self.pulse_json = pulse_json
        except Exception as e:
            logger.error(f"Error setting pulse sequence: {e}")
            raise e
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        return {
            "pulse": json.loads(self.pulse_json),
            "h_freq": self.h_freq,
            "p_freq": self.p_freq,
            "makePps": self.makePps,
            "samplePath": self.samplePath,
            "custom_freq": self.custom_freq
        }

class ExpNMR(Experiment):
    """NMR Experiment Class"""
    
    def __init__(self, parameters: ExpNMRParameters):
        """
        Initialize NMR experiment
        
        Args:
            parameters: NMR experiment parameters
        """
        super().__init__(parameters)
        self.experiment_type = "NMR"
        
        # 初始化实验相关属性
        self.data_points = []
        self.status = "initialized"
        self.start_time = None
        self.end_time = None
        self.error_message = ""
        
        logger.info(f"Created NMR experiment")

    def data_update_callback(self, data: Dict[str, Any]) -> None:
        """
        Process experiment data
        
        Args:
            data: Experiment data
        """
        logger.info(f"Received experiment data update: {data}")
        # Store data points
        self.data_points.append(data)
        # Call external callback if exists
        if self._data_callback:
            self._data_callback(data)

    def status_update_callback(self, status: str) -> None:
        """
        Process experiment status
        
        Args:
            status: Experiment status
        """
        logger.info(f"Experiment status update: {status}")
        self.status = status
        # Call external status callback if exists
        if self._status_callback:
            self._status_callback(status)

    def error_callback(self, error: str) -> None:
        """
        Process experiment error
        
        Args:
            error: Experiment error
        """
        logger.error(f"Experiment error: {error}")
        self.status = "error"
        self.error_message = error
        # Call external error callback if exists
        if self._error_callback:
            self._error_callback(error)

    def finish_callback(self, result: Dict[str, Any]) -> None:
        """
        Process experiment completion
        
        Args:
            result: Experiment result
        """
        logger.info(f"Experiment completed")
        self.status = "completed"
        self.end_time = time.time()
        self.result.data = result
        # Process results
        processed_result = self._process_results()
        # Call external finish callback if exists
        if self._finish_callback:
            self._finish_callback(processed_result)
    
    def _process_results(self) -> Dict[str, Any]:
        """
        Process experiment results
        
        Returns:
            Dict[str, Any]: Processed results
        """
        # Calculate experiment duration
        duration = 0
        if self.start_time and self.end_time:
            duration = self.end_time - self.start_time
        
        # Extract experiment data
        data_points = []
        if hasattr(self, 'data_points') and self.data_points:
            data_points = [point.get("data", point) for point in self.data_points]
        
        # Process NMR specific results
        # 这里可以添加 NMR 特定的数据处理逻辑
        # 例如：信号处理、频谱分析等
        
        # Build result
        result = {
            "experiment_type": self.experiment_type,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": duration,
            "data_points_count": len(data_points),
            "parameters": self.parameters.to_dict() if self.parameters else {},
            "result": {
                "raw_data": data_points,
                "processed_data": {},  # NMR 特定的处理结果
                "analysis": {}  # 分析结果
            }
        }
        
        return result 