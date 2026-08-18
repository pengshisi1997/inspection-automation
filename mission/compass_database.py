import os
import pandas as pd
import numpy as np
import mysql.connector

# 机型对应的数据库名
MODEL_DATABASES = {
    'EX': 'robot_system',
    'default': 'youicompass'
}

# 机型对应的表名
MODEL_TABLES = {
    'EX': ['checkpoint', 'checkpoint_action', 'checkpoint_action_parameter', 'checkpoint_action_record',
           'mission', 'mission_model', 'path', 'side_path', 'agv','global_variable'],
    'default': ['mission', 'mission_action',  'mission_action_parameter']
}

def get_database(model_type):
    """根据机型获取对应的数据库名"""
    return MODEL_DATABASES.get(model_type, MODEL_DATABASES['default'])

def get_tables(model_type):
    """根据机型获取对应的表名列表"""
    return MODEL_TABLES.get(model_type, MODEL_TABLES['default'])

def download_task(ip, model_type):
    connection = mysql.connector.connect(
        host=ip,
        user='root',
        password='root',
        database=get_database(model_type)
    )

    tables = get_tables(model_type)

    try:
        for table in tables:
            query = f"SELECT * FROM {table}"
            df = pd.read_sql(query, connection)
            df.to_csv(f"mission/{table}.csv", index=False)
            print(f"Table {table} exported successfully.")
    finally:
        connection.close()

def upload_task(ip, model_type):
    connection = mysql.connector.connect(
        host=ip,
        user='root',
        password='root',
        database=get_database(model_type)
    )

    tables = get_tables(model_type)

    try:
        cursor = connection.cursor()
        current_path = os.getcwd()

        for table in tables:
            csv_file_path = os.path.join(current_path, "mission", f"{table}.csv")

            if not os.path.exists(csv_file_path):
                print(f"文件 {csv_file_path} 不存在，跳过该表的导入。")
                continue

            try:
                df = pd.read_csv(csv_file_path)
            except Exception as e:
                print(f"读取文件 {csv_file_path} 时出错：{e}")
                continue

            df = df.replace({np.nan: None})

            placeholders = ', '.join(['%s'] * len(df.columns))
            columns = ', '.join(df.columns)
            sql = f"INSERT IGNORE INTO {table} ({columns}) VALUES ({placeholders})"

            data = df.values.tolist()

            try:
                cursor.executemany(sql, data)
                connection.commit()
                print(f"{table} 数据库导入成功")
            except mysql.connector.Error as err:
                print(f"导入表 {table} 数据时出错：{err}")

    except mysql.connector.Error as err:
        print(f"数据库连接或操作出错：{err}")
    finally:
        if cursor:
            cursor.close()
        connection.close()

if __name__ == "__main__":
    # 使用示例：
    download_task('192.168.16.232', 'EX')
    # upload_task('192.168.16.119', 'default')
    # download_task('192.168.16.119', 'default')

    pass
