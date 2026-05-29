import paramiko


class RemoteDesktopVolumeBell:
    # ===== 固定账号 =====
    USERNAME = "youibot"
    PASSWORD = "youibot"
    PORT = 22

    def __init__(self, ip):
        self.ip = ip
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.client.connect(
            hostname=self.ip,
            port=self.PORT,
            username=self.USERNAME,
            password=self.PASSWORD,
            timeout=10
        )

    def close(self):
        if self.client:
            self.client.close()
            self.client = None

    def bell(self):
        """
        SSH执行音频播放（后台不阻塞）
        """
        cmd = "nohup play /usr/youibot/audio/AutoMode_audio.mp3 >/dev/null 2>&1 &"

        # 不读取stdout/stderr，避免阻塞
        self.client.exec_command(cmd)

    def emergent_stop_bell(self):
        """
        SSH执行紧急停止音频播放（后台不阻塞）
        """
        cmd = "nohup play /usr/youibot/install/share/youibot_blinker_sound/audio_folder/EmergentStop_audio.mp3 >/dev/null 2>&1 &"

        # 不读取stdout/stderr，避免阻塞
        self.client.exec_command(cmd)

    def tab_sound(self):
        """
        SSH连接10022端口，用speaker-test播放10次声音（后台不阻塞）
        """
        # 使用subprocess启动独立进程，避免阻塞
        import subprocess
        import sys
        
        # 启动后台进程
        subprocess.Popen(
            [sys.executable, '-c', 
             f'''
import paramiko
import time
import sys

try:
    print(f"正在连接 {self.ip}:10022...", file=sys.stderr)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname="{self.ip}",
        port=10022,
        username="youibot",
        password="youibot",
        timeout=10
    )
    print("连接成功！", file=sys.stderr)
    
    # 使用speaker-test播放10次
    for i in range(1):
        print(f"播放第 {{i+1}} 次...", file=sys.stderr)
        cmd = "speaker-test -t sine -f 440 -l 1 2>/dev/null"
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
        time.sleep(0.1)
    
    client.close()
    print("完成！", file=sys.stderr)
except Exception as e:
    print(f"错误: {{e}}", file=sys.stderr)
    import traceback
    print(traceback.format_exc(), file=sys.stderr)
'''],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def play(self):
        """
        触发播放
        """
        try:
            self.connect()
            self.bell()
            self.tab_sound()
            self.emergent_stop_bell()
        finally:
            self.close()

    def play_emergent_stop(self):
        """
        只播放紧急停止声音
        """
        try:
            self.connect()
            self.emergent_stop_bell()
        finally:
            self.close()


if __name__ == "__main__":
    player = RemoteDesktopVolumeBell(
        ip="192.168.16.15"
    )

    player.play()