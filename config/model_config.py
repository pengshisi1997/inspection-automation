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
        "pilot_version": "feature_v4.0.3_xjyw.260528.1-x86_64-running",
        "rcc_base_version": "2.01",
        "robot_version": "robot-v1.3.0_202605301834",
        "rws_version": "v2.0.2",
        "mirror_system": "Pilot-4.0.3-desktop-2025-7-31.img",
        "youiscript_version": "release_v2.0.0.8-x86_64-running",
        "mos_version": "2.8.5_20260411",
    },
    'HSR': {
        "pilot_version": "v4.0.6_ex100.251028.1",
        "compass_version": "YOUICompassSetup-4.7.4-xjyw-V3.0-bl-20251229",
        "mirror_system": "Pilot-4.0.3-desktop-2025-7-31.img",
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
        'ping': ['192.168.0.8', '192.168.2.63', '192.168.2.88', '192.168.2.90', '192.168.2.250', '192.168.2.2', '192.168.2.89', '192.168.0.100:8081'],
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
