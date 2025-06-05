# Copyright 2025 SpinQ Technology Co., Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
