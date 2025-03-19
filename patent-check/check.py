"""验收代码，csv_files参数为待匹配数据文件列表，需要与split_data.py中的文件列表顺序一致，check_gap参数为交叉验证的重叠比例"""
import csv
import math
import json

print ("开始读取专利申请人数据")
def create_authorization_dict():
    try:
        # 读取JSON文件并创建字典
        with open("data/专利申请人.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
            # 创建以授权公告号为key的字典
            return {item['授权公告号']: item for item in data}
    
    except FileNotFoundError:
        print("错误：找不到文件 专利申请人.json")
        return {}
    except json.JSONDecodeError:
        print("错误：JSON文件格式不正确")
        return {}
    except Exception as e:
        print(f"发生错误：{str(e)}")
        return {}
    return {}

auth_dict = create_authorization_dict()
print ("读取专利申请人数据完毕")

def check_authorization_number(target_number):
    # 直接通过字典查找，时间复杂度为 O(1)
    return target_number in auth_dict

def validate_files(csv_files, check_gap = 0.2):
    total_existence_rate = 0.0
    total_consistency_rate = 0.0
    
    # 生成环形文件列表用于处理最后一个文件
    circular_files = csv_files + [csv_files[0]]
    
    for i, file_path in enumerate(csv_files):
        # 读取当前文件
        with open(file_path, 'r', encoding = 'utf-8-sig') as f:
            reader = csv.DictReader(f)
            current_rows = list(reader)
            
            # 验证存在率
            exist_count = 0
            for row in current_rows:
                if check_authorization_number(row["patent_publication_number"]):
                    exist_count += 1
            existence_rate = exist_count / len(current_rows)
            
        # 读取下一个文件的前20%
        next_file = circular_files[i+1]
        with open(next_file, 'r', encoding = 'utf-8-sig') as f:
            reader = csv.DictReader(f)
            next_rows = list(reader)
            chunk_size = math.ceil(len(next_rows) * check_gap)
            next_chunk = next_rows[:chunk_size]
            name_mapping = {row["name"]: row["have_patent_fixed"] for row in next_chunk}
            
        # 交叉验证
        valid_count = 0
        match_count = 0
        for row in current_rows:
            if row["name"] in name_mapping:
                match_count += 1
                if row["have_patent_fixed"] == name_mapping[row["name"]]:
                    valid_count += 1
        consistency_rate = valid_count / match_count if match_count > 0 else 0
        
        # 输出结果
        print(f"文件 {file_path}:")
        print(f"• 专利存在率: {existence_rate:.2%}")
        print(f"• 交叉验证一致率: {consistency_rate:.2%}\n")
        
        # 累加统计
        total_existence_rate += existence_rate
        total_consistency_rate += consistency_rate
        
    # 输出平均值
    avg_existence = total_existence_rate / len(csv_files)
    avg_consistency = total_consistency_rate / len(csv_files)
    print(f"平均值统计:")
    print(f"• 平均专利存在率: {avg_existence:.2%}")
    print(f"• 平均交叉验证一致率: {avg_consistency:.2%}")

# 使用示例
if __name__ == "__main__":
    # 假设授权号字典和文件列表已定义
    csv_files = ["data/匹配失败起草单位v4_无专利数据_split/part_1.csv", "data/匹配失败起草单位v4_无专利数据_split/part_2.csv", "data/匹配失败起草单位v4_无专利数据_split/part_3.csv", "data/匹配失败起草单位v4_无专利数据_split/part_4.csv", "data/匹配失败起草单位v4_无专利数据_split/part_5.csv"]  # 文件路径列表
    
    validate_files(csv_files)