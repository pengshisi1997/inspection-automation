import json
import re
import time

import paramiko
import requests


class SerialATVersionReader:
    def __init__(self, username="youibot", password="youibot"):
        self.port = 22
        self.username = username
        self.password = password
        self.sudo_password = password
        self.serial_port = "/dev/ttyS3"
        self.timeout = 2
        self.remote_path = "/home/youibot/tmp.py"
        self.ssh = None

    def generate_script_content(self, at_commands):
        # 支持多个命令
        commands_list = at_commands if isinstance(at_commands, list) else [at_commands]
        commands_json = json.dumps(commands_list)
        return f'''# -*- coding: utf-8 -*-
import serial
import time
import json


def main():
    port = "/dev/ttyS3"
    baudrate = 115200
    timeout = 2

    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
    except serial.SerialException as exc:
        print("无法打开串行端口: {{}}".format(exc))
        return

    responses = {{}}
    commands = {commands_json}

    try:
        for command in commands:
            ser.write((command + "\\r\\n").encode("utf-8"))
            time.sleep(1)
            data_received = ser.read(ser.inWaiting()).decode("utf-8", errors="ignore").strip()
            responses[command] = data_received if data_received else None
    finally:
        ser.close()
        print(json.dumps(responses))


if __name__ == "__main__":
    main()
'''

    def connect(self, host_ip, port=None):
        if self.ssh is not None:
            return

        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(host_ip, port or self.port, self.username, self.password)
        except Exception:
            self.ssh = None
            raise

    def close(self):
        if self.ssh is not None:
            self.ssh.close()
            self.ssh = None

    def release_serial_port(self):
        sudo_cmd = f"sudo -S fuser -k {self.serial_port}"
        stdin, stdout, stderr = self.ssh.exec_command(sudo_cmd)
        stdin.write(self.sudo_password + "\n")
        stdin.flush()
        stdout.read()
        stderr.read()

    def upload_script(self, at_commands):
        script_content = self.generate_script_content(at_commands)
        sftp = self.ssh.open_sftp()
        try:
            with sftp.file(self.remote_path, "w") as remote_file:
                remote_file.write(script_content)
        finally:
            sftp.close()

    def execute_remote_script(self):
        stdin, stdout, stderr = self.ssh.exec_command(f"python {self.remote_path}")
        output = stdout.read().decode("utf-8", errors="ignore")
        error = stderr.read().decode("utf-8", errors="ignore")
        if error.strip():
            raise RuntimeError(error.strip())
        return output

    def extract_version(self, response):
        return None

    def parse_release_version(self, text):
        json_match = re.search(r"({.*})", text, re.S)
        if not json_match:
            return None

        data = json.loads(json_match.group(1))
        # 如果是多个命令，返回最后一个命令的响应
        responses = list(data.values())
        response = responses[-1] if responses else None
        if not response:
            return None

        return self.extract_version(response)

    def execute_lighting(self, host_ip, at_command):
        try:
            self.connect(host_ip)
            self.release_serial_port()
            self.upload_script(at_command)
            output = self.execute_remote_script()
            return self.parse_release_version(output)
        finally:
            self.close()
    
    def execute_multiple_commands(self, host_ip, at_commands):
        """执行多个AT命令，返回最后一个命令的版本信息"""
        try:
            self.connect(host_ip)
            self.release_serial_port()
            self.upload_script(at_commands)
            output = self.execute_remote_script()
            return self.parse_release_version(output)
        finally:
            self.close()


class IO_base(SerialATVersionReader):
    def extract_version(self, response):
        version_match = re.search(r"swVer=(\d+)", response)
        if version_match:
            return version_match.group(1)
        return None


class Rcc_base(SerialATVersionReader):
    def extract_version(self, response):
        version_match = re.search(r"release version=([\d.]+)", response)
        if version_match:
            return version_match.group(1)

        software_match = re.search(r"Software V\s*([\d.]+)", response)
        if software_match:
            return software_match.group(1)
        
        # 支持 [D]Software V2.02 compile:May 格式，提取 2.02（去掉前面的 V）
        tw_software_match = re.search(r"\[D\]Software V([\d.]+)", response)
        if tw_software_match:
            return tw_software_match.group(1)

        return None


