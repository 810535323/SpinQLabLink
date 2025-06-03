"""
SpinQLabLink

负责管理设备连接、断开连接、获取连接、获取实验管理器、获取设备信息
"""

from typing import Dict, Any
import time
import uuid
from connection.connection import TCPConnection
from utils import LoggerManager
from connection.protocol import Protocol
from connection.heartbeat import HeartbeatManager
from devices.device import Device
from utils.types import ExperimentType, MachineType
from experiment.ExperimentManager import ExperimentManager

# 创建logger
logger = LoggerManager.get_logger(name='spinqlablink')

class SpinQLabLink:
    """SpinQLabLink"""
    def __init__(self, host: str, port: int, account: str, password: str):
        self.connection = TCPConnection(host, port)
        self.connection.set_message_callback(self._handle_received_message)
        self.protocol = Protocol()
        self.expMgr = ExperimentManager()
        self.hardware_connected = False
        self.is_connected = False
        self.logging_in = False
        self.is_logged_in = False
        self.account = account
        self.password = password
        self.device_id = str("SpinQLabLink-" + str(uuid.uuid4()).upper()[:8])
        self.session_id = ""
        
        self.device = Device(device_id=self.device_id, device_type="SpinQLabLink", device_params={})
        
        # 心跳管理器
        self.heartbeat_manager = HeartbeatManager(self._send_message)
        self.heartbeat_manager.set_timeout_callback(self._on_heartbeat_timeout)
        
        self.handler_map = {
            MachineType.MSG_RES_USER_LOGIN: self._handle_user_login_res,
            MachineType.MSG_RES_USER_LOGOUT: self._handle_user_logout_res,
            MachineType.MSG_RES_HEARTBEAT: self._handle_heartbeat_res,
            MachineType.MSG_POST_PARAM: self._handle_device_param_post,
            MachineType.MSG_POST_LOCK_DATA: self._handle_lock_data_update_post,
            MachineType.MSG_POST_INFO: self._handle_device_info_post,
            MachineType.MSG_POST_SAMPLE_CALIBRATION: self._handle_sample_calibration_post,
            MachineType.MSG_POST_EXP_QUEUE_UPDATE: self._handle_exp_queue_update_post
        }

        self.exp_handler_map = {}

    def _send_message(self, msg_id: str, data: dict):
        serialized_message = self.protocol.serialize_message(msg_id, self._pack_metadata(), data)
        self.connection.send(serialized_message)

    def _handle_received_message(self, data: bytes):
        success, dict_data = self.protocol.deserialize_message(data)
        if not success: # 消息不完全，等待下次处理
            return
        
        handler = self.handler_map.get(dict_data["msg_id"])
        if handler:
            handler(dict_data["json_data"])
        else:
            handler = self.exp_handler_map.get(dict_data["msg_id"])
            if handler:
                if "json_data" in dict_data and dict_data["json_data"]:
                    handler(dict_data["json_data"])
                elif "chart_data" in dict_data and dict_data["chart_data"]:
                    handler(dict_data["chart_data"])
            else:
                logger.error(f"Message handler not found: {dict_data['msg_id']}")

    def _handle_user_login_res(self, data: Dict[str, Any]):
        logger.info(f"Login response: {data}")
        if data["code"] == 0:
            if data["sessionId"]:
                self.session_id = data["sessionId"]
                self.is_logged_in = True
                self.heartbeat_manager.start()
            else:
                logger.error("Login failed, sessionId is empty")
        else:
            logger.error(f"Login failed, error code: {data['json_data']['code']}, error message: {data['json_data']['message']}")

    def _handle_user_logout_res(self, data: Dict[str, Any]):
        logger.info(f"Logout response: {data}")
        self.is_logged_in = False
        
        # 登出时停止心跳
        self.heartbeat_manager.stop()

    def _handle_heartbeat_res(self, data: Dict[str, Any]):
        # 通知心跳管理器收到响应
        self.heartbeat_manager.on_heartbeat_response()

    def _handle_device_param_post(self, data: Dict[str, Any]):
        logger.info(f"Device parameters: {data}")
        self.device.set_device_params(data)

    def _handle_lock_data_update_post(self, data: Dict[str, Any]):
        logger.info(f"Device lock data update: {data}")
        self.device.set_lock_data_post(data)

    def _handle_device_info_post(self, data: Dict[str, Any]):
        logger.info(f"Device info: {data}")
        if data["connected"]:
            self.hardware_connected = data["connected"]

    def _handle_sample_calibration_post(self, data: Dict[str, Any]):
        logger.info(f"Sample calibration: {data}")

    def _handle_exp_queue_update_post(self, data: Dict[str, Any]):
        logger.info(f"Experiment queue update: {data}")
        for i, queue in enumerate(data["queue"]):
            if queue["id"] == self.expMgr.current_experiment.id:
                if i != 0:
                    logger.info(f"Experiment waiting in queue... {i} experiments ahead")

    def _on_heartbeat_timeout(self):
        """心跳超时回调"""
        # 断开连接
        self.is_connected = False
        self.is_logged_in = False
        self.connection.disconnect()

    def _pack_metadata(self) -> Dict[str, Any]:
        metadata = {}
        metadata["sequence_id"] = int(time.time() * 1000)
        metadata["timestamp"] = int(time.time() * 1000)
        metadata["account"] = self.account
        metadata["session_id"] = self.session_id
        return metadata

    def connect(self):
        if self.connection.connect():
            self.is_connected = True
            self._login()
        else:
            return False
    
    def _login(self):
        if not self.is_connected:
            logger.error("Not connected, unable to login")
            return
        
        self.logging_in = True
        
        serialized_message = self.protocol.serialize_message(MachineType.MSG_REQ_USER_LOGIN, self._pack_metadata(), {
            "account": self.account,
            "password": self.password
        })
        
        self.connection.send(serialized_message)

    def logout(self):
        if not self.is_connected:
            logger.error("Not connected, unable to logout")
            return
        
        serialized_message = self.protocol.serialize_message(MachineType.MSG_REQ_USER_LOGOUT, self._pack_metadata(), {})
        self.connection.send(serialized_message)
        
        # 停止心跳
        self.heartbeat_manager.stop()

    def disconnect(self):
        if not self.is_connected:
            self.logout()
        
        if self.is_connected:
            self.heartbeat_manager.stop()
            self.connection.disconnect()
            return True
        else:
            return False
        
    def wait_for_login(self, timeout: int = 10):
        start_time = time.time()
        if(self.logging_in):
            while not self.is_logged_in:
                if time.time() - start_time > timeout:
                    logger.error("Login timeout")
                    self.disconnect()
                    return False
                time.sleep(0.5)
            self.logging_in = False
            return True
        else:
            return False

    def get_connection(self):
        return self.is_connected
    
    def get_expMgr(self):
        return self.expMgr
    
    def register_experiment(self, experiment_type: ExperimentType):
        return self.expMgr.register_experiment(experiment_type, self.exp_handler_map)
    
    def deregister_experiment(self):
        return self.expMgr.deregister_experiment()
    
    def get_experiment_status(self):
        return self.expMgr.get_experiment_status()
    
    def get_experiment_result(self):
        return self.expMgr.get_experiment_result()

    def run_experiment(self):
        para = self.expMgr.get_experiment_parameter()
        para["deviceId"] = self.device_id
        para["account"] = self.account
        self._send_message(MachineType.MSG_REQ_ADD_EXP_TASK_REQ, para)

    def wait_for_experiment_completion(self):
        return self.expMgr.wait_for_experiment_completion()