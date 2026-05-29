# -*- coding: utf-8 -*-
import paramiko
import time
import threading
import re


class LidarFieldReader:

    def __init__(self, ip, username="youibot", password="youibot", interval=0.2, recv_timeout=0.8):

        self.ip = ip
        self.username = username
        self.password = password
        self.topic = "/front/lidarField"

        self.interval = interval
        self.recv_timeout = recv_timeout
        self.recv_interval = 0.01

        self.running = False
        self.thread = None

        self.last_data = None

    def _connect(self):

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(
            self.ip,
            username=self.username,
            password=self.password,
            timeout=10
        )

        shell = client.invoke_shell()
        time.sleep(0.1)

        return client, shell

    def _recv_output(self, shell, timeout=3):

        output = ""
        start = time.time()

        while time.time() - start < timeout:

            if shell.recv_ready():

                data = shell.recv(4096).decode(errors="ignore")

                output += data

            else:
                time.sleep(self.recv_interval)

        return output

    def _recv_until_data(self, shell, timeout):

        output = ""
        start = time.time()

        while time.time() - start < timeout:

            if shell.recv_ready():

                data = shell.recv(4096).decode(errors="ignore")
                output += data

                if re.search(r"data:\s*(\d+)", output):
                    return output

            else:
                time.sleep(self.recv_interval)

        return output

    def _parse_data(self, text):

        match = re.search(r"data:\s*(\d+)", text)

        if match:
            return int(match.group(1))

        return None

    # ------------------------
    # 持续采集线程
    # ------------------------

    def _run(self):

        try:

            client, shell = self._connect()

            while self.running:
                loop_start = time.time()

                while shell.recv_ready():
                    shell.recv(4096)

                cmd = f"rostopic echo -n 1 {self.topic}\n"

                shell.send(cmd)

                output = self._recv_until_data(shell, timeout=self.recv_timeout)

                value = self._parse_data(output)

                if value is not None:
                    self.last_data = value

                elapsed = time.time() - loop_start
                if elapsed < self.interval:
                    time.sleep(self.interval - elapsed)

        except Exception as e:
            print("reader error:", e)

        finally:
            if 'client' in locals():
                client.close()

    # ------------------------
    # 启动持续采集
    # ------------------------

    def start(self):

        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self._run,
            daemon=True
        )

        self.thread.start()

    # ------------------------
    # 停止采集
    # ------------------------

    def stop(self):

        self.running = False

        if self.thread:
            self.thread.join(timeout=2)

    # ------------------------
    # 读取一帧
    # ------------------------

    def read_one_frame(self, timeout=5):

        try:

            client, shell = self._connect()

            cmd = f"rostopic echo -n 1 {self.topic}\n"

            shell.send(cmd)

            output = self._recv_until_data(shell, timeout=timeout)

            value = self._parse_data(output)

            client.close()

            return value

        except Exception as e:
            print("read error:", e)

            return None


# ---------------- 示例 ----------------

if __name__ == "__main__":

    reader = LidarFieldReader("192.168.16.25")

    # 启动持续采集
    reader.start()

    try:

        while True:

            print("lidarField:", reader.last_data)

            time.sleep(0.5)

    except KeyboardInterrupt:

        reader.stop()