class SSHJumpReader:
    FILE_PATH = ".Mirror_system.txt"

    def __init__(
        self,
        jump_ip,
        target_ip="192.168.2.90",
        username="youibot",
        password="youibot",
        timeout=10,
    ):
        self.jump_ip = jump_ip
        self.target_ip = target_ip
        self.username = username
        self.password = password
        self.timeout = timeout
        self.jump_client = None
        self.target_client = None

    def _connect(self):
        self.jump_client = paramiko.SSHClient()
        self.jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.jump_client.connect(
            hostname=self.jump_ip,
            username=self.username,
            password=self.password,
            timeout=self.timeout,
        )

        channel = self.jump_client.get_transport().open_channel(
            "direct-tcpip",
            dest_addr=(self.target_ip, 22),
            src_addr=("127.0.0.1", 0),
        )

        self.target_client = paramiko.SSHClient()
        self.target_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.target_client.connect(
            hostname=self.target_ip,
            username=self.username,
            password=self.password,
            sock=channel,
            timeout=self.timeout,
        )

    def _close(self):
        if self.target_client:
            self.target_client.close()
        if self.jump_client:
            self.jump_client.close()

    def _read_file(self):
        stdin, stdout, stderr = self.target_client.exec_command(f"cat {self.FILE_PATH}")
        error = stderr.read().decode("utf-8").strip()
        if error:
            raise RuntimeError(f"读取错误: {error}")
        return stdout.read().decode("utf-8", errors="ignore").strip()

    @classmethod
    def run(cls, jump_ip, **kwargs):
        reader = cls(jump_ip, **kwargs)
        try:
            reader._connect()
            return reader._read_file()
        finally:
            reader._close()


class SSHJumpCommandRunner:
    def __init__(
        self,
        jump_ip,
        target_ip="192.168.2.90",
        username="youibot",
        password="youibot",
        timeout=10,
    ):
        self.jump_ip = jump_ip
        self.target_ip = target_ip
        self.username = username
        self.password = password
        self.timeout = timeout
        self.jump_client = None
        self.target_client = None

    def _connect(self):
        self.jump_client = paramiko.SSHClient()
        self.jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.jump_client.connect(
            hostname=self.jump_ip,
            username=self.username,
            password=self.password,
            timeout=self.timeout,
        )

        channel = self.jump_client.get_transport().open_channel(
            "direct-tcpip",
            dest_addr=(self.target_ip, 22),
            src_addr=("127.0.0.1", 0),
        )

        self.target_client = paramiko.SSHClient()
        self.target_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.target_client.connect(
            hostname=self.target_ip,
            username=self.username,
            password=self.password,
            sock=channel,
            timeout=self.timeout,
        )

    def _close(self):
        if self.target_client:
            self.target_client.close()
        if self.jump_client:
            self.jump_client.close()

    def run_command(self, command):
        try:
            self._connect()
            stdin, stdout, stderr = self.target_client.exec_command(command)
            output = stdout.read().decode("utf-8", errors="ignore")
            error = stderr.read().decode("utf-8", errors="ignore").strip()
            if error:
                raise RuntimeError(error)
            return output
        finally:
            self._close()


