# -*- coding: utf-8 -*-
"""
跨平台（Win→Ubuntu）SSH远程并行延迟采集
- IP            -> 使用 ping，取第一次有效 time=xxx ms
- IP:PORT       -> 使用 telnet，若输出含 Trying 视为成功，返回固定 0.1 ms
"""

import paramiko
import time
import threading
import re


class SinglePingReader:
    """单个目标延迟采集器（独立SSH通道 + 第一次有效结果）"""
    duration = 3

    def __init__(self, ssh_ip, target, username="youibot", password="youibot"):
        self.ssh_ip = ssh_ip
        self.target = target
        self.username = username
        self.password = password
        self.last_delay = None
        self.done = threading.Event()
        self.thread = None

        self.target_ip, self.target_port = self._parse_target(target)

    @staticmethod
    def _parse_target(target: str):
        m = re.match(r"^\s*([^:]+):(\d+)\s*$", target)
        if m:
            ip = m.group(1).strip()
            port = int(m.group(2))
            return ip, port
        return target.strip(), None

    def start(self):
        """启动独立线程执行采集"""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        client = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                self.ssh_ip,
                username=self.username,
                password=self.password,
                timeout=8
            )

            if self.target_port is not None:
                self._run_telnet(client)
            else:
                self._run_ping(client)

            if self.last_delay is None:
                print(f"WARN [{self.target}] 超时未获取到有效延迟数据")

        except Exception as e:
            print(f"ERROR [{self.target}] 出错: {e}")
        finally:
            try:
                if client:
                    client.close()
            except Exception:
                pass
            self.done.set()
            print(f"END [{self.target}] 任务结束")

    def _run_ping(self, client):
        """执行 ping 命令并提取第一次有效延迟"""
        cmd = f"ping -i 0.5 -c 10 {self.target_ip}"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)

        start_time = time.time()
        while time.time() - start_time < self.duration:
            line = stdout.readline()
            if not line:
                break

            match = re.search(r"time=([\d.]+)\s*ms", line)
            if match:
                self.last_delay = float(match.group(1))
                print(f"PING [{self.target}] 首次延迟: {self.last_delay:.3f} ms")
                break

    def _run_telnet(self, client):
        cmd = f"telnet {self.target_ip} {self.target_port}"
        stdin, stdout, stderr = client.exec_command(cmd, get_pty=True)

        chan = stdout.channel
        chan.settimeout(0.2)

        start_time = time.time()
        buffer = ""

        while time.time() - start_time < self.duration:
            if chan.recv_ready():
                chunk = chan.recv(4096).decode("utf-8", errors="ignore")
                buffer += chunk

                if "Connected" in buffer:
                    self.last_delay = 0.1
                    print(f"TELNET [{self.target}] 检测到 Connected，返回固定延迟: 0.1 ms")
                    break
            else:
                time.sleep(0.05)


class PingManager:
    """管理多目标的并行采集"""
    duration = 3

    def __init__(self, ssh_ip, targets, username="youibot", password="youibot"):
        self.ssh_ip = ssh_ip
        self.targets = targets
        self.username = username
        self.password = password
        self.readers = {
            t: SinglePingReader(ssh_ip, t, username, password)
            for t in targets
        }

    def run_all(self):
        """并行执行所有任务"""
        print(f"INFO SSH主机 {self.ssh_ip} 准备并行处理 {len(self.targets)} 个目标...")

        for reader in self.readers.values():
            reader.start()

        for reader in self.readers.values():
            reader.done.wait()

        results = {
            target: (f"{r.last_delay:.3f} ms" if r.last_delay is not None else None)
            for target, r in self.readers.items()
        }
        print("INFO 所有任务完成")
        return results


# ------------------- 示例 -------------------
if __name__ == "__main__":
    manager = PingManager(
        ssh_ip="192.168.16.25",
        targets=[
            "192.168.0.8",
            "192.168.2.63",
            "192.168.2.250",
            "192.168.0.100:8081",  # 有端口 -> 走telnet
            "192.168.2.2:8083",  

        ],
    )

    result = manager.run_all()
    print("\n📈 最终延迟结果:")
    print(result)