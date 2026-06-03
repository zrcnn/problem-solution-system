#!/usr/bin/env python3
"""
日志系统工具
提供统一的日志管理功能，支持按日期存放、时间戳、日志级别等
"""

import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
import json

class Logger:
    """统一的日志系统工具类"""
    
    # 日志级别映射
    LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __init__(self, name='problem_solution_system', log_dir='logs', level='INFO'):
        """
        初始化日志系统
        
        Args:
            name: 日志记录器名称
            log_dir: 日志存放目录
            level: 日志级别
        """
        self.name = name
        self.log_dir = log_dir
        self.level = self.LEVELS.get(level.upper(), logging.INFO)
        
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 创建日志记录器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # 清除可能存在的处理器
        self.logger.handlers.clear()
        
        # 添加控制台处理器
        console_handler = self._create_console_handler()
        self.logger.addHandler(console_handler)
        
        # 添加文件处理器（按日期分割）
        file_handler = self._create_file_handler()
        self.logger.addHandler(file_handler)
        
        # 添加错误日志专用处理器
        error_handler = self._create_error_handler()
        self.logger.addHandler(error_handler)
    
    def _create_console_handler(self):
        """创建控制台处理器"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.level)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        return console_handler
    
    def _create_file_handler(self):
        """创建文件处理器（按日期分割）"""
        # 日志文件名格式：app_YYYY-MM-DD.log
        log_file = os.path.join(self.log_dir, f'{self.name}_%Y-%m-%d.log')
        
        # 使用时间分割处理器，每天一个文件
        file_handler = TimedRotatingFileHandler(
            filename=os.path.join(self.log_dir, f'{self.name}.log'),
            when='D',  # 按天分割
            interval=1,
            backupCount=30,  # 保留30天的日志
            encoding='utf-8'
        )
        file_handler.setLevel(self.level)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # 设置文件后缀
        file_handler.suffix = '%Y-%m-%d.log'
        
        return file_handler
    
    def _create_error_handler(self):
        """创建错误日志专用处理器"""
        # 错误日志单独存放
        error_file = os.path.join(self.log_dir, f'{self.name}_errors.log')
        
        error_handler = RotatingFileHandler(
            filename=error_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,  # 保留5个文件
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # 设置格式
        formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        error_handler.setFormatter(formatter)
        
        return error_handler
    
    def debug(self, message, **kwargs):
        """记录DEBUG级别日志"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message, **kwargs):
        """记录INFO级别日志"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message, **kwargs):
        """记录WARNING级别日志"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message, **kwargs):
        """记录ERROR级别日志"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message, **kwargs):
        """记录CRITICAL级别日志"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message, **kwargs):
        """记录异常日志"""
        self.logger.exception(message, **kwargs)
    
    def _log(self, level, message, **kwargs):
        """
        通用日志记录方法
        
        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外的字段，会添加到日志中
        """
        if kwargs:
            # 如果有额外字段，将消息和字段合并为JSON格式
            log_data = {
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'extra': kwargs
            }
            message = json.dumps(log_data, ensure_ascii=False)
        
        self.logger.log(level, message)
    
    def log_request(self, method, path, status_code, duration, ip=None, user_agent=None):
        """记录HTTP请求日志"""
        self.info(
            f"{method} {path} {status_code}",
            method=method,
            path=path,
            status_code=status_code,
            duration=f"{duration:.3f}s",
            ip=ip,
            user_agent=user_agent
        )
    
    def log_database_operation(self, operation, table, success=True, error=None):
        """记录数据库操作日志"""
        if success:
            self.info(
                f"DB {operation} {table}",
                operation=operation,
                table=table,
                success=success
            )
        else:
            self.error(
                f"DB {operation} {table} failed",
                operation=operation,
                table=table,
                success=success,
                error=error
            )
    
    def log_user_action(self, user_id, action, target=None, result='success'):
        """记录用户操作日志"""
        self.info(
            f"User {user_id} {action}",
            user_id=user_id,
            action=action,
            target=target,
            result=result
        )
    
    def cleanup_old_logs(self, days=30):
        """清理旧日志文件"""
        import glob
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        log_files = glob.glob(os.path.join(self.log_dir, f'{self.name}_*.log'))
        
        cleaned_count = 0
        for log_file in log_files:
            # 从文件名提取日期
            try:
                file_date_str = os.path.basename(log_file).split('_')[1].replace('.log', '')
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    os.remove(log_file)
                    cleaned_count += 1
            except (IndexError, ValueError):
                # 文件名格式不正确，跳过
                continue
        
        if cleaned_count > 0:
            self.info(f"清理了 {cleaned_count} 个旧日志文件")
        
        return cleaned_count


# 全局日志实例
_logger = None

def get_logger(name='problem_solution_system', log_dir='logs', level='INFO'):
    """
    获取全局日志实例
    
    Args:
        name: 日志记录器名称
        log_dir: 日志存放目录
        level: 日志级别
    
    Returns:
        Logger实例
    """
    global _logger
    if _logger is None:
        _logger = Logger(name, log_dir, level)
    return _logger


def init_app_logger(app):
    """
    为Flask应用初始化日志系统
    
    Args:
        app: Flask应用实例
    """
    # 创建日志记录器
    logger = get_logger(app.name or 'flask_app')
    
    # 将日志记录器绑定到应用
    app.logger.handlers = []
    for handler in logger.logger.handlers:
        app.logger.addHandler(handler)
    app.logger.setLevel(logger.level)
    
    # 记录应用启动日志
    logger.info("应用启动", extra={
        'app_name': app.name,
        'debug': app.debug,
        'start_time': datetime.now().isoformat()
    })
    
    return logger


if __name__ == '__main__':
    # 测试日志系统
    logger = get_logger('test_app', 'test_logs', 'DEBUG')
    
    logger.debug('这是一条调试日志')
    logger.info('这是一条信息日志')
    logger.warning('这是一条警告日志')
    logger.error('这是一条错误日志')
    logger.critical('这是一条严重错误日志')
    
    # 测试带额外字段的日志
    logger.info('用户登录', user_id=123, username='test', ip='192.168.1.1')
    
    # 测试请求日志
    logger.log_request('GET', '/api/test', 200, 0.123, '127.0.0.1', 'Mozilla/5.0')
    
    # 测试数据库操作日志
    logger.log_database_operation('SELECT', 'users', True)
    logger.log_database_operation('UPDATE', 'users', False, 'Connection timeout')
    
    # 测试用户操作日志
    logger.log_user_action(123, 'login', '/dashboard', 'success')
    
    print("日志测试完成，查看 logs/ 目录下的日志文件")
