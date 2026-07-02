import os
import pandas as pd
import numpy as np
import mysql.connector

def download_task():
    # 数据库连接信息
    connection = mysql.connector.connect(
        host='192.168.16.178',
        user='root',
        password='root',
        database='youicompass'
    )

    # 表名列表
    tables = ['mission', 'mission_action', 'mission_work', 'mission_work_action', 'mission_action_parameter']

    try:
        for table in tables:
            # 查询表数据
            query = f"SELECT * FROM {table}"
            df = pd.read_sql(query, connection)
            
            # 导出为CSV文件
            df.to_csv(f"mission/{table}.csv", index=False)
            print(f"Table {table} exported successfully.")

    finally:
        # 关闭连接
        connection.close()

# def clear_tables(
#     host: str,
#     user: str,
#     password: str,
#     database: str,
#     tables: list
# ):
#     """
#     清空指定数据库中的表数据
#     """
#     connection = mysql.connector.connect(
#         host=host,
#         user=user,
#         password=password,
#         database=database
#     )

#     cursor = connection.cursor()

#     try:
#         # 关闭外键检查，避免 truncate 失败
#         cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

#         for table in tables:
#             sql = f"TRUNCATE TABLE `{table}`;"
#             cursor.execute(sql)
#             print(f"表 {table} 已清空")

#         # 恢复外键检查
#         cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
#         connection.commit()

#     except Exception as e:
#         connection.rollback()
#         raise e

#     finally:
#         cursor.close()
#         connection.close()


def upload_task():

    # 目标数据库连接信息
    connection = mysql.connector.connect(
        host="192.168.16.177",
        user='root',
        password='root',
        database='youicompass'
    )

    # 表名列表
    tables = ['mission', 'mission_action', 'mission_work', 'mission_work_action', 'mission_action_parameter']

    # clear_tables(
    #     host="192.168.16.177",
    #     user='root',
    #     password='root',
    #     database='youicompass',
    #     tables=tables
    # )

    try:
        cursor = connection.cursor()

        # 获取脚本运行的当前路径
        current_path = os.getcwd()

        for table in tables:
            # 拼接 CSV 文件的完整路径
            csv_file_path = os.path.join(current_path, "mission", f"{table}.csv")

            # 检查 CSV 文件是否存在
            if not os.path.exists(csv_file_path):
                print(f"文件 {csv_file_path} 不存在，跳过该表的导入。")
                continue

            # 从 CSV 文件加载数据
            try:
                df = pd.read_csv(csv_file_path)
            except Exception as e:
                print(f"读取文件 {csv_file_path} 时出错：{e}")
                continue

            # 替换 NaN 值为 None，以适配 MySQL 的插入要求
            df = df.replace({np.nan: None})

            # 生成插入 SQL 语句
            placeholders = ', '.join(['%s'] * len(df.columns))
            columns = ', '.join(df.columns)
            sql = f"INSERT IGNORE INTO {table} ({columns}) VALUES ({placeholders})"

            # 将 DataFrame 数据转换为列表形式
            data = df.values.tolist()

            # 执行批量插入操作
            try:
                cursor.executemany(sql, data)
                connection.commit()
                print(f"{table} 数据库导入成功")
            except mysql.connector.Error as err:
                print(f"导入表 {table} 数据时出错：{err}")

    except mysql.connector.Error as err:
        print(f"数据库连接或操作出错：{err}")
    finally:
        # 关闭游标和连接
        if cursor:
            cursor.close()
        connection.close()

if __name__ == "__main__":
    # upload_task()
    download_task()