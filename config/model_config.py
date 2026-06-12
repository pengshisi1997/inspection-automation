import os

# ============================================================
# 全局数据存储根目录
#
# 新的存储结构（按IP分组，便于按机器人归档/迁移）：
#   DATA_BASE_DIR/
#       test_record/
#           <ip1>/
#               <ip1>.json          # 测试结果 JSON
#               image_yuntai/       # 该IP下载的云台/集成图片/视频
#               manual_upload/      # 该IP手动测试上传的图片
#                   <测试项A>/
#                       xxx.jpg
#                   <测试项B>/
#                       ...
#           <ip2>/
#               ...
#       image/                      # 其它共用图片（若有）
# ============================================================
DATA_BASE_DIR = r"D:\自动化测试保存"

# 顶层目录
TEST_RECORD_DIR = os.path.join(DATA_BASE_DIR, "test_record")
IMAGE_DIR        = os.path.join(DATA_BASE_DIR, "image")
# 为保持与旧代码的兼容性，仍然导出这个变量；新代码优先使用
# get_image_yuntai_dir(ip) 来获取按IP区分的目录
IMAGE_YUNTAI_DIR = os.path.join(DATA_BASE_DIR, "image_yuntai")

# 确保顶层目录存在（程序首次运行时自动创建）
for _dir in (TEST_RECORD_DIR, IMAGE_DIR, IMAGE_YUNTAI_DIR):
    os.makedirs(_dir, exist_ok=True)


def _safe_ip(ip):
    """对 IP 做简单清洗，便于作为合法目录名使用。"""
    if not ip:
        return "unknown"
    cleaned = str(ip).strip()
    for ch in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
        cleaned = cleaned.replace(ch, "_")
    return cleaned or "unknown"


def get_ip_dir(ip):
    """获取指定IP的归档目录： DATA_BASE_DIR/test_record/<ip>/"""
    d = os.path.join(TEST_RECORD_DIR, _safe_ip(ip))
    os.makedirs(d, exist_ok=True)
    return d


def get_result_file_path(ip):
    """获取指定IP的测试结果 JSON 文件路径。"""
    return os.path.join(get_ip_dir(ip), f"{_safe_ip(ip)}.json")


def get_image_yuntai_dir(ip=None):
    """
    获取云台/集成图片存储目录。
    - 若提供了 ip，则返回： test_record/<ip>/image_yuntai/
    - 否则回退到旧的全局目录： DATA_BASE_DIR/image_yuntai/
    """
    if ip:
        d = os.path.join(get_ip_dir(ip), "image_yuntai")
        os.makedirs(d, exist_ok=True)
        return d
    os.makedirs(IMAGE_YUNTAI_DIR, exist_ok=True)
    return IMAGE_YUNTAI_DIR


def get_manual_upload_dir(ip=None):
    """
    获取手动测试图片存储目录。
    - 若提供了 ip，则返回： test_record/<ip>/manual_upload/
    - 否则回退到旧的全局目录： static/manual_upload/
    """
    if ip:
        d = os.path.join(get_ip_dir(ip), "manual_upload")
        os.makedirs(d, exist_ok=True)
        return d
    # 旧路径，兼容无 ip 的场景（如 shared / 未登录）
    old = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "manual_upload")
    old = os.path.abspath(old)
    os.makedirs(old, exist_ok=True)
    return old


DEFAULT_MODEL = 'MS'

VERSION_ITEMS = {
    'MS': ['pilot_version', 'compass_version', 'rcc_base_version', 'mirror_system'],
    'MR': ['pilot_version', 'compass_version', 'mirror_system', 'rws_version'],
    'TW': ['pilot_version', 'rcc_base_version', 'robot_version', 'rws_version', 'mirror_system', 'youiscript_version', 'mos_version'],
    'HSR': ['pilot_version', 'compass_version', 'mirror_system', 'mos_version_hsr', 'mirror_system_hsr', 'rcc_base_version'],
}

