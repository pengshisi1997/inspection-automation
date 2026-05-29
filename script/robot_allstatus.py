# -*- coding: utf-8 -*-
"""
单次获取 ROS Topic 一帧数据（Win→Ubuntu 跨平台）
支持功能：
1. 自动 SSH 连接
2. 获取 topic 一帧数据
3. 可传入字段名，返回 1（True）或 0（False）
4. 自动过滤 Ubuntu 登录欢迎信息
"""

import paramiko
import time
import re


class SingleTopicOnceReader:
    """单次获取 Topic 一帧数据"""
    def __init__(self, ip, topic, username="youibot", password="youibot", timeout=5):
        self.ip = ip
        self.topic = topic
        self.username = username
        self.password = password
        self.timeout = timeout
        self.recv_interval = 0.02

    def _connect(self):
        """创建 SSH 连接"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.ip, username=self.username, password=self.password, timeout=10)

        shell = client.invoke_shell()
        time.sleep(0.1)  # 给 shell 初始化
        return client, shell

    def _recv_output(self, shell, timeout=3):
        """读取 SSH 输出"""
        output = ""
        start = time.time()

        while time.time() - start < timeout:
            if shell.recv_ready():
                output += shell.recv(4096).decode(errors="ignore")
            else:
                time.sleep(self.recv_interval)

        return output.strip()

    def _recv_until_field(self, shell, field, timeout):
        output = ""
        start = time.time()
        # 尝试多种可能的格式
        patterns = [
            rf"{re.escape(field)}:\s*(True|False|\d+)",
            rf"bit\.{re.escape(field)}:\s*(True|False|\d+)",
            rf"bit\.{re.escape(field)}:(True|False|\d+)",
            rf"{re.escape(field)}:(True|False|\d+)"
        ]

        while time.time() - start < timeout:
            if shell.recv_ready():
                output += shell.recv(4096).decode(errors="ignore")
                # 检查是否匹配任何一个模式
                for pattern in patterns:
                    if re.search(pattern, output):
                        return output.strip()
            else:
                time.sleep(self.recv_interval)

        return output.strip()

    def _parse_field(self, text, field):
        """
        从 rostopic echo 输出中解析一个字段的值
        支持格式：
            field: True
            field: False
            field: 1
            field: 0
            bit.field:0
            bit.field:1
        """
        # 尝试多种可能的格式
        patterns = [
            rf"{field}:\s*(True|False|\d+)",
            rf"bit\.{field}:\s*(True|False|\d+)",
            rf"bit\.{field}:(True|False|\d+)",
            rf"{field}:(True|False|\d+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                break

        if not match:
            return None

        value = match.group(1)
        if value == "True":
            return 1    
        elif value == "False":
            return 0        
        else:
            return int(value)

    def _clean_output(self, output):
        """
        清理 Ubuntu 登录欢迎内容，只保留 Topic 数据
        只要找到 header: 视为数据开始
        """
        if "header:" in output:
            return output[output.index("header:"):]
        return output

    def get_one_frame(self, field=None):
        """
        获取 topic 一帧数据
        参数:
            field=None → 返回完整数据字符串
            field="xxx" → 返回数字 0/1
        """
        try:
            client, shell = self._connect()
            print(f"已连接到 {self.ip}")

            while shell.recv_ready():
                shell.recv(4096)

            cmd = f"timeout {self.timeout} rostopic echo -n 1 {self.topic}\n"
            shell.send(cmd)

            if field:
                output = self._recv_until_field(shell, field=field, timeout=self.timeout + 0.5)
            else:
                output = self._recv_output(shell, timeout=self.timeout + 0.5)
            output = self._clean_output(output).strip()

            print("已获取 Topic 数据")
            print(f"原始数据: {output[:200] if len(output) > 200 else output}")

            # 如果请求某个字段，则解析
            if field:
                result = self._parse_field(output, field)
                print(f"字段 {field} = {result}")
                return result

            # 返回完整原始数据
            return output

        except Exception as e:
            print(f"出错: {e}")
            return None

        finally:
            if "client" in locals():
                client.close()
            print("SSH 已关闭")


# ------------------- 示例 -------------------
if __name__ == "__main__":
    reader = SingleTopicOnceReader(
        ip="192.168.16.39",
        topic="/robot/all_status",
    )

    # 获取一个字段值（True/False → 1/0）
    v = reader.get_one_frame("stop_button")
    print("\n返回字段结果：", v)

    # 获取完整数据
    # raw = reader.get_one_frame()
    # print("\n返回完整数据：")
    # print(raw)
