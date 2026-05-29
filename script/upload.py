import paramiko
import os

def upload_file_to_server(
    local_path,
    remote_path,
    host="192.168.16.64",
    username="youibot",
    password="youibot",
    port=22
):
    """
    将本地文件上传到远程服务器指定路径

    :param local_path: 本地文件路径
    :param remote_path: 远程目标路径（包含文件名）
    :param host: 服务器IP
    :param username: 用户名
    :param password: 密码
    :param port: SSH端口（默认22）
    """
    if not os.path.exists(local_path):
        raise FileNotFoundError(f"本地文件不存在: {local_path}")

    transport = paramiko.Transport((host, port))
    try:
        transport.connect(username=username, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        print(f"开始上传: {local_path} -> {remote_path}")
        sftp.put(local_path, remote_path)
        print("上传成功")

    finally:
        transport.close()


# 调用示例
if __name__ == "__main__":
    upload_file_to_server(
        local_path="read_topic.py",
        remote_path="/home/youibot/read_topic.py"
    )