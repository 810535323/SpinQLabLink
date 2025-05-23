"""
异常类定义
"""

class SpinQRemoteError(Exception):
    """SpinQ远程实验接口基础异常类"""
    pass

class ConnectionError(SpinQRemoteError):
    """连接错误异常"""
    pass

class ExperimentError(SpinQRemoteError):
    """实验执行错误异常"""
    pass

class AuthenticationError(SpinQRemoteError):
    """认证错误异常"""
    pass

class DataError(SpinQRemoteError):
    """数据处理错误异常"""
    pass 