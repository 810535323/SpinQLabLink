"""
NMR Experiment Module

Provides Nuclear Magnetic Resonance experiment functionality
"""

from typing import Dict, Any, Optional, List, Union
import time

from .exp_nmr import EXP_NMR_PARAMETERS
from .experiment_base import BaseExperiment, Pulse
from ..utils import LoggerManager

# Create logger
logger = LoggerManager.get_logger(name='exp_rabi')
class EXP_RABI_PARAMETERS(EXP_NMR_PARAMETERS):
    """Rabi Experiment Parameters Class"""
    def __init__(self):
        super().__init__()


class EXP_RABI(BaseExperiment):
    """Rabi Experiment Class"""
    
    def __init__(self, parameters: EXP_RABI_PARAMETERS):
        """
        Initialize Rabi experiment
        
        Args:
            experiment_id: Experiment ID
            config: Experiment configuration
        """
        super().__init__(parameters=parameters)
        self.experiment_type = "NMR"
        
        self.parameters = parameters
        logger.info(f"Created Rabi experiment")

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