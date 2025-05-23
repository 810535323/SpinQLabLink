"""
NMR Experiment Module

Provides Nuclear Magnetic Resonance experiment functionality
"""

from typing import Dict, Any, Optional, List, Union
import time

from .experiment_base import BaseExperiment, Pulse
from ..utils import LoggerManager

# Create logger
logger = LoggerManager.get_logger(name='exp_nmr')
class EXP_NMR_PARAMETERS:
    """NMR Experiment Parameters Class"""
    def __init__(self):
        # Pulse configuration
        self.pulse = {
            "hPulse": [],  # Hydrogen nucleus pulse sequence
            "pPulse": []   # Phosphorus nucleus pulse sequence
        }
        self.h_freq = 27.0  # Hydrogen resonance frequency (MHz)
        self.p_freq = 11.0  # Phosphorus resonance frequency (MHz)
        self.makePps = False  # Whether to generate PPS signal
        self.samplePath = 0  # Sampling path selection: 0 for hydrogen channel, 1 for phosphorus channel
        self.custom_freq = True  # Whether to use custom frequency

    def _verify_pulse_format(self, hpulse: List[Pulse], ppulse: List[Pulse]):
        """Verify pulse format"""
        # Check pulse parameter format
        for pulse_list, name in [(hpulse, "Hydrogen pulse"), (ppulse, "Phosphorus pulse")]:
            if not isinstance(pulse_list, list):
                raise ValueError(f"{name} sequence must be a list type")
            
            for i, pulse in enumerate(pulse_list):
                if not isinstance(pulse, dict):
                    raise ValueError(f"Element {i+1} in {name} sequence must be a dictionary type")
                
                # Check if required keys exist
                required_keys = ["width", "amp", "phase", "detune"]
                for key in required_keys:
                    if key not in pulse:
                        raise ValueError(f"Element {i+1} in {name} sequence is missing required '{key}' parameter")
                
                # Check parameter types
                if not isinstance(pulse["width"], (int, float)) or pulse["width"] < 0:
                    raise ValueError(f"'width' parameter in element {i+1} of {name} sequence must be a non-negative numeric value")
                
                if not isinstance(pulse["amp"], (int, float)):
                    raise ValueError(f"'amp' parameter in element {i+1} of {name} sequence must be a numeric type")
                
                if not isinstance(pulse["phase"], (int, float)):
                    raise ValueError(f"'phase' parameter in element {i+1} of {name} sequence must be a numeric type")
                
                if not isinstance(pulse["detune"], (int, float)):
                    raise ValueError(f"'detune' parameter in element {i+1} of {name} sequence must be a numeric type")

    def set_pulse(self, h_pulse: List[Pulse], p_pulse: List[Pulse]):
        """Set pulse sequence"""
        """
        Set pulse sequence
        
        Args:
            h_pulse: Hydrogen pulse sequence list, each element is a dictionary containing width, amp, phase, detune
            p_pulse: Phosphorus pulse sequence list, each element is a dictionary containing width, amp, phase, detune
            
        Raises:
            ValueError: Raised when pulse parameters format is incorrect
        """
        self._verify_pulse_format(h_pulse, h_pulse)
        
        self.pulse["hPulse"] = h_pulse
        self.pulse["pPulse"] = p_pulse
        logger.debug(f"Setting pulse sequence: Hydrogen pulse count={len(h_pulse)}, Phosphorus pulse count={len(p_pulse)}")
    
    def set_h_freq(self, h_freq: float):
        """Set hydrogen resonance frequency"""
        self.h_freq = h_freq
    
    def set_p_freq(self, p_freq: float):
        """Set phosphorus resonance frequency"""
        self.p_freq = p_freq

    def set_makePps(self, makePps: bool):
        """Set whether to generate PPS signal"""
        self.makePps = makePps

    def set_samplePath(self, samplePath: int):
        """Set sampling path"""
        if samplePath not in [0, 1]:
            raise ValueError("Invalid sample path. Must be 0 or 1(H = 0, P = 1)")
        
        self.samplePath = samplePath

    def set_samplePath(self, samplePath: str):
        """Set sampling path"""
        if samplePath not in ['H', 'P']:
            raise ValueError("Invalid sample path. Must be 'H' or 'P'")
        
        self.samplePath = 0 if samplePath == 'H' else 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary"""
        return {
            "pulse": self.pulse,
            "h_freq": self.h_freq,
            "p_freq": self.p_freq,
            "makePps": self.makePps,
            "samplePath": self.samplePath,
            "custom_freq": self.custom_freq
        }

class EXP_NMR(BaseExperiment):
    """NMR Experiment Class"""
    
    def __init__(self, parameters: EXP_NMR_PARAMETERS):
        """
        Initialize NMR experiment
        
        Args:
            experiment_id: Experiment ID
            config: Experiment configuration
        """
        super().__init__(parameters=parameters)
        self.experiment_type = "NMR"
        
        self.parameters = parameters
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
        self.result = result
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
        duration = self.end_time - self.start_time
        
        # Extract experiment data
        data_points = [point["data"] for point in self.data_points]
        
        # Process NMR specific results
        # ...
        
        # Build result
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
                "raw_data": data_points,
                # NMR specific results
                # ...
            }
        }
        
        return result 