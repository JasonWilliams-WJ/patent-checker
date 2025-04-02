"""分割待匹配数据代码，n参数为需要分割的文件数量，check_gap参数为交叉验证的重叠比例"""
import csv
import math
import os

def split_csv(input_path, n, check_gap = 0.2):
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    
    total_rows = len(rows)
    chunk_size = math.ceil(total_rows / n)
    chunks = [rows[i*chunk_size : min((i+1)*chunk_size, total_rows)] for i in range(n)]
    
    output_dir = os.path.splitext(input_path)[0] + "_split"
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(n):
        current_chunk = chunks[i]
        next_idx = (i+1) % n
        overlap_size = math.ceil(len(chunks[next_idx]) * check_gap)
        combined = current_chunk + chunks[next_idx][:overlap_size]
        
        output_path = os.path.join(output_dir, f'part_{i+1}.csv')
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(combined)

# 使用示例
split_csv('data/匹配失败起草单位v4_无专利数据.csv', n=5, check_gap=0.2)