import json
import pandas as pd

print ("开始读取专利申请人数据")
def create_authorization_dict():
    try:
        with open("data/专利申请人.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
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
    return target_number in auth_dict

def process_csv_file(csv_file):
    count_now_name = 0
    count_have_patent_fixed = 0
    count_patent_publication_number = 0
    success_patent_publication_number = 0
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = pd.read_csv(file)
        for index, row in reader.iterrows():
            now_name = row['now_name']
            if now_name:
                count_now_name += 1
            patent_fixed = row['patent_fixed']
            if patent_fixed:
                count_have_patent_fixed += 1
            patent_publication_number = row['patent_publication_number']
            if patent_publication_number:
                count_patent_publication_number += 1
                if check_authorization_number(patent_publication_number):
                    success_patent_publication_number += 1
    return count_now_name, count_have_patent_fixed, count_patent_publication_number, success_patent_publication_number

def main ():
    # 此处文件路径填写需要检查的文件路径
    csv_file = "example.csv"
    count_now_name, count_have_patent_fixed, count_patent_publication_number, success_patent_publication_number = process_csv_file(csv_file)
    print(f"当前名称数量: {count_now_name} / 50")
    print(f"有专利数量: {count_have_patent_fixed} / 50")
    print(f"专利公开号数量: {count_patent_publication_number} / 50")
    print(f"专利公开号有效率: {success_patent_publication_number} / {count_patent_publication_number}")

if __name__ == "__main__":
    main()