VERSION_STANDARDS = {
    'MS': {
        "pilot_version": "release/v3.8.0_xjyw_v1.5.21_20260313",
        "compass_version": "YOUICompassSetup-4.7.4-xjyw-V4.2.0-20260427",
        "rcc_base_version": "2.01",
        "mirror_system": "Pilot-4.0.3-desktop-2025-7-31.img",
    },
    'MR': {
        "pilot_version": "YouiPilot-release_v3.5.2_IDC_13-linux-amd64.deb",
        "compass_version": "YOUICompass-4.6.0-IDC03-20250813",
        "mirror_system": "Pilot3.7.0_2022-5-18--img",
        "rws_version": "YOUIRWS_v2.0.2",
    },
    'X310': {
        "pilot_version": "release/v3.8.0_xjyw_v1.5.21_20260313",
        "compass_version": "YOUICompassSetup-4.7.4-xjyw-V4.2.0-20260427",
        "rcc_base_version": "2.01",
        "mirror_system": "Pilot-4.0.3-desktop-2025-7-31.img",
    },
    'X320': {
        "pilot_version": "release/v3.8.0_xjyw_v1.5.21_20260313",
        "compass_version": "YOUICompassSetup-4.7.4-xjyw-V4.2.0-20260427",
        "rcc_base_version": "2.01",
        "mirror_system": "Pilot-4.0.3-desktop-2025-7-31.img",
    },
    'TW': {
        "pilot_version": "release_v4.0.8_xjyw.260528.1-x86_64-running",
        "rcc_base_version": "2.02",
        "robot_version": "robot-v1.3.0_202605301834",
        "rws_version": "v2.0.2",
        "mirror_system": "Pilot-4.0.3-desktop-2025-7-31.img",
        "youiscript_version": "release_v2.0.0.8-x86_64-running",
        "mos_version": "2.8.5_20260411",
    },
    'HSR': {
        "pilot_version": "v4.0.6_ex100.251028.1",
        "compass_version": "YOUICompassSetup-4.7.4-xjyw-V3.0-bl-20251229",
        "mirror_system": "Pilot-4.0.3-desktop-2025-11-27.img",
        "mos_version_hsr": "2.6.21_ARIS",
        "mirror_system_hsr": "Pilot-4.0.3-desktop-2025-11-27.img",
        "rcc_base_version": "2.01",
    },
}

DEFAULT_DYNAMIC_TASKS = ['直线', '切区', '曲线', '沟壑', '云台']
HSR_DYNAMIC_TASKS = ['直线', '切区', '横移', '沟壑', '45°夹角', '精定位', '云台', '上集成']

