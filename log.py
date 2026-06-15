import os
import logging
from datetime import datetime


class DailyFileHandler(logging.Handler):
    """按日期生成日志文件：logs/YYYY-MM-DD.log，每天自动切换到新文件。"""

    def __init__(self, log_dir="logs", encoding="utf-8"):
        super().__init__()
        self.log_dir = log_dir
        self.encoding = encoding
        os.makedirs(self.log_dir, exist_ok=True)
        self._current_date = None
        self._current_path = None
        self._open_file()

    def _open_file(self):
        today = datetime.now().strftime("%Y-%m-%d")
        if today == self._current_date and self._current_path:
            return
        self._current_date = today
        self._current_path = os.path.join(self.log_dir, f"{today}.log")
        # 不持有关闭句柄，防止 Windows 锁定；每次写时重新打开
        self.stream = None

    def _ensure_stream(self):
        self._open_file()
        try:
            self.stream = open(self._current_path, "a", encoding=self.encoding)
        except Exception:
            self.stream = None

    def emit(self, record):
        try:
            self._ensure_stream()
            if self.stream is None:
                return
            msg = self.format(record)
            self.stream.write(msg + "\n")
            self.stream.flush()
        except Exception:
            pass
        finally:
            if self.stream is not None:
                try:
                    self.stream.close()
                except Exception:
                    pass
                self.stream = None


class Logger:
    def __init__(self, name="AppLogger", log_dir="logs"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        # 避免重复添加 handler
        if self.logger.handlers:
            return

        fmt = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = DailyFileHandler(log_dir=log_dir)
        file_handler.setFormatter(fmt)
        file_handler.setLevel(logging.DEBUG)
        self.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(fmt)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)

    # ---------- 基础日志 ----------
    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def debug(self, msg):
        self.logger.debug(msg)

    # ---------- 前端操作日志（含测试人员信息） ----------
    def action(self, tester, action, detail=None):
        """记录用户操作：谁（tester）做了什么动作（action），附带详情（detail）。"""
        who = tester or "未登录用户"
        if detail:
            try:
                detail_str = str(detail)
            except Exception:
                detail_str = "<unserializable detail>"
            self.info(f"[操作] 用户={who} | 动作={action} | 详情={detail_str}")
        else:
            self.info(f"[操作] 用户={who} | 动作={action}")

    # ---------- 测试结果日志 ----------
    def test_result(self, tester, test_type, result, ip=None, extra=None):
        """记录测试结果。"""
        who = tester or "未登录用户"
        msg = (
            f"[测试结果] 用户={who} | 测试项={test_type} | 结果={result}"
        )
        if ip:
            msg += f" | 机器人IP={ip}"
        if extra:
            try:
                msg += f" | 附加={str(extra)}"
            except Exception:
                pass
        self.info(msg)

    # ---------- 登录/登出 ----------
    def login(self, tester, ip_address=None, success=True):
        status = "成功" if success else "失败"
        self.info(
            f"[登录] 用户={tester or '匿名'} | 状态={status}"
            + (f" | 来源IP={ip_address}" if ip_address else "")
        )


# 模块级默认实例，方便各路由 `from log import log`
log = Logger()
