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
    'EX': ['pilot_version', 'rcc_base_version', 'robot_version', 'rws_version', 'mirror_system', 'youiscript_version', 'mos_version'],
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
        "pilot_version": "release_v4.0.8_xjyw.260730.1-x86_64-running",
        "rcc_base_version": "2.02",
        "robot_version": "robot-v1.3.1.1_2.2_202608011711",
        "rws_version": "v2.0.2",
        "mirror_system": "Pilot-4.0.3-desktop-2025-7-31.img",
        "youiscript_version": "release_v2.0.0.8-x86_64-running",
        "mos_version": "2.8.7_ARIS_20260804",
    },
    'EX': {
        "pilot_version": "release_v4.0.8_xjyw.260725.1-x86_64-running",
        "rcc_base_version": "2.01",
        "robot_version": "robot-v1.3.1.1_2.2_202608011711",
        "rws_version": "v2.0.2",
        "mirror_system": "Pilot-4.0.3-desktop-2025-12-31.img",
        "youiscript_version": "release_v2.0.0.8-x86_64-running",
        "mos_version": "2.8.7_ARIS_20260804",
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

# 动态测试的执行顺序和任务 ID 也归配置层管理；dynamic.py 不再维护副本。
DYNAMIC_TASK_EXECUTION = {
    'MS': {
        '直线': '66fae2d4-462b-4b33-a392-b66e4f63cdbe',
        '切区': '4aa45ede-d467-447b-850b-0f4ca1d9c122',
        '曲线': 'f5fb1dd8-fb44-46d1-aa0f-6876b08cbf1a',
        '沟壑': '769a31f3-50a7-4b5f-a431-34f5513a0bc5',
        '云台': '7f883a3c-0c98-4e1a-b4ee-e21f805ec9d4',
    },
    'EX': {
        '直线': '66fae2d4-462b-4b33-a392-b66e4f63cdbe',
        '切区': '2087823360446771201',
        '曲线': 'f5fb1dd8-fb44-46d1-aa0f-6876b08cbf1a',
        '沟壑': '769a31f3-50a7-4b5f-a431-34f5513a0bc5',
        '云台': '2089241270201430018',
    },
    'MR': {
        '直线': '5631958b-40e7-45c8-8f7b-b447c3d8e9b4',
        '切区': '6075b08e-0291-4cb5-a8c7-8d388fe1674e',
        '曲线': '5631958b-40e7-45c8-8f7b-b447c3d8e9b4',
        '沟壑': '5c2b6075-3f7c-4b6a-8781-e1cdd74c9dc5',
        '云台': 'ec59ba95-e151-4e4a-8b5c-b81eb8527961',
    },
    'HSR': {
        '直线': '374b38e0-5025-4f8a-8575-3525f99588c7',
        '切区': '5844ef46-4613-45c9-8b9d-e5148f33375b',
        '横移': '706cd915-f030-4178-a1d7-2e3747613db8',
        '沟壑': 'e653c5a9-8756-45b7-9aa5-57da4279adaa',
        '45°夹角': 'be3fe392-0275-4c52-90fb-8b6fb956bade',
        '云台': 'hsr_yuntai',
        '上集成': '337c9cf0-818f-498b-9e89-382584253cf4',
    },
}

DEFAULT_DYNAMIC_TASKS = list(DYNAMIC_TASK_EXECUTION['MS'])
HSR_DYNAMIC_TASKS = list(DYNAMIC_TASK_EXECUTION['HSR'])

# 测试子任务的单一事实源。
#
# MODEL_CONFIG 只决定“某机型启用哪些子任务及其顺序”；所有面向用户的名称、
# PDF 描述和前端能力都在这里维护。新增/改名子任务时无需再修改 HTML 或 pdf.py。
SUBTASK_CATALOG = {
    'version': {
        'pilot_version': {'label': 'Pilot版本'},
        'compass_version': {'label': 'Compass版本'},
        'rcc_base_version': {'label': 'RCC_Base版本'},
        'mirror_system': {'label': '工控机镜像版本'},
        'robot_version': {'label': 'Robot版本'},
        'rws_version': {'label': 'RWS版本'},
        'youiscript_version': {'label': 'Youiscript版本'},
        'mos_version': {'label': 'MOS版本'},
        'mos_version_hsr': {'label': '上集成MOS版本'},
        'mirror_system_hsr': {'label': '上集成工控机镜像'},
    },
    'sensor': {
        'odom': {'label': '里程计'},
        'imu_data': {'label': 'IMU数据'},
        'ks114_sensor': {'label': '超声波传感器'},
        'tfmini_sensor': {'label': '防跌落传感器'},
        'encoder': {'label': '编码器'},
        'scan_1': {'label': '激光雷达'},
        'cpu_hz': {'label': 'CPU频率（需大于2400Hz）'},
        'temperature': {'label': '温度'},
        'humidity': {'label': '湿度'},
        'pm10': {'label': 'PM10'},
        'pm2_5': {'label': 'PM2.5'},
        'o2': {'label': '气体板（O2/CO）'},
        'co': {'label': 'CO'},
        'microphone': {'label': '拾音器'},
        'fan_board': {'label': '风扇板'},
        'byz06_sensor': {'label': '噪声传感器'},
        'fs00802_sensor': {'label': '气体板（PM值）'},
    },
    'ping': {
        '192.168.0.8': {'label': '4G运维 (192.168.0.8)'},
        '192.168.2.63': {'label': '云台 (192.168.2.63)'},
        '192.168.2.250': {'label': '路由器 (192.168.2.250)'},
        '192.168.0.100': {'label': '内网口 (192.168.0.100)'},
        '192.168.2.2': {'label': '外网口 (192.168.2.2)'},
        '192.168.0.100:8081': {'label': 'Compass接口 (192.168.0.100:8081)'},
        '192.168.2.100': {'label': '算力板 (192.168.2.100)'},
        '192.168.0.50': {'label': 'PLC (192.168.0.50)'},
        '192.168.2.88': {'label': '机械臂 (192.168.2.88)'},
        '192.168.2.90': {'label': 'MOS工控机 (192.168.2.90)'},
        '192.168.2.89': {'label': '大恒相机 (192.168.2.89)'},
    },
    'button': {
        'emergency_stop': {'label': '急停按钮'},
        'left_emergency_stop': {'label': '左急停按钮'},
        'right_emergency_stop': {'label': '右急停按钮'},
        'voice': {'label': '语音按钮'},
        'chassis_left_stop': {'label': '底盘左急停'},
        'chassis_right_stop': {'label': '底盘右急停'},
        'integrated_left_stop': {'label': '上集成左急停'},
        'integrated_right_stop': {'label': '上集成右急停'},
        'unlock_brake': {'label': '解抱闸按钮'},
    },
    'anti_collision': {
        'front': {'label': '前防撞条', 'report_label': '前方'},
        'back': {'label': '后防撞条', 'report_label': '后方'},
        'left': {'label': '左防撞条', 'report_label': '左方'},
        'right': {'label': '右防撞条', 'report_label': '右方'},
    },
    'light': {
        'red': {'label': '红色灯光'},
        'blue': {'label': '蓝色灯光'},
        'green': {'label': '绿色灯光'},
        'front_light': {'label': '前补光灯', 'switchable': True},
        'back_light': {'label': '后补光灯', 'switchable': True},
        'charge_relay': {'label': '充电继电器', 'switchable': True},
    },
    'dynamic': {
        '直线': {'label': '直线', 'description': '0.4、0.8、1.2速度任务均能正常执行完成'},
        '切区': {'label': '切区', 'description': '切换地图任务能正常执行完成'},
        '曲线': {'label': '曲线', 'description': '0.4、0.8、1.2速度任务均能正常执行完成'},
        '横移': {'label': '横移', 'description': '横移任务能正常执行完成'},
        '沟壑': {'label': '沟壑', 'description': '30mm/50mm/70mm沟壑任务能正常执行完成'},
        '45°夹角': {'label': '45°夹角', 'description': '45°夹角任务能正常执行完成'},
        '云台': {'label': '云台', 'description': '云台拍照、预置点拍照及测温任务正常完成', 'view_result': True},
        '上集成': {'label': '上集成', 'description': '上集成功能任务能正常执行完成'},
    },
    'integrated': {
        'light_photo': {'label': '可见光拍照', 'description': '可见光拍照', 'view_result': True},
        'light_video': {'label': '可见光录像', 'description': '可见光录像', 'view_result': True},
        'thermal_photo': {'label': '热成像拍照', 'description': '热成像拍照', 'view_result': True},
        'thermal_video': {'label': '热成像录像', 'description': '热成像录像', 'view_result': True},
        'thermal_Temperature': {'label': '测温任务', 'description': '测温任务', 'view_result': True},
        'light_PTZ': {'label': '云台动作', 'description': '云台动作'},
        'light_point': {'label': '云台移动变倍至预置点10', 'description': '云台移动变倍至预置点10'},
        'thermal_point': {'label': '云台移动变倍至预置点11', 'description': '云台移动变倍至预置点11'},
        'Manual_focusing': {'label': '云台切换为手动聚焦', 'description': '云台切换为手动聚焦'},
        'Auto_focusing': {'label': '云台切换为自动聚焦', 'description': '云台切换为自动聚焦'},
    },
}

MODEL_CONFIG = {
    'MS': {
        'test_items': ['version', 'sensor', 'ping', 'button', 'anti_collision', 'speaker', 'light', 'dynamic', 'manual'],
        'button': ['emergency_stop'],
        'light': ['red', 'blue', 'green'],
        'anti_collision': ['front', 'back'],
        'version': list(VERSION_ITEMS['MS']),
        'sensor': ['odom', 'imu_data', 'ks114_sensor', 'encoder', 'scan_1', 'cpu_hz'],
        'ping': ['192.168.0.8', '192.168.2.63', '192.168.2.250', '192.168.0.100', '192.168.2.2', '192.168.0.100:8081'],
        'dynamic': list(DYNAMIC_TASK_EXECUTION['MS']),
    },
    'MR': {
        'test_items': ['version', 'sensor', 'ping', 'button', 'anti_collision', 'speaker', 'lift_motor', 'dynamic', 'manual'],
        'button': ['left_emergency_stop', 'right_emergency_stop', 'voice'],
        'light': [],
        'anti_collision': ['front', 'back'],
        'version': list(VERSION_ITEMS['MR']),
        'sensor': ['odom', 'imu_data', 'ks114_sensor', 'tfmini_sensor', 'encoder', 'scan_1', 'cpu_hz', 'byz06_sensor', 'fs00802_sensor'],
        'ping': ['192.168.0.8', '192.168.2.63', '192.168.2.250', '192.168.0.100', '192.168.2.2', '192.168.0.100:8081', '192.168.0.50'],
        'dynamic': list(DYNAMIC_TASK_EXECUTION['MR']),
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
        'test_items': ['version', 'sensor', 'ping', 'button', 'speaker', 'light',  'manual'],
        'button': ['emergency_stop'],
        'light': ['red', 'blue', 'green', 'front_light', 'back_light', 'charge_relay'],
        'anti_collision': ['front', 'back'],
        'version': list(VERSION_ITEMS['TW']),
        'sensor': ['odom', 'imu_data', 'ks114_sensor', 'cpu_hz', 'temperature', 'humidity', 'o2', 'microphone', 'fan_board'],
        'ping': ['192.168.0.8', '192.168.2.63', '192.168.2.250', '192.168.0.100', '192.168.2.2', ],
        'integrated': ['light_photo', 'light_video', 'thermal_photo', 'thermal_video', 'thermal_Temperature', 'light_PTZ', 'light_point', 'thermal_point', 'Manual_focusing', 'Auto_focusing'],
    },
    'EX': {
        'test_items': ['version', 'sensor', 'ping', 'button', 'anti_collision', 'speaker', 'light', 'dynamic', 'manual'],
        'button': ['emergency_stop'],
        'light': ['red', 'green', 'blue'],
        'anti_collision': ['front', 'back'],
        'version': list(VERSION_ITEMS['EX']),
        'sensor': ['odom', 'imu_data', 'encoder', 'scan_1', 'cpu_hz'],
        'ping': ['192.168.0.8', '192.168.2.63', '192.168.2.250', '192.168.0.100', '192.168.2.2'],
        'dynamic': list(DYNAMIC_TASK_EXECUTION['EX']),
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

# 兼容旧调用方；内容由统一目录派生，不再单独维护。
INTEGRATED_TASK_DESCRIPTIONS = {
    task_id: meta.get('description', meta.get('label', task_id))
    for task_id, meta in SUBTASK_CATALOG['integrated'].items()
}
DYNAMIC_TASK_DESCRIPTIONS = {
    task_id: meta.get('description', '')
    for task_id, meta in SUBTASK_CATALOG['dynamic'].items()
}


def get_model_config(model, default_model=DEFAULT_MODEL):
    return MODEL_CONFIG.get(model) or MODEL_CONFIG[default_model]


def get_version_fields(model):
    return list(get_model_config(model).get('version', VERSION_ITEMS['MS']))


def get_subtask_definitions(model, test_type):
    """按机型配置顺序返回前端/PDF可直接消费的子任务定义。"""
    task_ids = get_model_config(model).get(test_type, [])
    catalog = SUBTASK_CATALOG.get(test_type, {})
    definitions = []
    for task_id in task_ids:
        meta = dict(catalog.get(task_id, {}))
        meta.setdefault('label', str(task_id))
        meta['id'] = task_id
        definitions.append(meta)
    return definitions


def get_subtask_labels(model, test_type, report=False):
    label_key = 'report_label' if report else 'label'
    return {
        item['id']: item.get(label_key, item.get('label', str(item['id'])))
        for item in get_subtask_definitions(model, test_type)
    }


def get_subtask_descriptions(model, test_type):
    return {
        item['id']: item.get('description', item.get('label', str(item['id'])))
        for item in get_subtask_definitions(model, test_type)
    }


def validate_test_config():
    """启动时尽早暴露漏配，避免到了网页或 PDF 才发现名称为空。"""
    errors = []
    for model, config in MODEL_CONFIG.items():
        unknown_tests = [item for item in config.get('test_items', []) if item not in TEST_NAMES]
        if unknown_tests:
            errors.append(f"{model}.test_items 未定义名称: {unknown_tests}")

        for test_type, catalog in SUBTASK_CATALOG.items():
            missing = [task_id for task_id in config.get(test_type, []) if task_id not in catalog]
            if missing:
                errors.append(f"{model}.{test_type} 未定义子任务元数据: {missing}")

        if model in DYNAMIC_TASK_EXECUTION:
            execution_order = list(DYNAMIC_TASK_EXECUTION[model])
            if config.get('dynamic', []) != execution_order:
                errors.append(f"{model}.dynamic 与动态执行配置顺序不一致")

    missing_dynamic_meta = [
        f"{model}.{task_id}"
        for model, tasks in DYNAMIC_TASK_EXECUTION.items()
        for task_id in tasks
        if task_id not in SUBTASK_CATALOG['dynamic']
    ]
    if missing_dynamic_meta:
        errors.append(f"动态执行任务未定义展示元数据: {missing_dynamic_meta}")

    if errors:
        raise ValueError("测试配置无效: " + "; ".join(errors))


validate_test_config()
