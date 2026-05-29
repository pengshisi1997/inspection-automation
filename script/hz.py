# -*- coding: utf-8 -*-
import paramiko
import time
import re

class RosTopicHzReader:
    """
    使用 SSH invoke_shell 获取 ROS topic 的频率（rostopic hz）。
    只获取第一帧的频率，超时则返回 None。
    用户名和密码固定为 'youibot'
    超时时间固定为 3 秒
    """
    TIMEOUT = 3  # 固定超时时间（秒）

    def __init__(self, ssh_ip):
        """
        初始化 SSH 参数
        :param ssh_ip: 远程 Ubuntu IP
        """
        self.ssh_ip = ssh_ip
        self.ssh_user = "youibot"
        self.ssh_password = "youibot"
        self.ssh_port = 22
        self.client = None

    def connect(self):
        """建立 SSH 连接"""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            hostname=self.ssh_ip,
            port=self.ssh_port,
            username=self.ssh_user,
            password=self.ssh_password,
            timeout=10
        )

    def close(self):
        """关闭 SSH 连接"""
        if self.client:
            self.client.close()

    def get_topic_hz(self, topic_name):
        """
        获取指定 topic 的频率
        :param topic_name: ROS topic 名称，例如 '/bms/can'
        :return: Hz（浮点数）或者 None
        """
        if not self.client:
            self.connect()

        shell = self.client.invoke_shell()
        shell.settimeout(self.TIMEOUT)

        # 启动 rostopic hz
        shell.send(f"rostopic hz {topic_name}\n")

        start_time = time.time()
        buffer = ""

        while True:
            # 超时退出
            if time.time() - start_time > self.TIMEOUT:
                return None

            try:
                if shell.recv_ready():
                    data = shell.recv(1024).decode('utf-8')
                    buffer += data

                    # rostopic hz 输出类似：
                    # average rate: 10.123
                    match = re.search(r"average rate:\s*([\d\.]+)", buffer)
                    if match:
                        hz = float(match.group(1))
                        return hz
            except Exception:
                continue

# ===== 新增管理类 =====
class RosHzReader:
    """
    批量获取多个 topic 的频率
    """
    def __init__(self, ssh_ip, topic_list):
        """
        :param ssh_ip: 远程 Ubuntu IP
        :param topic_list: ROS topic 列表，例如 ['/bms/can', '/odom']
        """
        self.ssh_ip = ssh_ip
        self.topic_list = topic_list

    def get_all_topics_hz(self):
        """
        遍历 topic 列表获取频率
        :return: dict，格式 {topic_name: hz 或 None}
        """
        result = {}
        reader = RosTopicHzReader(self.ssh_ip)
        try:
            for topic in self.topic_list:
                hz = reader.get_topic_hz(topic)
                # 统一返回带 Hz 单位
                result[topic] = f"{hz} Hz" if hz is not None else None
        finally:
            reader.close()
        print(000000000000)
        print(result)
        return result

# ===== 示例使用 =====
if __name__ == "__main__":
    topics = ["/bms_data", "/odom", "/imu_data"]
    manager = RosHzReader("192.168.16.37", topics)
    result = manager.get_all_topics_hz()
    print("所有 topic 频率结果:")
    print(result)
