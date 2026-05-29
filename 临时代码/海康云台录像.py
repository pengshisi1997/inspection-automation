import time
from hikvisionapi import Client
from datetime import datetime

# 设备配置信息
DEVICE_IP = "192.168.16.64"  # 仅IP地址，不含端口
DEVICE_PORT = 8083           # 单独指定端口
USER = "admin"
PWD = "robot2020"

def test_device_info():
    """
    测试设备连接并获取设备信息
    """
    device_url = f"http://{DEVICE_IP}:{DEVICE_PORT}"
    
    try:
        print("正在连接海康云台设备...")
        client = Client(device_url, USER, PWD, timeout=10)
        print("设备连接成功！")
        
        # 获取设备信息
        print("获取设备信息...")
        device_info = client.System.deviceInfo(method='get')
        print("设备信息:", device_info)
        
        # 尝试获取存储设备信息
        print("获取存储设备信息...")
        try:
            storage = client.Storage.storageDevices(method='get')
            print("存储设备:", storage)
        except Exception as e:
            print("获取存储设备失败:", str(e))
        
        # 尝试获取通道信息（不同路径）
        print("获取通道信息...")
        try:
            channels = client.Media.channels(method='get')
            print("通道信息:", channels)
        except Exception as e:
            print("获取通道信息失败:", str(e))
        
        # 尝试获取录像状态
        print("获取录像状态...")
        try:
            record_status = client.ContentMgmt.record.status(method='get')
            print("录像状态:", record_status)
        except Exception as e:
            print("获取录像状态失败:", str(e))
            
    except Exception as e:
        print(f"操作失败：{str(e)}")

def record_video_5seconds():
    """
    录制海康云台视频5秒钟
    """
    # 拼接设备完整地址
    device_url = f"http://{DEVICE_IP}:{DEVICE_PORT}"
    
    try:
        # 1. 建立与设备的连接
        print("正在连接海康云台设备...")
        client = Client(device_url, USER, PWD, timeout=10)
        print("设备连接成功！")

        # 2. 检查设备信息
        print("检查设备型号...")
        device_info = client.System.deviceInfo(method='get')
        model = device_info.get('DeviceInfo', {}).get('model', 'Unknown')
        print(f"设备型号: {model}")

        # 3. 分析设备能力
        print("分析设备能力...")
        system_capability = client.System.capabilities(method='get')
        support_playback = system_capability.get('DeviceCap', {}).get('isSupportPlayback', 'false')
        print(f"支持回放: {support_playback}")

        # 4. 尝试获取实时流（作为替代方案）
        print("\n尝试获取实时视频流...")
        try:
            # 尝试获取主码流
            stream_params = {
                'method': 'get',
                'type': 'opaque_data'
            }
            # 主码流地址：ISAPI/Streaming/channels/101/httpPreview
            stream_response = client.Streaming.channels[101].httpPreview(**stream_params)
            print("成功获取实时流！")
            
            # 保存流数据到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_path = f"record_{timestamp}.mp4"
            print(f"开始录制5秒钟，保存路径：{video_path}")
            
            with open(video_path, 'wb') as f:
                start_time = time.time()
                while time.time() - start_time < 5:
                    chunk = stream_response.raw.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    print(f"录制中... {int(time.time() - start_time)}秒", end="\r")
                    time.sleep(0.1)
            
            print("\n录像完成！视频已保存至:", video_path)
            
        except Exception as e:
            print(f"获取实时流失败: {str(e)}")
            print("\n=== 错误分析 ===")
            print("1. 设备可能没有配置存储设备（SD卡/硬盘）")
            print("2. 账号权限不足，需要管理员权限")
            print("3. 设备型号可能不支持本地录像功能")
            print("4. 固件版本限制了API访问")
            print("\n=== 解决方案 ===")
            print("1. 检查设备是否插入SD卡或连接硬盘")
            print("2. 确认使用的是管理员账号")
            print("3. 登录设备Web界面检查存储配置")
            print("4. 检查设备是否支持本地录像功能")
            print("5. 尝试升级设备固件到最新版本")

    except Exception as e:
        print(f"操作失败：{str(e)}")
        # 常见错误说明：
        # 1. 连接超时：检查IP、端口是否正确，设备是否在线
        # 2. 认证失败：检查用户名密码是否正确
        # 3. 权限不足：确保账号有录像权限
        # 4. 存储问题：检查设备是否有存储设备

if __name__ == "__main__":
    # 先测试设备信息
    test_device_info()
    print("\n" + "="*50 + "\n")
    # 再测试录像功能
    record_video_5seconds()