MODEL_CONFIG = {
    'MS': {
        'test_items': ['version', 'sensor', 'ping', 'button', 'anti_collision', 'speaker', 'light', 'dynamic', 'manual'],
        'button': ['emergency_stop'],
        'light': ['red', 'blue', 'green'],
        'anti_collision': ['front', 'back'],
        'version': list(VERSION_ITEMS['MS']),
        'sensor': ['odom', 'imu_data', 'ks114_sensor', 'encoder', 'scan_1', 'cpu_hz'],
        'ping': ['192.168.0.8', '192.168.2.63', '192.168.2.250', '192.168.0.100', '192.168.2.2', '192.168.0.100:8081'],
        'dynamic': DEFAULT_DYNAMIC_TASKS,
    },
    'MR': {
        'test_items': ['version', 'sensor', 'ping', 'button', 'anti_collision', 'speaker', 'lift_motor', 'dynamic', 'manual'],
        'button': ['left_emergency_stop', 'right_emergency_stop', 'voice'],
        'light': [],
        'anti_collision': ['front', 'back'],
        'version': list(VERSION_ITEMS['MR']),
        'sensor': ['odom', 'imu_data', 'ks114_sensor', 'tfmini_sensor', 'encoder', 'scan_1', 'cpu_hz', 'byz06_sensor', 'fs00802_sensor'],
        'ping': ['192.168.0.8', '192.168.2.63', '192.168.2.250', '192.168.0.100', '192.168.2.2', '192.168.0.100:8081', '192.168.0.50'],
        'dynamic': DEFAULT_DYNAMIC_TASKS,
    },
    'X310': {
        'test_items': ['version', 'sensor', 'ping', 'button', 'anti_collision', 'speaker', 'light', 'dynamic', 'manual'],
        'button': ['emergency_stop', 'voice'],
        'light': ['red', 'blue', 'green'],
        'anti_collision': ['front', 'back'],
        'version': list(VERSION_ITEMS['MS']),
        'sensor': ['odom', 'imu_data', 'ks114_sensor', 'tfmini_sensor', 'encoder', 'scan_1', 'cpu_hz'],
        'ping': ['192.168.0.8', '192.168.2.63', '192.168.2.250', '192.168.0.100', '192.168.2.2', '192.168.0.100:8081'],
        'dynamic': DEFAULT_DYNAMIC_TASKS,
    },
    'X320': {
        'test_items': ['version', 'sensor', 'ping', 'button', 'anti_collision', 'speaker', 'light', 'dynamic', 'manual'],
        'button': ['emergency_stop', 'voice'],
        'light': ['red', 'blue', 'green'],
        'anti_collision': ['front', 'back'],
        'version': list(VERSION_ITEMS['MS']),
        'sensor': ['odom', 'imu_data', 'ks114_sensor', 'tfmini_sensor', 'encoder', 'scan_1', 'cpu_hz'],
        'ping': ['192.168.0.8', '192.168.2.63', '192.168.2.250', '192.168.0.100', '192.168.2.2', '192.168.0.100:8081'],
        'dynamic': DEFAULT_DYNAMIC_TASKS,
    },
    'TW': {
        'test_items': ['version', 'sensor', 'ping', 'button', 'speaker', 'light', 'integrated', 'manual'],
        'button': ['emergency_stop'],
        'light': ['red', 'blue', 'green', 'front_light', 'back_light', 'charge_relay'],
        'anti_collision': ['front', 'back'],
        'version': list(VERSION_ITEMS['TW']),
        'sensor': ['odom', 'imu_data', 'ks114_sensor', 'cpu_hz', 'temperature', 'humidity', 'o2', 'microphone', 'fan_board'],
        'ping': ['192.168.0.8', '192.168.2.63', '192.168.2.250', '192.168.0.100', '192.168.2.2', '192.168.2.100'],
        'integrated': ['light_photo', 'light_video', 'thermal_photo', 'thermal_video', 'thermal_Temperature', 'light_PTZ', 'light_point', 'thermal_point', 'Manual_focusing', 'Auto_focusing'],
    },
    'HSR': {
        'test_items': ['version', 'sensor', 'ping', 'button', 'anti_collision', 'speaker', 'light', 'dynamic', 'manual'],
        'button': ['chassis_left_stop', 'chassis_right_stop', 'integrated_left_stop', 'integrated_right_stop', 'unlock_brake'],
        'light': ['red', 'blue', 'green'],
        'anti_collision': ['front', 'back', 'left', 'right'],
        'version': list(VERSION_ITEMS['HSR']),
        'sensor': ['odom', 'imu_data', 'encoder', 'scan_1', 'cpu_hz'],
        'ping': ['192.168.0.8', '192.168.2.88', '192.168.2.90', '192.168.2.250', '192.168.2.2', '192.168.2.89', '192.168.0.100:8081'],
        'dynamic': HSR_DYNAMIC_TASKS,
    },
}

MODEL_OPTIONS = list(MODEL_CONFIG.keys())

TEST_ORDER = ['version', 'sensor', 'ping', 'button', 'anti_collision', 'speaker', 'light', 'lift_motor', 'dynamic', 'integrated', 'manual']

TEST_NAMES = {
    'version': '版本检测',
    'sensor': '传感器检测',
    'ping': '网络Ping测试',
    'anti_collision': '防撞条检测',
    'speaker': '扬声器检测',
    'button': '按钮测试',
    'light': '灯光测试',
    'lift_motor': '升降电机测试',
    'dynamic': '动态测试',
    'integrated': '集成测试',
    'manual': '人工测试',
}

INTEGRATED_TASK_DESCRIPTIONS = {
    'light_photo': '可见光拍照',
    'light_video': '可见光录像',
    'thermal_photo': '热成像拍照',
    'thermal_video': '热成像录像',
    'light_PTZ': '云台动作',
    'light_point': '云台移动变倍至预置点10',
    'thermal_point': '云台移动变倍至预置点11',
    'Manual_focusing': '云台切换为手动聚焦',
    'Auto_focusing': '云台切换为自动聚焦',
    'thermal_Temperature': '测温任务',
}


def get_model_config(model, default_model=DEFAULT_MODEL):
    return MODEL_CONFIG.get(model) or MODEL_CONFIG[default_model]


def get_version_fields(model):
    return list(get_model_config(model).get('version', VERSION_ITEMS['MS']))
