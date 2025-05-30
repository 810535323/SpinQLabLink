"""
设备类

负责保存设备参数
"""

class Device:
    """
    设备类

    负责保存设备参数
    """
    def __init__(self, device_id: str, device_type: str, device_params: dict):
        self.device_id = device_id
        self.device_type = device_type
        self.device_params = device_params

    def set_device_params(self, device_params: dict):
        self.device_params = device_params

    def set_lock_data_post(self, lock_data_post: dict):
        self.lock_data_post = lock_data_post
