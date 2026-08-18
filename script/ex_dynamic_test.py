"""
EX 机型动态测试脚本
使用 robot_request.py 中的函数完成：
  上传地图 → 刷新地图 → 指定地图 → 切换手动模式 →
  手动重定位 → 自动重定位 → 切换自动模式 → 创建任务
"""
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from robot_request import (
    login_request,
    upload_agv_map,
    reload_agv_maps,
    set_current_map,
    set_manual_mode,
    set_auto_mode,
    manual_relocation,
    auto_relocation,
    create_mission,
)

# ======================== EX 机型配置 ========================
# 根据实际环境修改以下参数
EX_IP = "192.168.16.200"          # 机器人 IP
MAP_FILE = "zidonghuaceshi.zip"    # 地图文件路径（map/EX/ 下的 zidonghuaceshi.zip）
MAP_ID = "zidonghuaceshi"          # 地图 ID

# 手动重定位参数
RELOCATION_PARAMS = {
    "init_x": 0.0,
    "init_y": 0.0,
    "init_angle": 0.0,
    "target_x": 0.0,
    "target_y": 0.0,
    "target_angle": 0.0,
}

# EX 动态测试任务列表
EX_MISSIONS = ["直线", "切区", "曲线", "沟壑", "云台"]


def run_ex_dynamic_test(ip, map_file=MAP_FILE, map_id=MAP_ID):
    """执行 EX 机型动态测试完整流程"""
    print(f"\n{'='*60}")
    print(f"  EX 机型动态测试开始")
    print(f"  目标 IP: {ip}")
    print(f"{'='*60}\n")

    # 1. 上传地图
    print("[1/8] 上传地图...")
    if os.path.exists(map_file):
        resp = upload_agv_map(ip, map_file)
        print(f"  上传地图完成: status={resp.status_code}")
    else:
        print(f"  警告: 地图文件 {map_file} 不存在，跳过上传")
    time.sleep(1)

    # 2. 刷新地图
    print("[2/8] 刷新地图...")
    result = reload_agv_maps(ip)
    print(f"  刷新地图完成: {result.get('status_code', result.get('error'))}")
    time.sleep(1)

    # 3. 指定地图
    print(f"[3/8] 指定地图 (mapId={map_id})...")
    result = set_current_map(ip, map_id=map_id)
    print(f"  指定地图完成: {result}")
    time.sleep(1)

    # 4. 切换手动模式
    print("[4/8] 切换手动模式...")
    result = set_manual_mode(ip)
    print(f"  切换手动模式完成: {result}")
    time.sleep(1)

    # 5. 手动重定位
    print("[5/8] 手动重定位...")
    params = RELOCATION_PARAMS
    result = manual_relocation(
        ip,
        init_x=params["init_x"],
        init_y=params["init_y"],
        init_angle=params["init_angle"],
        target_x=params["target_x"],
        target_y=params["target_y"],
        target_angle=params["target_angle"],
    )
    print(f"  手动重定位完成: {result}")
    time.sleep(2)

    # 6. 自动重定位
    print("[6/8] 自动重定位...")
    result = auto_relocation(ip)
    print(f"  自动重定位完成: {result}")
    time.sleep(3)

    # 7. 切换自动模式
    print("[7/8] 切换自动模式...")
    result = set_auto_mode(ip)
    print(f"  切换自动模式完成: {result}")
    time.sleep(1)

    # 8. 创建任务
    print("[8/8] 创建动态测试任务...")
    mission_results = {}
    for mission_name in EX_MISSIONS:
        print(f"  创建任务: {mission_name}")
        result = create_mission(ip, mission_name)
        print(f"    结果: {result}")
        mission_results[mission_name] = result
        time.sleep(1)

    print(f"\n{'='*60}")
    print(f"  EX 动态测试完成")
    print(f"{'='*60}\n")

    return mission_results


# 单独执行某个步骤（方便调试）
def step_upload_map(ip, map_file=MAP_FILE):
    """仅上传地图"""
    print(f"上传地图: {map_file}")
    return upload_agv_map(ip, map_file)


def step_reload_maps(ip):
    """仅刷新地图"""
    print("刷新地图...")
    return reload_agv_maps(ip)


def step_set_map(ip, map_id=MAP_ID):
    """仅指定地图"""
    print(f"指定地图: {map_id}")
    return set_current_map(ip, map_id=map_id)


def step_manual_relocation(ip):
    """仅手动重定位"""
    params = RELOCATION_PARAMS
    print(f"手动重定位: init=({params['init_x']},{params['init_y']},{params['init_angle']})")
    return manual_relocation(
        ip,
        init_x=params["init_x"],
        init_y=params["init_y"],
        init_angle=params["init_angle"],
        target_x=params["target_x"],
        target_y=params["target_y"],
        target_angle=params["target_angle"],
    )


def step_auto_relocation(ip):
    """仅自动重定位"""
    print("自动重定位...")
    return auto_relocation(ip)


def step_create_missions(ip, missions=None):
    """仅创建任务"""
    if missions is None:
        missions = EX_MISSIONS
    results = {}
    for name in missions:
        print(f"创建任务: {name}")
        results[name] = create_mission(ip, name)
        time.sleep(1)
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="EX 机型动态测试")
    parser.add_argument("ip", nargs="?", default=EX_IP, help="机器人 IP 地址")
    parser.add_argument("--map-file", default=MAP_FILE, help="地图文件路径")
    parser.add_argument("--map-id", default=MAP_ID, help="地图 ID")
    parser.add_argument("--step", choices=[
        "all", "upload_map", "reload_maps", "set_map",
        "manual_relocation", "auto_relocation", "create_missions",
    ], default="all", help="执行单一步骤")

    args = parser.parse_args()

    step_map = {
        "upload_map": step_upload_map,
        "reload_maps": step_reload_maps,
        "set_map": step_set_map,
        "manual_relocation": step_manual_relocation,
        "auto_relocation": step_auto_relocation,
        "create_missions": step_create_missions,
    }

    if args.step == "all":
        run_ex_dynamic_test(args.ip, args.map_file, args.map_id)
    else:
        fn = step_map[args.step]
        fn(args.ip)
