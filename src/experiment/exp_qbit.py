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
        
        logger.info(f"Created NMR experiment")

    def handle_exp_started(self) -> None:
        """处理实验开始，实现具体实验类型的开始处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_started方法")
    
    def handle_exp_terminated(self) -> None:
        """处理实验结束，实现具体实验类型的结束处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_terminated方法")
    
    def handle_exp_removed(self) -> None:
        """处理实验移除，实现具体实验类型的移除处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_removed方法")

    def handle_exp_step_changed(self, step: int) -> None:
        """处理实验步骤变化，实现具体实验类型的步骤变化处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_step_changed方法")
    
    def handle_exp_data_updated(self, data: Dict[str, Any]) -> None:
        """处理实验数据更新，实现具体实验类型的数据更新处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_data_updated方法")
    
    def handle_exp_chart_data_updated_started(self, data: Dict[str, Any]) -> None:
        """处理实验图表数据更新，实现具体实验类型的图表数据更新处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_chart_data_updated_started方法")
    
    def handle_exp_chart_data_updated(self, data: Dict[str, Any]) -> None:
        """处理实验图表数据更新，实现具体实验类型的图表数据更新处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_chart_data_updated方法")

    def handle_exp_chart_data_updated_finished(self, data: Dict[str, Any]) -> None:
        """处理实验图表数据更新，实现具体实验类型的图表数据更新处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_chart_data_updated_finished方法")


    def handle_exp_finished(self, data: Dict[str, Any]) -> None:
        """处理实验结束，实现具体实验类型的结束处理"""
        raise NotImplementedError("必须在子类中实现handle_exp_finished方法")
