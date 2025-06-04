"""
日志工具模块，提供可配置的日志功能。
"""

import os
import logging
import datetime
from logging.handlers import RotatingFileHandler


class LoggerManager:
    """日志管理类，用于创建和配置日志器"""
    
    # 默认日志格式
    DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # 日志级别映射
    LEVEL_MAP = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }
    
    # 单例模式，保存所有日志器实例
    _loggers = {}
    
    @classmethod
    def get_logger(cls, name='spinq', level='info', 
                  log_file=None, max_size=10*1024*1024, backup_count=5,
                  log_format='%(asctime)s [%(levelname)s] %(message)s'):
        """
        获取日志器实例
        
        Args:
            name: 日志器名称
            level: 日志级别，可选：debug, info, warning, error, critical
            log_file: 日志文件路径，None表示只输出到控制台
            max_size: 单个日志文件最大大小，默认10MB
            backup_count: 备份日志文件数量，默认5个
            log_format: 日志格式，默认为None表示使用DEFAULT_FORMAT
                        可以自定义格式，例如：'%(asctime)s - %(levelname)s - %(message)s'
                        常用格式化字段包括：
                        - %(asctime)s：日志时间
                        - %(name)s：日志器名称
                        - %(levelname)s：日志级别
                        - %(filename)s：文件名
                        - %(lineno)d：行号
                        - %(funcName)s：函数名
                        - %(message)s：日志信息
        
        Returns:
            logger: 日志器实例
        """
        """
        获取日志器实例
        
        Args:
            name: 日志器名称
            level: 日志级别，可选：debug, info, warning, error, critical
            log_file: 日志文件路径，None表示只输出到控制台
            max_size: 单个日志文件最大大小，默认10MB
            backup_count: 备份日志文件数量，默认5个
            log_format: 日志格式，None表示使用默认格式
            
        Returns:
            logger: 日志器实例
        """
        # 如果logger已存在直接返回
        if name in cls._loggers:
            return cls._loggers[name]
        
        # 创建logger
        logger = logging.getLogger(name)
        logger.setLevel(cls.LEVEL_MAP.get(level.lower(), logging.INFO))
        
        # 避免重复添加handler
        if logger.handlers:
            return logger
        
        # 设置日志格式
        formatter = logging.Formatter(log_format or cls.DEFAULT_FORMAT)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 如果指定了日志文件，添加文件处理器
        if log_file:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            # 创建文件处理器，支持日志轮转
            file_handler = RotatingFileHandler(
                filename=log_file,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # 保存logger实例
        cls._loggers[name] = logger
        return logger


def setup_default_logger(log_level='info', log_dir=None):
    """
    设置默认日志器
    
    Args:
        log_level: 日志级别
        log_dir: 日志目录，None表示不记录到文件
        
    Returns:
        logger: 日志器实例
    """
    log_file = None
    if log_dir:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        timestamp = datetime.datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f'spinq_{timestamp}.log')
    
    return LoggerManager.get_logger(name='spinq', level=log_level, log_file=log_file)


# 创建一个默认日志器，可以直接导入使用
default_logger = setup_default_logger()


# 导出简便方法
def debug(msg, *args, **kwargs):
    """记录debug级别日志"""
    default_logger.debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """记录info级别日志"""
    default_logger.info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """记录warning级别日志"""
    default_logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """记录error级别日志"""
    default_logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """记录critical级别日志"""
    default_logger.critical(msg, *args, **kwargs) 