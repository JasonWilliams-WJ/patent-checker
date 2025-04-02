import sqlite3
import typer
import os
import csv
import math
from datetime import datetime
from typing import List, Dict
import pandas as pd

app = typer.Typer()

class TaskManager:
    def __init__(self, db_path="tasks.db"):
        """
        初始化数据库连接、创建表、加载配置，并定义任务状态的常量
        :param db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # 支持字典式访问
        self.cursor = self.conn.cursor()

        # 初始化数据库结构
        self._create_tables()
        self._init_team_config()

        # 状态常量
        self.STATUS = {
            'unassigned': 0,
            'assigned': 1,
            'completed': 2,
            'validated': 3
        }

    def _create_tables(self):
        """创建所有数据库表结构"""
        try:
            self.cursor.execute("PRAGMA foreign_keys = ON")  # 启用外键支持

            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS DataRecord (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                value_preprocessedname TEXT,
                value_keyname TEXT,
                have_patent TEXT,
                now_name TEXT DEFAULT '不存在',
                have_patent_fixed TEXT CHECK(have_patent_fixed IN ('有', '无')),
                patent_publication_number TEXT DEFAULT '无',
                is_validated int DEFAULT 0
            )""")

            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS File (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                FOREIGN KEY (record_id) REFERENCES DataRecord(id) ON DELETE CASCADE
            )""")

            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS DataTask (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL,
                executor TEXT NOT NULL,
                is_masked BOOLEAN DEFAULT 0,
                FOREIGN KEY (file_id) REFERENCES File(file_id) ON DELETE CASCADE
            )""")

            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"数据库初始化失败: {str(e)}")

    def _init_team_config(self):
        """初始化默认团队配置"""
        default_teams = [
            ('group1', 'member', 'member1_g1'),
            ('group1', 'member', 'member2_g1'),
            ('group1', 'deputy', 'deputy_g1'),
            ('group1', 'leader', 'leader_g1'),
            ('group2', 'member', 'member1_g2'),
            ('group2', 'member', 'member2_g2'),
            ('group2', 'deputy', 'deputy_g2'),
            ('group2', 'leader', 'leader_g2')
        ]

        try:
            # 检查是否已存在配置
            self.cursor.execute("SELECT COUNT(*) FROM Teams")
            if self.cursor.fetchone()[0] == 0:
                self.cursor.executemany(
                    "INSERT INTO Teams (group_name, role, member_name) VALUES (?, ?, ?)",
                    default_teams
                )
                self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"团队配置初始化失败: {str(e)}")


    def get_team_config(self, group_name: str = None) -> Dict:
        """获取团队配置"""
        try:
            query = "SELECT group_name, role, member_name FROM Teams"
            params = ()

            if group_name:
                query += " WHERE group_name = ?"
                params = (group_name,)

            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            config = {}
            for row in rows:
                group = row['group_name']
                if group not in config:
                    config[group] = {'members': [], 'deputy': [], 'leader': []}

                if row['role'] == 'member':
                    config[group]['members'].append(row['member_name'])
                elif row['role'] == 'deputy':
                    config[group]['deputy'].append(row['member_name'])
                elif row['role'] == 'leader':
                    config[group]['leader'].append(row['member_name'])

            return config[group_name] if group_name else config
        except sqlite3.Error as e:
            raise RuntimeError(f"获取团队配置失败: {str(e)}")


    def assign_tasks(self, daily_goal: int, group_name: str = 'group1'):
        """分配任务到指定小组"""
        try:
            # 验证小组有效性
            team_config = self.get_team_config(group_name)
            if not team_config:
                raise ValueError(f"无效的小组名称: {group_name}")

            # 获取未分配的记录
            self.cursor.execute(
                "SELECT id, record_data FROM DataRecord "
                "WHERE is_validated = ? LIMIT ?",
                (self.STATUS['unassigned'], daily_goal)
            )
            records = self.cursor.fetchall()

            if not records:
                typer.echo("没有可分配的未处理记录")
                return 0

            actual_goal = len(records)
            if actual_goal < daily_goal:
                typer.echo(f"可用记录不足: 需要 {daily_goal} 条，实际分配 {actual_goal} 条")

            # 计算各角色分配数量
            ratios = {'members': 0.6, 'deputy': 0.25, 'leader': 0.15}
            allocations = {
                role: math.ceil(actual_goal * ratios[role])
                for role in ['members', 'deputy', 'leader']
            }

            # 分配任务给各角色
            record_index = 0

            for role in ['members', 'deputy', 'leader']:
                members = team_config[role]
                if not members:
                    continue

                records_per_member = allocations[role] // len(members)
                extra_records = allocations[role] % len(members)

                for i, member in enumerate(members):
                    assign_count = records_per_member + (1 if i < extra_records else 0)
                    if record_index + assign_count > len(records):
                        assign_count = len(records) - record_index
                    if assign_count <= 0:
                        break

                    # 生成文件ID
                    file_id = f"{datetime.now().strftime('%m%d')}_{member}"

                    # 分配记录
                    for record in records[record_index:record_index + assign_count]:

                        # 增加 File 记录
                        self.cursor.execute(
                            "INSERT OR IGNORE INTO File (file_id, record_id) VALUES (?, ?)",
                            (file_id, record['id'])
                        )

                        # 更新 DataRecord 状态（标记已分配）
                        self.cursor.execute(
                            "UPDATE DataRecord SET is_validated = ? WHERE id = ?",
                            (self.STATUS['assigned'], record['id'])
                        )

                    # 记录任务信息到 DataTask
                    self.cursor.execute(
                        "INSERT INTO DataTask (file_id, executor, is_masked) VALUES (?, ?, ?)",
                        (file_id, member, False)
                    )

                    #导出为csv
                    self._export_file_data_to_csv(file_id)

                    record_index += assign_count
                    if record_index >= len(records):
                        break

            self.conn.commit()

            typer.echo(f"成功分配 {len(records)} 条记录到小组 {group_name}")
            return len(records)

        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"任务分配失败: {str(e)}")
        except Exception as e:
            self.conn.rollback()
            raise

    def _export_file_data_to_csv(self, file_id):
        """将指定file_id的File表数据导出为CSV文件"""
        try:
            # 查询 File 表中与 file_id 相关的数据
            self.cursor.execute(
                "SELECT f.file_id, f.record_id, dr.record_data "
                "FROM File f "
                "JOIN DataRecord dr ON f.record_id = dr.id "
                "WHERE f.file_id = ?",
                (file_id,)
            )
            file_data = self.cursor.fetchall()

            if not file_data:
                raise ValueError(f"没有找到 file_id 为 {file_id} 的记录")

            # 定义文件名
            filename = f"{file_id}.csv"

            # 打开CSV文件并写入数据
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['file_id', 'record_id', 'record_data'])  # CSV表头
                writer.writerows(file_data)  # 写入所有记录数据

            print(f"任务数据已成功导出到 {filename}")

        except Exception as e:
            print(f"导出CSV失败: {str(e)}")

    def mark_tasks_completed(self,  file_ids: List[str]):
        """标记任务为已完成"""
        try:
            if not file_ids:
                raise ValueError("file_ids 不能为空")

            # 验证文件ID有效性
            placeholders = ','.join(['?'] * len(file_ids))
            self.cursor.execute(
                f"SELECT COUNT(*) FROM File WHERE file_id IN ({placeholders})",
                file_ids
            )
            if self.cursor.fetchone()[0] != len(file_ids):
                raise ValueError("包含无效的文件ID")

            # 更新 DataTask，标记任务完成
            self.cursor.execute(
                f"UPDATE DataTask SET is_masked = 1 "
                f"WHERE file_id IN ({placeholders})",
                file_ids
            )

            # 更新 DataRecord，标记数据标记完成（待审核）
            self.cursor.execute(
                f"UPDATE DataRecord SET is_validated = self.STATUS['completed'] "
                f"WHERE id IN (SELECT record_id FROM File WHERE file_id IN ({placeholders}))",
                file_ids
            )

            affected = self.cursor.rowcount
            print(f" 已完成 {affected} 个任务")
            return affected

        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"任务标记失败: {str(e)}")

    def validate_records(self, folder_path: str,output_folder: str):
        """读取助研交上来的csv文件，分配审核任务"""
        try:
            if not os.path.exists(folder_path):
                raise FileNotFoundError(f"文件夹不存在: {folder_path}")

            # 获取团队配置
            team_config = self.get_team_config()
            leader = team_config['group1']['leader'][0]  # 组长
            deputy = team_config['group1']['deputy'][0]  # 副组长
            group_members = set(team_config['group1']['members'])  # 组员列表

            # 创建临时表
            self.cursor.execute("DROP TABLE IF EXISTS Temp_Leader_Review")
            self.cursor.execute("DROP TABLE IF EXISTS Temp_Deputy_Review")

            self.cursor.execute("""
                CREATE TEMP TABLE Temp_Leader_Review (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    count INTEGER DEFAULT 0,
                    value_preprocessedname TEXT,
                    value_keyname TEXT,
                    have_patent TEXT,
                    now_name TEXT DEFAULT '不存在',
                    have_patent_fixed TEXT CHECK(have_patent_fixed IN ('有', '无')),
                    patent_publication_number TEXT DEFAULT '无'
                )
            """)

            self.cursor.execute("""
                CREATE TEMP TABLE Temp_Deputy_Review (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    count INTEGER DEFAULT 0,
                    value_preprocessedname TEXT,
                    value_keyname TEXT,
                    have_patent TEXT,
                    now_name TEXT DEFAULT '不存在',
                    have_patent_fixed TEXT CHECK(have_patent_fixed IN ('有', '无')),
                    patent_publication_number TEXT DEFAULT '无'
                )
            """)



            # 遍历文件夹，分类任务
            member_data = []  # 组员数据

            for file_id in os.listdir(folder_path):
                file_dir = os.path.join(folder_path, file_id)
                if not os.path.isdir(file_dir):  # 只处理文件夹
                    continue

                submitter = self._get_submitter(file_id)  # 获取提交人
                file_content = self._read_csv_files(file_dir,1)  # 读取 CSV 数据

                if submitter == leader:
                    self._insert_into_temp_table("Temp_Deputy_Review", file_content)  # 组长提交 → 副组长审核
                elif submitter == deputy:
                    self._insert_into_temp_table("Temp_Leader_Review", file_content)  # 副组长提交 → 组长审核
                elif submitter in group_members:
                    member_data.extend(file_content)  # 组员提交的数据

            # 组员数据拆分
            if member_data:
                total_records = len(member_data)
                leader_records = (7 * total_records) // 12

                self._insert_into_temp_table("Temp_Leader_Review", member_data[:leader_records])
                self._insert_into_temp_table("Temp_Deputy_Review", member_data[leader_records:])

            self.conn.commit()

            # 导出 CSV
            self._export_table_to_csv("Temp_Leader_Review", os.path.join(output_folder, "leader_review.csv"))
            self._export_table_to_csv("Temp_Deputy_Review", os.path.join(output_folder, "deputy_review.csv"))

            print(f"复核任务分配完成: 组员数据 {len(member_data)} 条")
            print(f"CSV 已导出至 {output_folder}")
            return len(member_data)

        except (sqlite3.Error, FileNotFoundError) as e:
            self.conn.rollback()
            raise RuntimeError(f"验证失败: {str(e)}")

    def _insert_into_temp_table(self, table_name: str, data: list):
        """插入数据到指定的临时表"""
        if not data:
            return

        self.cursor.executemany(
            f"""INSERT INTO {table_name} 
                (record_id, name, count, value_preprocessedname, value_keyname, have_patent, now_name, have_patent_fixed, patent_publication_number) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [(rec["id"], rec["name"], rec["count"], rec["value_preprocessedname"], rec["value_keyname"],
              rec["have_patent"], rec["now_name"], rec["have_patent_fixed"], rec["patent_publication_number"])
             for rec in data]
        )

    def _get_submitter(self, file_id: str):
        """根据 file_id 查询提交人"""
        self.cursor.execute("SELECT executor FROM DataTask WHERE file_id = ?", (file_id,))
        result = self.cursor.fetchone()
        return result["executor"] if result else None

    def _export_table_to_csv(self, table_name: str, output_path: str):
        """导出 SQLite 临时表到 CSV"""
        try:
            self.cursor.execute(f"SELECT * FROM {table_name}")
            columns = [desc[0] for desc in self.cursor.description]  # 获取列名
            rows = self.cursor.fetchall()

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(columns)  # 写入列名
                writer.writerows(rows)  # 写入数据

            print(f"{table_name} 导出成功: {output_path}")

            # 销毁临时表
            self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            self.conn.commit()
            print(f"{table_name} 已销毁")

        except sqlite3.Error as e:
            raise RuntimeError(f"导出 {table_name} 失败: {str(e)}")


    def merge_review_to_datarecord(self, leader_csv: str, deputy_csv: str):
        """将组长和副组长的审核内容合并到 DataRecord 表中，并设置 is_validated 为 1"""
        try:
            # 读取组长 CSV
            leader_data = self._read_csv_files(leader_csv)
            deputy_data = self._read_csv_files(deputy_csv)

            # 合并数据到 DataRecord 表
            all_data = leader_data + deputy_data

            for row in all_data:
                record_id = row['id']
                name = row['name']
                now_name = row['now_name']
                have_patent_fixed = row['have_patent_fixed']
                patent_publication_number = row['patent_publication_number']

                # 更新 DataRecord 表并设置 is_validated 为 1
                self.cursor.execute("""
                    UPDATE DataRecord                     
                    SET now_name = ?, have_patent_fixed = ?, patent_publication_number = ?, 
                        is_validated = 1
                    WHERE id = ? AND name = ?
                """, (now_name,have_patent_fixed, patent_publication_number, record_id, name))

            self.conn.commit()
            print(f"数据成功合并到 DataRecord 表，更新了 {len(all_data)} 条记录，并设置 is_validated 为 1")
        except sqlite3.Error as e:
            self.conn.rollback()
            raise RuntimeError(f"合并失败: {str(e)}")

    def _read_csv_files(self, path: str, is_folder: bool = False):
        """读取 CSV 文件或文件夹内的 CSV 文件，并转换为结构化数据"""
        records = []
        try:
            if is_folder:  # 如果是文件夹，读取文件夹内所有 CSV 文件
                for file_name in sorted(os.listdir(path)):  # 按文件名排序
                    file_path = os.path.join(path, file_name)
                    if os.path.isfile(file_path) and file_name.endswith(".csv"):
                        df = pd.read_csv(file_path, encoding="utf-8")
                        for _, row in df.iterrows():
                            records.append(self._process_row(row))
            else:  # 读取单个 CSV 文件
                with open(path, mode='r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        records.append(row)
        except Exception as e:
            raise RuntimeError(f"读取 CSV 文件失败: {str(e)}")

        return records

    def _process_row(self, row):
        """处理 CSV 行数据"""
        return {
            "record_id": row.get("id"),
            "name": row.get("name", ""),
            "count": row.get("count", 0),
            "value_preprocessedname": row.get("value_preprocessedname", ""),
            "value_keyname": row.get("value_keyname", ""),
            "have_patent": row.get("have_patent", ""),
            "now_name": row.get("now_name", "不存在"),
            "have_patent_fixed": row.get("have_patent_fixed", "无"),
            "patent_publication_number": row.get("patent_publication_number", "无")
        }


manager = TaskManager()

@app.command()
def assign(
    daily_goal: int = typer.Argument(..., help="每日任务目标数量"),
    group: str = typer.Option("group1", help="指定小组名称")
):
    """按固定比例分配任务给团队成员"""
    try:
        manager.assign_tasks(daily_goal, group)
    except Exception as e:
        typer.echo(f"错误: {str(e)}", err=True)
        raise typer.Exit(1)

@app.command()
def complete(
    file_ids: List[str] = typer.Argument(..., help="已完成文件的file_id列表")
):
    """标记任务为已完成"""
    try:
        manager.mark_tasks_completed(file_ids)
    except Exception as e:
        typer.echo(f"错误: {str(e)}", err=True)
        raise typer.Exit(1)

@app.command()
def validate(folder_path: str = typer.Argument("data/待审核文件", help="待验证文件夹路径")):
    """读取助研交上来的csv文件，分配审核任务"""
    try:
        manager.validate_records(folder_path, "data/审核分配.csv")
    except Exception as e:
        typer.echo(f"错误: {str(e)}", err=True)
        raise typer.Exit(1)

@app.command()
def team_list():
    """查看所有团队配置"""
    try:
        config = manager.get_team_config()
        for group, members in config.items():
            typer.echo(f"团队 [{group}]")
            for role, names in members.items():
                typer.echo(f"  {role}: {', '.join(names)}")
    except Exception as e:
        typer.echo(f"错误: {str(e)}", err=True)
        raise typer.Exit(1)

@app.command()
def merge_review(
    leader_csv: str = typer.Option(..., help="组长复核后文件路径"),
    deputy_csv: str = typer.Option(..., help="副组长复核后文件路径")
):
    """将组长和副组长的审核内容合并到 DataRecord 表中，并设置 is_validated 为 1"""
    try:
        manager.merge_review_to_datarecord(leader_csv, deputy_csv)
        typer.echo(f"已将 {leader_csv} 和 {deputy_csv}合并到 DataRecord 表中")
    except Exception as e:
        typer.echo(f"合并失败: {str(e)}")

if __name__ == "__main__":
    try:
        app()
    except Exception as e:
        typer.echo(f"程序运行出错: {str(e)}", err=True)
        raise typer.Exit(1)


