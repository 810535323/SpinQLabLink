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

from pydantic import Field, BaseModel

class Pulse(BaseModel):
    """
    脉冲类
    """
    path: int = Field(default=0, ge=0, le=1, description="Path selection: 0 for hydrogen channel, 1 for phosphorus channel")
    width: float = Field(default=0, ge=0, le=20000000, description="Width (µs)")
    amplitude: float = Field(default=0, ge=0, le=100, description="Amplitude (%)")
    phase: float = Field(default=0, description="Phase (°)")
    detuning: float = Field(default=0, ge=-10000, le=10000, description="Frequency shift (Hz)")

    def to_dict(self) -> dict:
        """
        将Pulse对象转换为字典
        
        Returns:
            dict: 脉冲的字典表示
        """
        return {
            "width": self.width,
            "am": self.amplitude,
            "phase": self.phase,
            "freshift": self.detuning
        }