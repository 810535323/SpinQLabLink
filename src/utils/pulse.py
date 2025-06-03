from pydantic import Field, BaseModel

class Pulse(BaseModel):
    """
    脉冲类
    """
    path: int = Field(default=0, ge=0, le=1, description="Path selection: 0 for hydrogen channel, 1 for phosphorus channel")
    width: float = Field(default=0, ge=0, le=2000000, description="Width (µs)")
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