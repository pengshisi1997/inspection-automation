#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import threading
import paramiko
import re
import json

from sonic_ks114.msg import KS114SensorData
from sensor_msgs.msg import Imu
from youibot_msgs.msg import Encoder
from nav_msgs.msg import Odometry


# ================= 全局数据缓存 =================
data_store = {
    "distance": None,
    "imu_orientation": None,
    "encoder": None,
    "odom_position": None,
    "odom_orientation": None,
    "cpu_mhz": None
}

lock = threading.Lock()


# ================= 回调函数 =================

def ks114_callback(msg):
    with lock:
        data_store["distance"] = msg.distance


def imu_callback(msg):
    ori = msg.orientation
    with lock:
        data_store["imu_orientation"] = (ori.x, ori.y, ori.z, ori.w)


def encoder_callback(msg):
    with lock:
        data_store["encoder"] = msg.encoder


def odom_callback(msg):
    pos = msg.pose.pose.position
    ori = msg.pose.pose.orientation

    with lock:
        data_store["odom_position"] = (pos.x, pos.y)
        data_store["odom_orientation"] = (ori.z, ori.w)


# ================= CPU 读取 =================

def read_cpu_hz(ip, username, password):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        client.connect(ip, username=username, password=password, timeout=5)

        stdin, stdout, stderr = client.exec_command(
            'cat /proc/cpuinfo | grep "cpu MHz"'
        )

        text = stdout.read().decode()
        client.close()

        matches = re.findall(r'cpu MHz\s*:\s*([0-9.]+)', text)

        return [float(x) for x in matches]

    except Exception as e:
        rospy.logwarn("CPU read failed: %s", str(e))
        return None


def cpu_monitor_thread(ip, username, password):
    rate = rospy.Rate(1)  # 1Hz

    while not rospy.is_shutdown():
        cpu = read_cpu_hz(ip, username, password)

        with lock:
            data_store["cpu_mhz"] = cpu

        rate.sleep()


# ================= 定时打印 =================

def timer_callback(event):
    with lock:
        rospy.loginfo("========== 当前传感器状态 ==========")
        rospy.loginfo("distance: %s", data_store["distance"])
        rospy.loginfo("imu_orientation: %s", data_store["imu_orientation"])
        rospy.loginfo("encoder: %s", data_store["encoder"])
        rospy.loginfo("odom_position: %s", data_store["odom_position"])
        rospy.loginfo("odom_orientation: %s", data_store["odom_orientation"])
        rospy.loginfo("cpu_mhz: %s", data_store["cpu_mhz"])
        
        # 保存到topic.json
        try:
            with open("topic.json", "w") as f:
                json.dump(data_store, f, indent=2)
            rospy.loginfo("Data saved to topic.json")
        except Exception as e:
            rospy.logwarn("Failed to save data: %s", str(e))


# ================= 主函数 =================

def listener():
    rospy.init_node('multi_sensor_aggregator', anonymous=True)

    # ===== ROS订阅 =====
    rospy.Subscriber("/ks114_sensor/ks114_data", KS114SensorData, ks114_callback)
    rospy.Subscriber("/imu_data", Imu, imu_callback)
    rospy.Subscriber("/sensors/encoder", Encoder, encoder_callback)
    rospy.Subscriber("/odom", Odometry, odom_callback)

    # ===== SSH配置（建议用rosparam）=====
    ip = rospy.get_param("~cpu_ip", "192.168.1.100")
    username = rospy.get_param("~cpu_user", "user")
    password = rospy.get_param("~cpu_pass", "password")

    # ===== 启动CPU线程 =====
    t = threading.Thread(
        target=cpu_monitor_thread,
        args=(ip, username, password)
    )
    t.daemon = True
    t.start()

    # ===== 定时器 =====
    rospy.Timer(rospy.Duration(0.5), timer_callback)

    rospy.loginfo("multi_sensor_aggregator started")
    rospy.spin()


# ================= 入口 =================

if __name__ == '__main__':
    listener()