class MirrorSystemReader:
    DEFAULT_FIELDS = {
        "MS": ["pilot_version", "compass_version", "rcc_base_version", "mirror_system"],
        "MR": ["pilot_version", "compass_version", "mirror_system", "rws_version"],
        "TW": ["pilot_version", "rcc_base_version", "robot_version", "rws_version", "mirror_system", "youiscript_version", "mos_version"],
        "X310": ["pilot_version", "compass_version", "rcc_base_version", "mirror_system"],
        "X320": ["pilot_version", "compass_version", "rcc_base_version", "mirror_system"],
        "HSR": ["pilot_version", "compass_version", "mirror_system", "mos_version_hsr", "mirror_system_hsr"],
    }

    def __init__(self, model, username="youibot", password="youibot"):
        if not model:
            raise ValueError("MirrorSystemReader 需要传入机型")

        self.model = str(model).upper()
        self.username = username
        self.password = password

    def remove_ansi(self, text):
        ansi_escape = re.compile(
            r"""
            \x1B
            \[
            [0-?]*
            [ -/]*
            [@-~]
        """,
            re.VERBOSE,
        )
        return ansi_escape.sub("", text)

    def _ssh_connect(self, ip, port=22, timeout=5):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=ip,
            port=port,
            username=self.username,
            password=self.password,
            timeout=timeout,
        )
        return ssh

    def _run_command(self, ip, command, port=22, timeout=5):
        ssh = None
        try:
            ssh = self._ssh_connect(ip, port=port, timeout=timeout)
            stdin, stdout, stderr = ssh.exec_command(command)
            output = stdout.read().decode("utf-8", errors="ignore")
            error = stderr.read().decode("utf-8", errors="ignore").strip()
            return output.strip(), error
        finally:
            if ssh is not None:
                ssh.close()

    def _list_home_entries(self, ip, port=22):
        try:
            output, error = self._run_command(ip, "cd /home/youibot && ls -1", port=port)
            if error:
                return f"❌ 查询失败:\n{error}"
            return [line.strip() for line in output.splitlines() if line.strip()]
        except Exception as exc:
            return f"🚨 目录读取失败: {exc}"

    def _find_keyword_entry(
        self,
        ip,
        keyword,
        *,
        port=22,
        prefer_non_zip=False,
        zip_only=False,
        missing_message=None,
    ):
        entries = self._list_home_entries(ip, port=port)
        if isinstance(entries, str):
            return entries

        matches = [entry for entry in entries if keyword.lower() in entry.lower()]
        if zip_only:
            matches = [entry for entry in matches if entry.lower().endswith(".zip")]

        if prefer_non_zip:
            non_zip_matches = [entry for entry in matches if not entry.lower().endswith(".zip")]
            if len(non_zip_matches) == 1:
                return non_zip_matches[0]
            if len(non_zip_matches) > 1:
                return (
                    f"⚠️ 检测到多个版本文件（{len(non_zip_matches)} 个），需人工处理:\n"
                    + "\n".join(non_zip_matches)
                )

        if not matches:
            return missing_message or f"⚠️ 未检测到包含 {keyword} 的版本文件，需人工处理"

        if len(matches) == 1:
            result = matches[0]
            if result.lower().endswith(".zip"):
                return result[:-4]
            return result

        return f"⚠️ 检测到多个版本文件（{len(matches)} 个），需人工处理:\n" + "\n".join(matches)

    def read_mirror_file(self, ip):
        try:
            output, error = self._run_command(ip, "cat ~/.Mirror_system.txt")
            if error:
                return f"❌ 读取文件出错:\n{error}"
            return output
        except Exception as exc:
            return f"🚨 SSH连接失败: {exc}"

    def get_compass_version_from_ads(self, ip):
        return self._find_keyword_entry(
            ip,
            "compass",
            zip_only=True,
            missing_message="⚠️ 未检测到 Compass 版本文件，需人工处理",
        )

    def read_mirror_file_from_mos(self, ip):
        try:
            return SSHJumpReader.run(
                jump_ip=ip,
                target_ip="192.168.2.90",
                username=self.username,
                password=self.password,
            )
        except RuntimeError as exc:
            return f"❌ 读取 MOS 镜像文件失败: {exc}"
        except Exception as exc:
            return f"🚨 二次 SSH 失败: {exc}"

    def get_mos_version(self, ip):
        try:
            output, error = self._run_command(ip, "cat /mos/data/version.info")
            if error:
                return f"❌ 读取 version.info 出错:\n{error}"
            for line in output.splitlines():
                clean = self.remove_ansi(line).strip()
                if clean.startswith("VERSION:"):
                    return clean.replace("VERSION:", "").strip()
            return None
        except Exception as exc:
            return f"🚨 读取 version.info 失败: {exc}"

    def get_mos_version_hsr(self, ip):
        try:
            output, error = self._run_command(ip, "cat /mos/data/version.info", port=23)
            if error:
                return f"❌ 读取 version.info 出错:\n{error}"
            for line in output.splitlines():
                clean = self.remove_ansi(line).strip()
                if clean.startswith("VERSION:"):
                    return clean.replace("VERSION:", "").strip()
            return None
        except Exception as exc:
            return f"🚨 读取 version.info 失败: {exc}"

    def read_mirror_file_hsr(self, ip):
        try:
            output, error = self._run_command(ip, "cat ~/.Mirror_system.txt", port=23)
            if error:
                return f"❌ 读取文件出错:\n{error}"
            return output
        except Exception as exc:
            return f"🚨 SSH连接失败: {exc}"

    def get_pilot_version(self, ip):
        if self.model in ("TW", "EX"):
            return self.get_pilot_version_tw(ip)
        if self.model == "MR":
            return self._find_keyword_entry(
                ip,
                "YouiPilot-release",
                prefer_non_zip=True,
                missing_message="⚠️ 未检测到 YouiPilot-release 版本文件，需人工处理",
            )
        if self.model == "HSR":
            return self.get_pilot_version_hsr(ip)

        try:
            url = f"http://{ip}:8080/api/v3/logo"
            url = f"http://{ip}:8080/api/v3/logo/updateVersionInfo"

            resp = requests.get(url, timeout=5)
            if resp.status_code != 200:
                return f"❌ 请求失败: HTTP {resp.status_code}"

            data = resp.json()
            agv_version = data.get("agvVersion")
            if not agv_version:
                return "⚠️ 未检测到 agvVersion 字段，需人工处理"
            return agv_version
        except requests.exceptions.RequestException as exc:
            return f"❌ 请求异常: {exc}"
        except Exception as exc:
            return f"🚨 pilot_version 获取失败: {exc}"
    
    def get_pilot_version_hsr(self, ip):
        try:
            import paramiko
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, 22, "youibot", "youibot", timeout=10)
            
            stdin, stdout, stderr = ssh.exec_command("echo youibot | sudo -S docker ps")
            output = stdout.read().decode('utf-8', errors='ignore')
            error = stderr.read().decode('utf-8', errors='ignore')
            
            ssh.close()
            
            if error and "password" not in error.lower() and "密码" not in error:
                return f"❌ 获取 pilot_version 失败:\n{error}"
            
            for line in output.splitlines():
                if "youipilot" in line.lower():
                    parts = line.split()
                    if len(parts) >= 2:
                        image_name = parts[1]
                        if ":" in image_name:
                            version = image_name.split(":")[1]
                            if "feature_" in version:
                                version = version.split("feature_")[1]
                            if "-x86_64-running" in version:
                                return version.split("-x86_64-running")[0]
                            return version
            
            return "⚠️ 未检测到 youipilot 容器"
        except paramiko.AuthenticationException:
            return "❌ SSH认证失败"
        except paramiko.SSHException as exc:
            return f"❌ SSH连接失败: {exc}"
        except Exception as exc:
            return f"🚨 HSR pilot_version 获取失败: {exc}"

    def get_compass_version_hsr(self, ip):
        try:
            output, error = self._run_command(ip, "ls -lt /home/youibot/")
            if error:
                return f"❌ 获取目录列表失败:\n{error}"

            compass_folders = []
            compass_zips = []
            
            for line in output.splitlines():
                line = self.remove_ansi(line).strip()
                if not line:
                    continue
                filename = line.split()[-1]
                if "compass" not in filename.lower():
                    continue
                if filename.lower().endswith(".zip"):
                    compass_zips.append(filename[:-4])
                else:
                    compass_folders.append(filename)

            if compass_folders:
                return compass_folders[0]
            
            if compass_zips:
                return compass_zips[0]

            return "⚠️ 未检测到 Compass 版本文件，需人工处理"
        except Exception as exc:
            return f"🚨 HSR compass_version 获取失败: {exc}"

    def get_pilot_version_tw(self, ip):
        try:
            output, error = self._run_command(
                ip,
                "echo youibot | sudo -S docker ps --format '{{.Image}}'",
            )
            if error and "password" not in error.lower() and "密码" not in error:
                return f"❌ 获取 pilot_version 失败:\n{error}"

            for line in output.splitlines():
                if "youipilot:" not in line.lower():
                    continue
                match = re.search(r"youipilot:([^\s]+)", line, re.IGNORECASE)
                if match:
                    return match.group(1)

            return "⚠️ 未检测到 youipilot 镜像，需人工处理"
        except Exception as exc:
            return f"🚨 pilot_version 获取失败: {exc}"

    def get_youiscript_version(self, ip):
        try:
            output, error = self._run_command(
                ip,
                "echo youibot | sudo -S docker ps --format '{{.Image}}'",
            )
            if error and "password" not in error.lower() and "密码" not in error:
                return f"❌ 获取 youiscript_version 失败:\n{error}"

            for line in output.splitlines():
                if "youiscript:" not in line.lower():
                    continue
                match = re.search(r"youiscript:([^\s]+)", line, re.IGNORECASE)
                if match:
                    return match.group(1)

            return "⚠️ 未检测到 youiscript 镜像，需人工处理"
        except Exception as exc:
            return f"🚨 youiscript_version 获取失败: {exc}"

    def get_rcc_base_version(self, ip):
        try:
            reader = Rcc_base(username=self.username, password=self.password)
            if self.model in ("TW", "EX"):
                # TW/EX机型：先发送 AT+SetDebugPort=1，再发送 AT+ReadVersion
                return reader.execute_multiple_commands(ip, ["AT+SetDebugPort=1", "AT+ReadVersion"])
            else:
                # 其他机型：直接发送 AT+ReadVersion
                return reader.execute_lighting(ip, "AT+ReadVersion")
        except Exception as exc:
            return f"🚨 RCC Base 版本获取失败: {exc}"

    def get_io_expander_version(self, ip):
        try:
            reader = IO_base(username=self.username, password=self.password)
            return reader.execute_lighting(ip, "AT+GetExtendBoardMsg=")
        except Exception as exc:
            return f"🚨 IO Expander 版本获取失败: {exc}"

    def get_io_expander_version_0(self, ip):
        try:
            reader = IO_base(username=self.username, password=self.password)
            return reader.execute_lighting(ip, "AT+GetExtendBoardMsg=0")
        except Exception as exc:
            return f"🚨 IO Expander 版本获取失败: {exc}"

    def get_io_expander_version_1(self, ip):
        try:
            reader = IO_base(username=self.username, password=self.password)
            return reader.execute_lighting(ip, "AT+GetExtendBoardMsg=1")
        except Exception as exc:
            return f"🚨 IO Expander 版本获取失败: {exc}"

    def get_robot_version(self, ip):
        return self._find_keyword_entry(
            ip,
            "robot",
            port=10022,
            prefer_non_zip=True,
            missing_message="⚠️ 未检测到 robot 版本文件，需人工处理",
        )

    def get_rws_version(self, ip):
        if self.model == "MR":
            return self._find_keyword_entry(
                ip,
                "YOUIRWS",
                prefer_non_zip=True,
                missing_message="⚠️ 未检测到 YOUIRWS 版本文件，需人工处理",
            )
        if self.model in ("TW", "EX"):
            try:
                output, error = self._run_command(
                    ip,
                    "echo youibot | sudo -S docker ps --format '{{.Image}}'",
                    port=10022,
                )
                if error and "password" not in error.lower() and "密码" not in error:
                    return f"❌ 获取 rws_version 失败:\n{error}"

                for line in output.splitlines():
                    if "youirws:" not in line.lower():
                        continue
                    match = re.search(r"youirws:([^\s]+)", line, re.IGNORECASE)
                    if match:
                        return match.group(1)

                return "⚠️ 未检测到 youirws 镜像，需人工处理"
            except Exception as exc:
                return f"🚨 rws_version 获取失败: {exc}"
        return "⚠️ 不支持的机型"

    def get_default_fields(self):
        return self.DEFAULT_FIELDS.get(
            self.model,
            ["pilot_version", "compass_version", "rcc_base_version", "mirror_system"],
        )

    def read_fields(self, ip, fields=None):
        field_map = {
            "pilot_version": self.get_pilot_version,
            "compass_version": self.get_compass_version_from_ads,
            "mirror_system": self.read_mirror_file,
            "mirror_system_mos": self.read_mirror_file_from_mos,
            "mirror_system_hsr": self.read_mirror_file_hsr,
            "mos_version": self.get_mos_version,
            "mos_version_hsr": self.get_mos_version_hsr,
            "rcc_base_version": self.get_rcc_base_version,
            "robot_version": self.get_robot_version,
            "rws_version": self.get_rws_version,
            "io_expander_version": self.get_io_expander_version,
            "io_expander_version_0": self.get_io_expander_version_0,
            "io_expander_version_1": self.get_io_expander_version_1,
            "youiscript_version": self.get_youiscript_version,
        }

        selected_fields = fields or self.get_default_fields()
        results = {}
        for field in selected_fields:
            if self.model == "HSR" and field == "compass_version":
                getter = self.get_compass_version_hsr
            else:
                getter = field_map.get(field)
            if getter is None:
                results[field] = f"⚠️ 未知字段：{field}"
            else:
                results[field] = getter(ip)
        return results

    def read_all(self, ip):
        return self.read_fields(ip, self.get_default_fields())


if __name__ == "__main__":
    reader = MirrorSystemReader(model="TW")
    result = reader.read_all("192.168.17.146")
    print(result)
