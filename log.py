import os
import logging
from logging.handlers import TimedRotatingFileHandler

class SafeTimedRotatingFileHandler(TimedRotatingFileHandler):
    """安全的日志文件处理器，处理 Windows 平台下的文件锁定问题"""
    
    def doRollover(self):
        try:
            super().doRollover()
        except PermissionError:
            # 如果无法重命名文件，忽略错误，继续使用当前文件
            pass
        except Exception:
            # 其他错误也忽略，避免程序崩溃
            pass

class Logger:
    def __init__(self, name="AppLogger", log_dir="logs"):
        """
        自动按天分割日志文件
        每天生成一个新日志，例如：
        logs_2025-11-17.log
        logs_2025-11-18.log
        """

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            os.makedirs(log_dir, exist_ok=True)

            # 定时切割日志：midnight = 每天 00:00切换
            log_filename = os.path.join(log_dir, "logs.log")
            file_handler = SafeTimedRotatingFileHandler(
                log_filename,
                when="midnight",   # 每天切一次
                interval=1,
                backupCount=7,     # 保留最近7天日志，可设为0关闭
                encoding="utf-8"
            )

            # 修改日志文件名格式
            file_handler.suffix = "%Y-%m-%d.log"

            log_format = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(log_format)
            file_handler.setLevel(logging.DEBUG)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_format)
            console_handler.setLevel(logging.INFO)
            # 设置控制台输出编码为UTF-8，避免Windows下GBK编码问题
            console_handler.encoding = 'utf-8'

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def debug(self, msg):
        self.logger.debug(msg)


if __name__ == "__main__":
    log = Logger()
    log.info("系统启动成功 🚀")
    log.debug("调试信息：配置已加载")
    log.warning("电量低于20% ⚠️")
    log.error("请求失败：超时 ❌")
