# -*- coding: utf-8 -*-
import paramiko
import time
import threading
import re


class SingleTopicReader:
    """单个Topic采集器"""

    def __init__(self, ip, topic, username="youibot", password="youibot", interval=3):
        self.ip = ip
        self.topic = topic
        self.username = username
        self.password = password
        self.interval = interval

        self.running = False
        self.thread = None
        self.last_data = None

    def _connect(self):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.ip, username=self.username, password=self.password, timeout=10)
        shell = client.invoke_shell()
        return client, shell

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        try:
            client, shell = self._connect()

            while self.running:

                cmd = f"timeout {self.interval} rostopic echo -n 1 {self.topic}\n"
                shell.send(cmd)

                output = self._recv_output(shell, timeout=self.interval + 1)

                if output:
                    data = self._parse_data(output)

                    if data is not None:
                        self.last_data = data

                time.sleep(self.interval)

        except Exception:
            pass
        finally:
            if 'client' in locals():
                client.close()

    def _recv_output(self, shell, timeout=3):
        output = ""
        start_time = time.time()

        while time.time() - start_time < timeout:
            if shell.recv_ready():
                data = shell.recv(4096).decode(errors="ignore")
                output += data
            else:
                time.sleep(0.05)

        return output.strip()

    # ------------------------
    # 新增：读取一帧
    # ------------------------

    def read_one_frame(self, timeout=5):
        """
        在 timeout 秒内获取一帧数据
        返回最后成功解析的数据
        """

        end_time = time.time() + timeout
        last_data = None

        try:
            client, shell = self._connect()

            while time.time() < end_time:

                cmd = f"timeout 1 rostopic echo -n 1 {self.topic}\n"
                shell.send(cmd)

                output = self._recv_output(shell, timeout=2)

                if output:
                    data = self._parse_data(output)

                    if data is not None:
                        last_data = data

        except Exception:
            pass
        finally:
            if 'client' in locals():
                client.close()

        return last_data

    # ------------------------
    # 数据解析
    # ------------------------

    def _parse_data(self, text):

        if "/ks114_sensor/ks114_data" in self.topic:
            return self._parse_ks114(text)

        if "/tfmini_sensor/tfmini_data" in self.topic:
            return self._parse_tfmini(text)

        if "/imu_data" in self.topic:
            return self._parse_imu(text)

        if "/sensors/encoder" in self.topic:
            return self._parse_encoder(text)

        if "/odom" in self.topic:
            return self._parse_odom(text)

        return None

    def _parse_ks114(self, text):

        match = re.search(r'distance:\s*\[([0-9,\s]+)\]', text)
        if not match:
            return None

        nums = match.group(1).split(",")

        return [int(n.strip()) for n in nums]

    def _parse_tfmini(self, text):

        match = re.search(r'distance:\s*\[([0-9,\s]+)\]', text)
        if not match:
            return None

        nums = match.group(1).split(",")

        return [int(n.strip()) for n in nums]

    def _parse_encoder(self, text):
        """
        encoder: [-1400034440, 570826979]
        """

        match = re.search(r'encoder:\s*\[([-0-9,\s]+)\]', text)

        if not match:
            return None

        nums = match.group(1).split(",")

        return [int(n.strip()) for n in nums]

    def _parse_imu(self):
        pass

    def _parse_imu(self, text):
        """
        提取 orientation 的 x y z w
        """

        pattern = r'orientation:\s*\n\s*x:\s*([-0-9.e]+)\s*\n\s*y:\s*([-0-9.e]+)\s*\n\s*z:\s*([-0-9.e]+)\s*\n\s*w:\s*([-0-9.e]+)'
        match = re.search(pattern, text)

        if not match:
            return None

        return {
            "x": float(match.group(1)),
            "y": float(match.group(2)),
            "z": float(match.group(3)),
            "w": float(match.group(4))
        }

    def _parse_odom(self, text):
        """
        提取 odom position
        """

        pattern = r'position:\s*\n\s*x:\s*([-0-9.e]+)\s*\n\s*y:\s*([-0-9.e]+)\s*\n\s*z:\s*([-0-9.e]+)'
        match = re.search(pattern, text)

        if not match:
            return None

        return {
            "x": float(match.group(1)),
            "y": float(match.group(2)),
            "z": float(match.group(3))
        }

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)


class RosTopicReader:
    """多Topic管理"""

    TOPICS = [
        "/ks114_sensor/ks114_data",
        "/tfmini_sensor/tfmini_data",
        "/imu_data",
        "/sensors/encoder",
        "/odom"
    ]

    INTERVAL = 1
    USERNAME = "youibot"
    PASSWORD = "youibot"

    def __init__(self, ip):

        self.ip = ip

        self.topic_readers = {
            t: SingleTopicReader(
                ip,
                t,
                self.USERNAME,
                self.PASSWORD,
                self.INTERVAL
            )
            for t in self.TOPICS
        }

    # ------------------------
    # 新增：读取CPU频率
    # ------------------------

    def _read_cpu_hz(self):

        try:

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.ip, username=self.USERNAME, password=self.PASSWORD, timeout=10)

            stdin, stdout, stderr = client.exec_command('cat /proc/cpuinfo | grep "cpu MHz"')

            text = stdout.read().decode()

            client.close()

            matches = re.findall(r'cpu MHz\s*:\s*([0-9.]+)', text)

            return [float(x) for x in matches]

        except Exception:
            return None

    # 持续采集模式
    def start(self):

        for reader in self.topic_readers.values():
            reader.start()

    def stop(self):

        for reader in self.topic_readers.values():
            reader.stop()

    def get_all_data(self):

        result = {}

        for topic, reader in self.topic_readers.items():

            if "ks114_sensor" in topic:
                key = "ks114_sensor"

            elif "tfmini_sensor" in topic:
                key = "tfmini_sensor"

            elif "imu_data" in topic:
                key = "imu"

            elif "encoder" in topic:
                key = "encoder"

            elif "odom" in topic:
                key = "odom"

            else:
                key = topic

            result[key] = reader.last_data

        result["scan_1"] = "大量数据"

        # 新增CPU频率
        result["cpu_hz"] = self._read_cpu_hz()

        return result

    # ------------------------
    # 新增：获取一帧
    # ------------------------

    def get_one_frame(self, timeout=5):

        result = {}
        threads = []

        def worker(topic, reader):
            data = reader.read_one_frame(timeout)

            if "ks114_sensor" in topic:
                key = "ks114_sensor"
            elif "tfmini_sensor" in topic:
                key = "tfmini_sensor"
            elif "imu_data" in topic:
                key = "imu_data"
            elif "encoder" in topic:
                key = "encoder"
            elif "odom" in topic:
                key = "odom"
            else:
                key = topic

            result[key] = data

        for topic, reader in self.topic_readers.items():
            t = threading.Thread(target=worker, args=(topic, reader))
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout)

        # 添加雷达数据
        result["scan_1"] = "大量数据"

        # 新增CPU频率
        result["cpu_hz"] = self._read_cpu_hz()

        return result


# ------------------- 示例 -------------------

if __name__ == "__main__":

    reader = RosTopicReader("192.168.16.64")

    # 获取一帧数据
    data = reader.get_one_frame(timeout=5)

    print("one frame:", data)

    # # 持续采集示例
    # reader.start()

    # try:
    #     while True:
    #         time.sleep(0.5)

    #         sensor_data = reader.get_all_data()

    #         print(sensor_data)

    # except KeyboardInterrupt:
    #     reader.stop()