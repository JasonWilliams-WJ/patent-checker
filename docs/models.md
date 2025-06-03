# 数据模型

## 草稿v2

方案1：Raw -> Annonated -> Validated
方案2：Raw和Validated合并成一个数据模型，有个状态

### 数据记录

1. 数据标注环节在整个流程中的作用

网页采集（买菜） -> 数据清洗（洗菜） -> 数据标注（） -> 数据精炼（切菜） -> 数据建模（炒菜） -> 数据可视化（装盘）

数据记录 Record: 
- is_collected: 从空-有些变量
- is_cleaned: 有些变量经过加工，或者产生一些转换后的变量
- is_annonated:
- is_xxx: 建模的变量已经准备好


本阶段的记录:
- 状态更新：未标记 -> 已标记
- 待标注字段更新： 空数据（null） -> 有数据（0,1）

数据记录 Record/DataRecord ：一条数据
id, raw, ann, is_validated
0, "我是一个小猫", , 0
1, "我是一个测试数据", "我是一个标记结果", 1

2. 数据标注环节的交付

Record: 实际功能
AnnRecord: 标注记录，如果Record发现问题，可以从标注记录里核查。

Record(state 0)
- Annonator(核心处理器 AI) ->
or 
-> Exporter -> 人工 ->
Annoated -> Validator（辅助处理器） 
-> Record(state 1)


### 数据分发

DataTask表：id, is_finished

TaskRecordRelation表：
record_id, task_id
0,0
1,0
2,0
3,0
4,1

Assigner表：
id, real_name, username, is_active

TaskeAssignerRelation:
task_id, assigner_id

方法：
- register_assigner: 注册一个标注员
- assign_task: 分配一个任务给标注员
- get_assigner_status: 获取标注员当前任务的状态
- import_task_result: 导入标注员标注结果
