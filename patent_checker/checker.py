"""验收代码，csv_files参数为待匹配数据文件列表，需要与split_data.py中的文件列表顺序一致，check_gap参数为交叉验证的重叠比例"""
import csv
import math
import json
import logging
from logging.handlers import RotatingFileHandler
import time
import os


# 配置日志系统
def setup_logging():
    """配置完整的日志系统"""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # 采集所有级别日志

    # 控制台输出 (简洁格式)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(levelname)-8s %(message)s')
    console_handler.setFormatter(console_format)

    # 文件输出 (详细格式+自动轮转)
    file_handler = RotatingFileHandler(
        'patent_validation.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_format = logging.Formatter(
        '%(asctime)s [%(levelname)-7s] %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


# 初始化日志系统
setup_logging()


def create_authorization_dict(json_path):
    """创建授权号字典 - 增强错误处理和性能监控"""
    start_time = time.perf_counter()

    try:
        logging.info("开始读取专利申请人数据: %s", json_path)

        # 检查文件存在性
        if not os.path.exists(json_path):
            logging.error("文件不存在: %s", json_path)
            return {}

        # 读取JSON文件
        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        # 创建字典
        auth_dict = {item['授权公告号']: item for item in data}

        elapsed = time.perf_counter() - start_time
        logging.info("专利申请人数据读取完毕 | 记录数: %d | 耗时: %.3f秒",
                     len(auth_dict), elapsed)
        return auth_dict

    except FileNotFoundError:
        logging.exception("找不到文件: %s", json_path)
        return {}
    except json.JSONDecodeError:
        logging.exception("JSON文件格式不正确: %s", json_path)
        return {}
    except Exception as e:
        logging.exception("读取专利申请人数据时发生意外错误: %s", str(e))
        return {}


def validate_files(csv_files, check_gap=0.2, auth_dict_path="patent-checker-main/data/raw/专利申请人.json"):
    """执行专利数据验证工作流"""
    logging.info("=" * 70)
    logging.info("开始专利数据验证流程")
    logging.info("文件数量: %d | 验证重叠率: %.0f%%",
                 len(csv_files), check_gap * 100)
    logging.info("系统时间: %s", time.strftime("%Y-%m-%d %H:%M:%S"))
    logging.info("=" * 70)

    start_time = time.time()
    total_existence_rate = 0.0
    total_consistency_rate = 0.0

    # 加载授权字典
    global auth_dict
    auth_dict = create_authorization_dict(auth_dict_path)
    if not auth_dict:
        logging.critical("无法继续: 专利申请人字典为空")
        return

    # 检查文件路径
    missing_files = [f for f in csv_files if not os.path.exists(f)]
    if missing_files:
        logging.warning("以下文件缺失: %s", ", ".join(missing_files))
        csv_files = [f for f in csv_files if f not in missing_files]
        if not csv_files:
            logging.error("所有文件均不存在")
            return

    # 生成环形文件列表用于处理最后一个文件
    circular_files = csv_files + [csv_files[0]]

    # 处理每个文件
    processed_files = 0
    for i, file_path in enumerate(csv_files):
        file_start = time.time()
        logging.info("处理文件 [%d/%d]: %s", i + 1, len(csv_files), file_path)

        # 读取当前文件
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                current_rows = list(reader)
                logging.debug("读取到 %d 条记录", len(current_rows))

        except UnicodeDecodeError:
            logging.exception("文件编码问题: %s", file_path)
            continue
        except Exception as e:
            logging.exception("读取文件失败: %s", file_path)
            continue

        if not current_rows:
            logging.warning("文件为空: %s", file_path)
            continue

        # 验证存在率
        exist_count = 0
        missing_numbers = []

        for row_idx, row in enumerate(current_rows, 1):
            pub_num = row.get("patent_publication_number")
            if not pub_num:
                logging.debug("第 %d 行缺少专利号", row_idx)
                continue

            if pub_num in auth_dict:
                exist_count += 1
            else:
                missing_numbers.append(pub_num)

        existence_rate = exist_count / len(current_rows)
        total_existence_rate += existence_rate

        # 记录缺失率高的文件
        if existence_rate < 0.6:
            logging.warning("低专利存在率: %.2f%%", existence_rate * 100)
            if missing_numbers:
                logging.debug("前3个缺失专利号: %s", ", ".join(missing_numbers[:3]))

        # 读取下一个文件的前20%
        next_file = circular_files[i + 1]
        logging.debug("交叉验证来源: %s (前%.0f%%)", next_file, check_gap * 100)

        try:
            with open(next_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                next_rows = list(reader)

            if not next_rows:
                logging.warning("交叉验证文件为空: %s", next_file)
                consistency_rate = 0
            else:
                chunk_size = math.ceil(len(next_rows) * check_gap)
                next_chunk = next_rows[:chunk_size]
                name_mapping = {row["name"]: row["have_patent_fixed"] for row in next_chunk}

                # 交叉验证
                valid_count = 0
                match_count = 0
                mismatch_names = []

                for row in current_rows:
                    if row["name"] in name_mapping:
                        match_count += 1
                        if row["have_patent_fixed"] == name_mapping[row["name"]]:
                            valid_count += 1
                        elif valid_count == 0:  # 只记录前2个不匹配
                            mismatch_names.append(row["name"])

                if match_count:
                    consistency_rate = valid_count / match_count
                    total_consistency_rate += consistency_rate

                    # 记录低一致性文件
                    if consistency_rate < 0.9:
                        logging.warning("交叉验证一致率低: %.2f%%", consistency_rate * 100)
                        if mismatch_names:
                            logging.debug("不一致的名称: %s", ", ".join(mismatch_names[:2]))
                else:
                    consistency_rate = 0
                    logging.warning("无匹配记录进行交叉验证")

        except FileNotFoundError:
            logging.error("交叉验证文件不存在: %s", next_file)
            consistency_rate = 0
        except KeyError as e:
            logging.error("CSV缺少关键字段: %s in %s", str(e), next_file)
            consistency_rate = 0
        except Exception as e:
            logging.exception("处理交叉验证文件失败: %s", next_file)
            consistency_rate = 0

        # 文件耗时统计
        file_time = time.time() - file_start
        logging.info("文件统计 | 专利存在率: %.2f%% | 交叉验证一致率: %.2f%% | 耗时: %.2f秒",
                     existence_rate * 100, consistency_rate * 100, file_time)
        processed_files += 1

    # 输出平均值
    if processed_files:
        avg_existence = total_existence_rate / processed_files
        avg_consistency = total_consistency_rate / processed_files

        total_time = time.time() - start_time
        logging.info("=" * 70)
        logging.info("验证完成 | 文件数: %d | 总耗时: %.2f秒", processed_files, total_time)
        logging.info("平均统计:")
        logging.info("平均专利存在率: %.2f%%", avg_existence * 100)
        logging.info("平均交叉验证一致率: %.2f%%", avg_consistency * 100)
        logging.info("=" * 70)

        return {"avg_existence_rate": avg_existence,
                "avg_consistency_rate": avg_consistency}
    else:
        logging.error("未成功处理任何文件")
        return None


# 使用示例
if __name__ == "__main__":
    # 文件列表
    csv_files = [
        "patent-checker-main/data/匹配失败起草单位v4_无专利数据_split/1组邓玉杰最终版.csv",
    ]

    # 执行验证
    results = validate_files(csv_files)

    if results:
        logging.info("验证成功完成 | 平均专利存在率: %.2f%% | 平均交叉验证一致率: %.2f%%",
                     results["avg_existence_rate"] * 100,
                     results["avg_consistency_rate"] * 100)
    else:
        logging.error("验证过程失败")
