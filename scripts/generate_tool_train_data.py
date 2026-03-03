#!/usr/bin/env python3
"""
生成束流分析工具的 train.jsonl 训练数据
每个工具生成 10 个问题，格式与 train.jsonl 一致
"""

import json
import os
import sys

# 添加项目根路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import TOOLS

# 若 RAG 未加载，尝试单独导入 RAG 工具定义，保证训练数据完整
try:
    from knowledge.rag_tool import RAG_TOOLS as _RAG
    names = [t.get("function", {}).get("name") for t in TOOLS if isinstance(t, dict)]
    if "explain_diagnosis_features" not in names:
        TOOLS = list(TOOLS) + list(_RAG)
except Exception:
    pass

# =============================================================================
# 每个工具的问题、tool_call 参数、模拟的 tool_response、期望的 assistant 回复
# =============================================================================

TRAIN_SAMPLES = {
    "query_beam_data": [
        {
            "question": "查询2025年8月31日凌晨2点到3点的束流数据",
            "tool_call": {"name": "query_beam_data", "arguments": {"start_time": "2025-08-31 02:00:00", "end_time": "2025-08-31 03:00:00"}},
            "tool_response": {"success": True, "summary": {"matched_records": 120, "returned_records": 20}, "data": [{"时间": "2025-08-31 02:00:00", "target": 0.85}]},
            "assistant": "已查询到2025年8月31日02:00-03:00时间段的束流数据，共匹配120条记录，返回前20条。数据显示该时段束流强度（target）均值约0.85，数据正常。"
        },
        {
            "question": "帮我看看8月31号上午10点到11点之间的target和feature1数据",
            "tool_call": {"name": "query_beam_data", "arguments": {"start_time": "2025-08-31 10:00:00", "end_time": "2025-08-31 11:00:00", "columns": ["时间", "target", "feature1"]}},
            "tool_response": {"success": True, "summary": {"matched_records": 60}, "data": [{"时间": "2025-08-31 10:00:00", "target": 0.92, "feature1": 12.5}]},
            "assistant": "已查询到8月31日10:00-11:00的target和feature1数据，共60条记录。该时段target均值约0.92，feature1约12.5，数据在正常范围内。"
        },
        {
            "question": "昨天下午3点到4点的束流数据有异常吗？先查一下数据",
            "tool_call": {"name": "query_beam_data", "arguments": {"start_time": "2025-08-30 15:00:00", "end_time": "2025-08-30 16:00:00", "include_statistics": True}},
            "tool_response": {"success": True, "statistics": {"target_mean": 0.78, "target_std": 0.05}, "data": []},
            "assistant": "已查询到8月30日15:00-16:00的束流数据。该时段target均值为0.78，标准差0.05。如需进一步判断是否异常，可调用异常检测工具。"
        },
        {
            "question": "给我看一下最近一小时的束流数据，只要前10条",
            "tool_call": {"name": "query_beam_data", "arguments": {"start_time": "2025-08-31 01:00:00", "end_time": "2025-08-31 02:00:00", "limit": 10}},
            "tool_response": {"success": True, "summary": {"returned_records": 10}, "data": []},
            "assistant": "已查询到最近一小时的束流数据，共返回10条记录。数据已按时间顺序排列，您可据此进行趋势分析。"
        },
        {
            "question": "查询2025-08-31T14:00:00到15:00:00的束流数据",
            "tool_call": {"name": "query_beam_data", "arguments": {"start_time": "2025-08-31T14:00:00", "end_time": "2025-08-31 15:00:00"}},
            "tool_response": {"success": True, "summary": {"matched_records": 60}, "data": []},
            "assistant": "已查询到2025年8月31日14:00-15:00的束流数据，共60条记录。数据格式支持ISO时间格式。"
        },
        {
            "question": "我想做趋势分析，先取8月31日全天数据的前50条",
            "tool_call": {"name": "query_beam_data", "arguments": {"start_time": "2025-08-31 00:00:00", "end_time": "2025-08-31 23:59:59", "limit": 50}},
            "tool_response": {"success": True, "summary": {"matched_records": 1440, "returned_records": 50}, "data": []},
            "assistant": "已查询到8月31日全天的束流数据，共匹配1440条，返回前50条供趋势分析使用。"
        },
        {
            "question": "异常诊断前需要确认数据，查一下9月1日早上8点到9点的数据",
            "tool_call": {"name": "query_beam_data", "arguments": {"start_time": "2025-09-01 08:00:00", "end_time": "2025-09-01 09:00:00"}},
            "tool_response": {"success": True, "summary": {"matched_records": 60}, "data": []},
            "assistant": "已查询到9月1日08:00-09:00的束流数据，共60条记录。数据已确认，可进行后续异常诊断。"
        },
        {
            "question": "查2025年8月31日12:00到13:00的target统计信息",
            "tool_call": {"name": "query_beam_data", "arguments": {"start_time": "2025-08-31 12:00:00", "end_time": "2025-08-31 13:00:00", "include_statistics": True}},
            "tool_response": {"success": True, "statistics": {"target_mean": 0.88, "target_max": 0.95, "target_min": 0.82, "target_std": 0.03}, "data": []},
            "assistant": "该时段target统计：均值0.88，最大值0.95，最小值0.82，标准差0.03。"
        },
        {
            "question": "核对一下8月30日晚上8点到9点的数据是否完整",
            "tool_call": {"name": "query_beam_data", "arguments": {"start_time": "2025-08-30 20:00:00", "end_time": "2025-08-30 21:00:00"}},
            "tool_response": {"success": True, "summary": {"matched_records": 60, "dataset_time_range": {"start": "2025-08-01 00:00:00", "end": "2025-09-01 00:00:00"}}, "data": []},
            "assistant": "已核对8月30日20:00-21:00的数据，该时段共60条记录，与预期采样频率一致，数据完整。"
        },
        {
            "question": "取8月31日16点到17点，只要时间、target和feature3这三列",
            "tool_call": {"name": "query_beam_data", "arguments": {"start_time": "2025-08-31 16:00:00", "end_time": "2025-08-31 17:00:00", "columns": ["时间", "target", "feature3"]}},
            "tool_response": {"success": True, "summary": {"selected_columns": ["时间", "target", "feature3"]}, "data": []},
            "assistant": "已查询到指定时间段的束流数据，仅包含时间、target和feature3三列，共60条记录。"
        },
    ],
    "get_data_info": [
        {
            "question": "数据集有哪些列？时间范围是多少？",
            "tool_call": {"name": "get_data_info", "arguments": {}},
            "tool_response": {"success": True, "data_info": {"columns": ["时间", "target", "feature1", "feature2"], "total_records": 10000, "time_range": {"start": "2025-08-01 00:00:00", "end": "2025-09-01 00:00:00"}}},
            "assistant": "数据集共10000条记录，时间范围为2025-08-01至2025-09-01。列包括：时间、target、feature1、feature2等。"
        },
        {
            "question": "首次使用，先了解一下数据的基本信息",
            "tool_call": {"name": "get_data_info", "arguments": {"include_target_stats": True, "include_sample": True}},
            "tool_response": {"success": True, "data_info": {"total_records": 10000, "target_stats": {"mean": 0.85, "max": 0.98, "min": 0.72}}, "sample": [{"时间": "2025-08-01 00:00:00", "target": 0.85}]},
            "assistant": "数据集共10000条记录，target均值0.85、最大0.98、最小0.72。已提供前几条样本供您参考。"
        },
        {
            "question": "数据里有多少条记录？有哪些特征列？",
            "tool_call": {"name": "get_data_info", "arguments": {}},
            "tool_response": {"success": True, "data_info": {"total_records": 10000, "columns": ["时间", "target", "feature1", "feature2", "feature3"]}},
            "assistant": "数据集共10000条记录，特征列包括feature1、feature2、feature3等，另有时间列和target列。"
        },
        {
            "question": "查询前能先告诉我数据的时间跨度吗？",
            "tool_call": {"name": "get_data_info", "arguments": {"include_sample": False}},
            "tool_response": {"success": True, "data_info": {"time_range": {"start": "2025-08-01 00:00:00", "end": "2025-09-01 00:00:00"}}},
            "assistant": "数据时间跨度为2025年8月1日至2025年9月1日。"
        },
        {
            "question": "target列的统计信息是什么？",
            "tool_call": {"name": "get_data_info", "arguments": {"include_target_stats": True, "include_sample": False}},
            "tool_response": {"success": True, "data_info": {"target_stats": {"mean": 0.85, "max": 0.98, "min": 0.72, "std": 0.08}}},
            "assistant": "target列统计：均值0.85，最大值0.98，最小值0.72，标准差0.08。"
        },
        {
            "question": "给我看几条样本数据",
            "tool_call": {"name": "get_data_info", "arguments": {"include_sample": True, "sample_size": 5}},
            "tool_response": {"success": True, "sample": [{"时间": "2025-08-01 00:00:00", "target": 0.85, "feature1": 12.0}]},
            "assistant": "已提供5条样本数据，包含时间、target及各特征列，供您了解数据格式。"
        },
        {
            "question": "确定一下可用的列名，方便后续查询",
            "tool_call": {"name": "get_data_info", "arguments": {}},
            "tool_response": {"success": True, "data_info": {"columns": ["时间", "target", "feature1", "feature2", "feature3", "feature4"]}},
            "assistant": "可用列名包括：时间、target、feature1、feature2、feature3、feature4。查询时可直接指定这些列。"
        },
        {
            "question": "数据集的元信息有哪些？",
            "tool_call": {"name": "get_data_info", "arguments": {}},
            "tool_response": {"success": True, "data_info": {"total_records": 10000, "time_column": "时间", "target_column": "target"}},
            "assistant": "数据集元信息：总记录数10000，时间列名为「时间」，目标列名为「target」。"
        },
        {
            "question": "在查具体数据前，先获取数据概览",
            "tool_call": {"name": "get_data_info", "arguments": {"include_target_stats": True, "include_sample": True, "sample_size": 3}},
            "tool_response": {"success": True, "data_info": {}, "sample": []},
            "assistant": "已获取数据概览，包括总记录数、时间范围、列名及target统计。建议在首次查询前调用此接口。"
        },
        {
            "question": "有哪些变量可以用于异常诊断？",
            "tool_call": {"name": "get_data_info", "arguments": {}},
            "tool_response": {"success": True, "data_info": {"columns": ["时间", "target", "feature1", "feature2", "feature3"]}},
            "assistant": "除时间、target外，可用于异常诊断的特征变量有feature1、feature2、feature3等。"
        },
    ],
    "detect_anomaly": [
        {
            "question": "2025年8月31日凌晨2点到3点这段时间有异常吗？",
            "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": "2025-08-31 02:00:00", "end_time": "2025-08-31 03:00:00"}},
            "tool_response": {"success": True, "is_anomaly": False, "anomaly_ratio": 0.0, "prediction_mean": 0.85, "normal_mean": 0.85, "normal_std": 0.05},
            "assistant": "该时段未检测到异常。预测均值0.85与正常均值一致，异常比例为0。"
        },
        {
            "question": "检测8月31日10点到11点是否存在异常",
            "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": "2025-08-31 10:00:00", "end_time": "2025-08-31 11:00:00"}},
            "tool_response": {"success": True, "is_anomaly": True, "anomaly_ratio": 0.15, "prediction_mean": 0.72, "normal_mean": 0.85, "normal_std": 0.05},
            "assistant": "检测到异常。该时段预测均值0.72，低于正常均值0.85，异常比例约15%，建议进行异常诊断。"
        },
        {
            "question": "8月30日下午3点到4点束流正常吗？",
            "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": "2025-08-30 15:00:00", "end_time": "2025-08-30 16:00:00"}},
            "tool_response": {"success": True, "is_anomaly": False, "anomaly_ratio": 0.02, "prediction_mean": 0.86, "normal_mean": 0.85, "normal_std": 0.05},
            "assistant": "该时段基本正常，异常比例仅2%，预测均值0.86与正常水平接近。"
        },
        {
            "question": "用3σ判据判断9月1日早上8点到9点有没有异常",
            "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": "2025-09-01 08:00:00", "end_time": "2025-09-01 09:00:00"}},
            "tool_response": {"success": True, "is_anomaly": False, "anomaly_ratio": 0.0, "prediction_mean": 0.84, "normal_mean": 0.85, "normal_std": 0.05},
            "assistant": "基于3σ工程判据，该时段无异常，预测值在正常范围内。"
        },
        {
            "question": "2025-08-31T14:00:00到15:00:00这段时间检测一下异常",
            "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": "2025-08-31T14:00:00", "end_time": "2025-08-31 15:00:00"}},
            "tool_response": {"success": True, "is_anomaly": True, "anomaly_ratio": 0.25, "prediction_mean": 0.68, "normal_mean": 0.85, "normal_std": 0.05},
            "assistant": "检测到异常。该时段预测均值0.68，明显低于正常值，异常比例约25%，建议进一步诊断原因。"
        },
        {
            "question": "帮我看看昨天中午12点到1点有没有问题",
            "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": "2025-08-30 12:00:00", "end_time": "2025-08-30 13:00:00"}},
            "tool_response": {"success": True, "is_anomaly": False, "anomaly_ratio": 0.0, "prediction_mean": 0.87, "normal_mean": 0.85, "normal_std": 0.05},
            "assistant": "昨天12:00-13:00时段无异常，预测均值0.87，在正常范围内。"
        },
        {
            "question": "回归预测偏差是否显示8月31日晚上7点到8点有异常？",
            "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": "2025-08-31 19:00:00", "end_time": "2025-08-31 20:00:00"}},
            "tool_response": {"success": True, "is_anomaly": True, "anomaly_ratio": 0.18, "prediction_mean": 0.71, "normal_mean": 0.85, "normal_std": 0.05},
            "assistant": "是的，回归预测偏差显示该时段存在异常，预测均值0.71，偏离正常值，异常比例约18%。"
        },
        {
            "question": "判断8月31日全天是否有异常时段",
            "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": "2025-08-31 00:00:00", "end_time": "2025-08-31 23:59:59"}},
            "tool_response": {"success": True, "is_anomaly": True, "anomaly_ratio": 0.08, "prediction_mean": 0.82, "normal_mean": 0.85, "normal_std": 0.05},
            "assistant": "全天检测到异常，整体异常比例约8%，预测均值0.82略低于正常。建议按小时分段检测以定位具体异常时段。"
        },
        {
            "question": "8月31日早上6点到7点束流状态如何？",
            "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": "2025-08-31 06:00:00", "end_time": "2025-08-31 07:00:00"}},
            "tool_response": {"success": True, "is_anomaly": False, "anomaly_ratio": 0.0, "prediction_mean": 0.86, "normal_mean": 0.85, "normal_std": 0.05},
            "assistant": "该时段束流状态正常，预测均值0.86，无异常点。"
        },
        {
            "question": "检测9月1日0点到1点是否存在异常",
            "tool_call": {"name": "detect_anomaly", "arguments": {"start_time": "2025-09-01 00:00:00", "end_time": "2025-09-01 01:00:00"}},
            "tool_response": {"success": True, "is_anomaly": False, "anomaly_ratio": 0.01, "prediction_mean": 0.84, "normal_mean": 0.85, "normal_std": 0.05},
            "assistant": "该时段基本正常，异常比例约1%，可视为在正常波动范围内。"
        },
    ],
    "diagnose_by_statistical_difference": [
        {
            "question": "用统计差异方法诊断8月31日10点到11点的异常，正常时段取8月30日10点到11点",
            "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": "2025-08-31 10:00:00", "anomaly_end": "2025-08-31 11:00:00", "normal_start": "2025-08-30 10:00:00", "normal_end": "2025-08-30 11:00:00", "top_k": 10}},
            "tool_response": {"method": "statistical_difference", "top_features": [{"feature": "feature4", "z_score": 3.2}, {"feature": "feature5", "z_score": 2.8}]},
            "assistant": "统计差异诊断结果显示，偏移最显著的特征为feature4（Z-score 3.2）和feature5（Z-score 2.8），建议重点排查这两个变量。"
        },
        {
            "question": "Z-score方法诊断异常时段8月31日14:00-15:00，正常基准8月30日14:00-15:00",
            "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": "2025-08-31 14:00:00", "anomaly_end": "2025-08-31 15:00:00", "normal_start": "2025-08-30 14:00:00", "normal_end": "2025-08-30 15:00:00"}},
            "tool_response": {"method": "statistical_difference", "top_features": [{"feature": "feature3", "z_score": 4.1}, {"feature": "feature6", "z_score": 3.5}]},
            "assistant": "Z-score诊断显示feature3和feature6偏移最显著，Z-score分别为4.1和3.5，可能是异常主要原因。"
        },
        {
            "question": "比较异常时段和正常时段，找出偏移最大的前5个特征",
            "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": "2025-08-31 19:00:00", "anomaly_end": "2025-08-31 20:00:00", "normal_start": "2025-08-30 19:00:00", "normal_end": "2025-08-30 20:00:00", "top_k": 5}},
            "tool_response": {"method": "statistical_difference", "top_features": [{"feature": "feature5", "z_score": 3.8}, {"feature": "feature7", "z_score": 3.2}]},
            "assistant": "前5个偏移最显著的特征为feature5（Z-score 3.8）、feature7（Z-score 3.2）等，建议优先检查这些变量。"
        },
        {
            "question": "统计差异诊断：异常8月31日08:00-09:00，正常8月30日08:00-09:00",
            "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": "2025-08-31 08:00:00", "anomaly_end": "2025-08-31 09:00:00", "normal_start": "2025-08-30 08:00:00", "normal_end": "2025-08-30 09:00:00"}},
            "tool_response": {"method": "statistical_difference", "top_features": [{"feature": "feature1", "z_score": 2.9}]},
            "assistant": "统计差异诊断显示feature1偏移最显著（Z-score 2.9），可能与抑制电源电压有关。"
        },
        {
            "question": "用正常工况8月29日全天做基准，诊断8月31日12点到13点的异常特征",
            "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": "2025-08-31 12:00:00", "anomaly_end": "2025-08-31 13:00:00", "normal_start": "2025-08-29 00:00:00", "normal_end": "2025-08-29 23:59:59"}},
            "tool_response": {"method": "statistical_difference", "top_features": [{"feature": "feature4", "z_score": 3.5}, {"feature": "feature10", "z_score": 3.0}]},
            "assistant": "以8月29日正常工况为基准，异常时段最显著偏移特征为feature4（加速电源电流）和feature10（C2电源电压）。"
        },
        {
            "question": "诊断异常时段各变量相对正常时段的分布差异，返回top10",
            "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": "2025-08-31 16:00:00", "anomaly_end": "2025-08-31 17:00:00", "normal_start": "2025-08-30 16:00:00", "normal_end": "2025-08-30 17:00:00", "top_k": 10}},
            "tool_response": {"method": "statistical_difference", "top_features": [{"feature": "feature6", "z_score": 3.9}, {"feature": "feature8", "z_score": 3.1}]},
            "assistant": "诊断完成，feature6（灯丝电源电流）和feature8（引出电源电流）分布差异最大，Z-score分别为3.9和3.1。"
        },
        {
            "question": "异常2025-09-01 06:00-07:00，正常2025-08-31 06:00-07:00，做统计差异分析",
            "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": "2025-09-01 06:00:00", "anomaly_end": "2025-09-01 07:00:00", "normal_start": "2025-08-31 06:00:00", "normal_end": "2025-08-31 07:00:00"}},
            "tool_response": {"method": "statistical_difference", "top_features": [{"feature": "feature14", "z_score": 2.7}, {"feature": "feature15", "z_score": 2.5}]},
            "assistant": "统计差异分析显示，对中X偏移电源相关变量（feature14、feature15）偏移较显著，建议检查对中系统。"
        },
        {
            "question": "识别异常状态下发生显著偏移的关键变量",
            "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": "2025-08-31 20:00:00", "anomaly_end": "2025-08-31 21:00:00", "normal_start": "2025-08-30 20:00:00", "normal_end": "2025-08-30 21:00:00", "top_k": 10}},
            "tool_response": {"method": "statistical_difference", "top_features": [{"feature": "feature3", "z_score": 4.2}, {"feature": "feature4", "z_score": 3.6}]},
            "assistant": "异常状态下显著偏移的关键变量为feature3（加速电源电压）和feature4（加速电源电流），Z-score均超过3。"
        },
        {
            "question": "比较异常与正常时段，找出Z-score最大的特征",
            "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": "2025-08-31 22:00:00", "anomaly_end": "2025-08-31 23:00:00", "normal_start": "2025-08-30 22:00:00", "normal_end": "2025-08-30 23:00:00"}},
            "tool_response": {"method": "statistical_difference", "top_features": [{"feature": "feature33", "z_score": 3.4}, {"feature": "feature34", "z_score": 3.0}]},
            "assistant": "Z-score最大的特征为feature33（冷水机压力）和feature34（冷水机内部温度），可能与冷却系统有关。"
        },
        {
            "question": "统计差异方法诊断，异常时段9月1日10:00-11:00，正常9月1日08:00-09:00",
            "tool_call": {"name": "diagnose_by_statistical_difference", "arguments": {"anomaly_start": "2025-09-01 10:00:00", "anomaly_end": "2025-09-01 11:00:00", "normal_start": "2025-09-01 08:00:00", "normal_end": "2025-09-01 09:00:00"}},
            "tool_response": {"method": "statistical_difference", "top_features": [{"feature": "feature5", "z_score": 3.1}, {"feature": "feature6", "z_score": 2.9}]},
            "assistant": "诊断结果显示feature5（灯丝电源电压）和feature6（灯丝电源电流）在同日不同时段间偏移最显著。"
        },
    ],
    "diagnose_by_pls": [
        {
            "question": "用PLS方法诊断8月31日10点到11点的异常特征",
            "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": "2025-08-31 10:00:00", "anomaly_end": "2025-08-31 11:00:00", "top_k": 10}},
            "tool_response": {"method": "pls", "top_features": [{"feature": "feature4", "pls_weight": 0.35}, {"feature": "feature3", "pls_weight": 0.28}]},
            "assistant": "PLS诊断显示与束流异常最相关的变量为feature4（权重0.35）和feature3（权重0.28），均为加速电源相关。"
        },
        {
            "question": "偏最小二乘模型分析8月31日14:00-15:00的异常，返回前5个关键变量",
            "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": "2025-08-31 14:00:00", "anomaly_end": "2025-08-31 15:00:00", "top_k": 5}},
            "tool_response": {"method": "pls", "top_features": [{"feature": "feature6", "pls_weight": 0.42}, {"feature": "feature5", "pls_weight": 0.31}]},
            "assistant": "PLS分析显示feature6（灯丝电源电流）和feature5（灯丝电源电压）权重最高，与束流变化高度相关。"
        },
        {
            "question": "PLS权重分析8月30日15点到16点的异常",
            "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": "2025-08-30 15:00:00", "anomaly_end": "2025-08-30 16:00:00"}},
            "tool_response": {"method": "pls", "top_features": [{"feature": "feature8", "pls_weight": 0.38}, {"feature": "feature7", "pls_weight": 0.29}]},
            "assistant": "PLS权重分析显示feature8（引出电源电流）和feature7（引出电源电压）对束流影响最大。"
        },
        {
            "question": "基于PLS模型识别8月31日19:00-20:00与束流异常高度相关的变量",
            "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": "2025-08-31 19:00:00", "anomaly_end": "2025-08-31 20:00:00", "top_k": 10}},
            "tool_response": {"method": "pls", "top_features": [{"feature": "feature3", "pls_weight": 0.41}, {"feature": "feature4", "pls_weight": 0.33}]},
            "assistant": "PLS模型显示feature3、feature4（加速电源电压/电流）与束流异常高度相关，建议优先排查。"
        },
        {
            "question": "用已训练的PLS做异常诊断，时段9月1日08:00-09:00",
            "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": "2025-09-01 08:00:00", "anomaly_end": "2025-09-01 09:00:00"}},
            "tool_response": {"method": "pls", "top_features": [{"feature": "feature10", "pls_weight": 0.36}, {"feature": "feature11", "pls_weight": 0.30}]},
            "assistant": "PLS诊断显示C2电源相关变量（feature10、feature11）权重最高，可能与异常有关。"
        },
        {
            "question": "PLS线性投影权重分析8月31日12点到13点",
            "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": "2025-08-31 12:00:00", "anomaly_end": "2025-08-31 13:00:00", "top_k": 8}},
            "tool_response": {"method": "pls", "top_features": [{"feature": "feature14", "pls_weight": 0.34}, {"feature": "feature15", "pls_weight": 0.28}]},
            "assistant": "PLS线性投影权重显示对中X偏移电源（feature14、feature15）对目标束流贡献最大。"
        },
        {
            "question": "PLS诊断8月31日22:00-23:00异常，top_k=5",
            "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": "2025-08-31 22:00:00", "anomaly_end": "2025-08-31 23:00:00", "top_k": 5}},
            "tool_response": {"method": "pls", "top_features": [{"feature": "feature33", "pls_weight": 0.39}, {"feature": "feature34", "pls_weight": 0.32}]},
            "assistant": "PLS诊断显示冷水机压力（feature33）和温度（feature34）权重较高，冷却系统可能影响束流。"
        },
        {
            "question": "偏最小二乘诊断9月1日06:00-07:00的异常特征",
            "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": "2025-09-01 06:00:00", "anomaly_end": "2025-09-01 07:00:00"}},
            "tool_response": {"method": "pls", "top_features": [{"feature": "feature1", "pls_weight": 0.37}, {"feature": "feature2", "pls_weight": 0.30}]},
            "assistant": "PLS诊断显示抑制电源电压（feature1）和电流（feature2）权重最大，建议检查抑制电源系统。"
        },
        {
            "question": "分析各变量对目标束流的PLS权重，异常时段8月31日16:00-17:00",
            "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": "2025-08-31 16:00:00", "anomaly_end": "2025-08-31 17:00:00"}},
            "tool_response": {"method": "pls", "top_features": [{"feature": "feature22", "pls_weight": 0.33}, {"feature": "feature23", "pls_weight": 0.27}]},
            "assistant": "PLS分析显示斜向消像散电流（feature22、feature23）对束流影响较大。"
        },
        {
            "question": "PLS模型诊断8月30日20:00-21:00",
            "tool_call": {"name": "diagnose_by_pls", "arguments": {"anomaly_start": "2025-08-30 20:00:00", "anomaly_end": "2025-08-30 21:00:00", "top_k": 10}},
            "tool_response": {"method": "pls", "top_features": [{"feature": "feature5", "pls_weight": 0.40}, {"feature": "feature6", "pls_weight": 0.35}]},
            "assistant": "PLS模型诊断完成，灯丝电源（feature5、feature6）权重最高，与束流变化关系密切。"
        },
    ],
    "diagnose_by_shap": [
        {
            "question": "用SHAP方法诊断8月31日10点到11点的异常，用随机森林模型",
            "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": "2025-08-31 10:00:00", "anomaly_end": "2025-08-31 11:00:00", "model_name": "RF", "top_k": 10}},
            "tool_response": {"method": "shap", "model": "RF", "top_features": [{"feature": "feature4", "mean_abs_shap": 0.25}, {"feature": "feature3", "mean_abs_shap": 0.20}]},
            "assistant": "SHAP诊断（RF模型）显示feature4和feature3对预测贡献最大，mean_abs_shap分别为0.25和0.20，是导致束流偏离的关键变量。"
        },
        {
            "question": "XGBoost模型的SHAP解释，分析8月31日14:00-15:00异常",
            "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": "2025-08-31 14:00:00", "anomaly_end": "2025-08-31 15:00:00", "model_name": "XGB", "top_k": 10}},
            "tool_response": {"method": "shap", "model": "XGB", "top_features": [{"feature": "feature6", "mean_abs_shap": 0.28}, {"feature": "feature5", "mean_abs_shap": 0.22}]},
            "assistant": "XGBoost的SHAP分析显示feature6、feature5（灯丝电源）对预测贡献最大，可能是异常主要原因。"
        },
        {
            "question": "SHAP分析异常时段各变量对模型预测的贡献，时段8月30日15:00-16:00",
            "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": "2025-08-30 15:00:00", "anomaly_end": "2025-08-30 16:00:00"}},
            "tool_response": {"method": "shap", "model": "RF", "top_features": [{"feature": "feature8", "mean_abs_shap": 0.23}, {"feature": "feature7", "mean_abs_shap": 0.19}]},
            "assistant": "SHAP分析显示feature8、feature7（引出电源）对模型预测贡献最大，从模型角度识别为关键变量。"
        },
        {
            "question": "用LightGBM做SHAP解释，诊断8月31日19:00-20:00",
            "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": "2025-08-31 19:00:00", "anomaly_end": "2025-08-31 20:00:00", "model_name": "LGBM"}},
            "tool_response": {"method": "shap", "model": "LGBM", "top_features": [{"feature": "feature3", "mean_abs_shap": 0.26}, {"feature": "feature4", "mean_abs_shap": 0.21}]},
            "assistant": "LightGBM的SHAP解释显示feature3、feature4（加速电源）贡献度最高，是导致束流偏离的关键变量。"
        },
        {
            "question": "SHAP诊断9月1日08:00-09:00，返回前5个重要特征",
            "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": "2025-09-01 08:00:00", "anomaly_end": "2025-09-01 09:00:00", "top_k": 5}},
            "tool_response": {"method": "shap", "model": "RF", "top_features": [{"feature": "feature10", "mean_abs_shap": 0.24}, {"feature": "feature11", "mean_abs_shap": 0.20}]},
            "assistant": "SHAP诊断前5个重要特征为feature10、feature11（C2电源）等，建议重点排查。"
        },
        {
            "question": "分析异常时段内各变量对预测结果的贡献程度，用RF模型",
            "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": "2025-08-31 12:00:00", "anomaly_end": "2025-08-31 13:00:00", "model_name": "RF"}},
            "tool_response": {"method": "shap", "model": "RF", "top_features": [{"feature": "feature14", "mean_abs_shap": 0.27}, {"feature": "feature15", "mean_abs_shap": 0.23}]},
            "assistant": "RF的SHAP分析显示对中X偏移电源（feature14、feature15）对预测贡献最大。"
        },
        {
            "question": "用神经网络MLP做SHAP解释，诊断8月31日22:00-23:00",
            "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": "2025-08-31 22:00:00", "anomaly_end": "2025-08-31 23:00:00", "model_name": "MLP"}},
            "tool_response": {"method": "shap", "model": "MLP", "top_features": [{"feature": "feature33", "mean_abs_shap": 0.29}, {"feature": "feature34", "mean_abs_shap": 0.24}]},
            "assistant": "MLP的SHAP解释显示冷水机压力（feature33）和温度（feature34）贡献度最高。"
        },
        {
            "question": "SHAP重要性分析8月31日16:00-17:00，top_k=8",
            "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": "2025-08-31 16:00:00", "anomaly_end": "2025-08-31 17:00:00", "top_k": 8}},
            "tool_response": {"method": "shap", "model": "RF", "top_features": [{"feature": "feature22", "mean_abs_shap": 0.22}, {"feature": "feature23", "mean_abs_shap": 0.18}]},
            "assistant": "SHAP重要性分析显示斜向消像散电流（feature22、feature23）对预测贡献较大。"
        },
        {
            "question": "线性回归模型的SHAP解释，诊断8月30日20:00-21:00",
            "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": "2025-08-30 20:00:00", "anomaly_end": "2025-08-30 21:00:00", "model_name": "Linear"}},
            "tool_response": {"method": "shap", "model": "Linear", "top_features": [{"feature": "feature5", "mean_abs_shap": 0.30}, {"feature": "feature6", "mean_abs_shap": 0.25}]},
            "assistant": "线性回归的SHAP解释显示feature5、feature6（灯丝电源）对预测贡献最大。"
        },
        {
            "question": "从模型角度识别导致束流偏离的关键变量，时段9月1日06:00-07:00",
            "tool_call": {"name": "diagnose_by_shap", "arguments": {"anomaly_start": "2025-09-01 06:00:00", "anomaly_end": "2025-09-01 07:00:00"}},
            "tool_response": {"method": "shap", "model": "RF", "top_features": [{"feature": "feature1", "mean_abs_shap": 0.28}, {"feature": "feature2", "mean_abs_shap": 0.22}]},
            "assistant": "从模型角度，feature1、feature2（抑制电源）是导致束流偏离的关键变量，SHAP贡献度最高。"
        },
    ],
    "diagnose_by_autoencoder": [
        {
            "question": "用自编码器诊断8月31日10点到11点的异常特征",
            "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": "2025-08-31 10:00:00", "anomaly_end": "2025-08-31 11:00:00", "top_k": 10}},
            "tool_response": {"method": "autoencoder", "top_features": [{"feature": "feature4", "mean_reconstruction_error": 0.15}, {"feature": "feature3", "mean_reconstruction_error": 0.12}]},
            "assistant": "自编码器诊断显示feature4和feature3重构误差最大，相对正常工况分布偏离最显著，可能是异常关键变量。"
        },
        {
            "question": "AutoEncoder分析8月31日14:00-15:00各变量的重构误差",
            "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": "2025-08-31 14:00:00", "anomaly_end": "2025-08-31 15:00:00"}},
            "tool_response": {"method": "autoencoder", "top_features": [{"feature": "feature6", "mean_reconstruction_error": 0.18}, {"feature": "feature5", "mean_reconstruction_error": 0.14}]},
            "assistant": "自编码器分析显示feature6、feature5（灯丝电源）重构误差最大，在异常时段相对正常分布发生显著偏离。"
        },
        {
            "question": "无故障标注场景下，用AE诊断8月30日15:00-16:00",
            "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": "2025-08-30 15:00:00", "anomaly_end": "2025-08-30 16:00:00"}},
            "tool_response": {"method": "autoencoder", "top_features": [{"feature": "feature8", "mean_reconstruction_error": 0.16}, {"feature": "feature7", "mean_reconstruction_error": 0.13}]},
            "assistant": "自编码器适用于无故障标注场景，诊断显示feature8、feature7（引出电源）重构误差最大。"
        },
        {
            "question": "分析异常时段各变量重构误差，识别显著偏离的变量，时段8月31日19:00-20:00",
            "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": "2025-08-31 19:00:00", "anomaly_end": "2025-08-31 20:00:00", "top_k": 10}},
            "tool_response": {"method": "autoencoder", "top_features": [{"feature": "feature3", "mean_reconstruction_error": 0.19}, {"feature": "feature4", "mean_reconstruction_error": 0.15}]},
            "assistant": "重构误差分析显示feature3、feature4（加速电源）相对正常工况偏离最显著。"
        },
        {
            "question": "AE变量级重构误差诊断9月1日08:00-09:00，top_k=5",
            "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": "2025-09-01 08:00:00", "anomaly_end": "2025-09-01 09:00:00", "top_k": 5}},
            "tool_response": {"method": "autoencoder", "top_features": [{"feature": "feature10", "mean_reconstruction_error": 0.17}, {"feature": "feature11", "mean_reconstruction_error": 0.14}]},
            "assistant": "AE变量级重构误差诊断显示C2电源（feature10、feature11）误差最大，建议重点检查。"
        },
        {
            "question": "自编码器诊断8月31日12:00-13:00，返回重构误差最大的特征",
            "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": "2025-08-31 12:00:00", "anomaly_end": "2025-08-31 13:00:00"}},
            "tool_response": {"method": "autoencoder", "top_features": [{"feature": "feature14", "mean_reconstruction_error": 0.20}, {"feature": "feature15", "mean_reconstruction_error": 0.16}]},
            "assistant": "重构误差最大的特征为feature14、feature15（对中X偏移电源），可能与对中系统异常有关。"
        },
        {
            "question": "基于已训练自编码器诊断8月31日22:00-23:00",
            "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": "2025-08-31 22:00:00", "anomaly_end": "2025-08-31 23:00:00"}},
            "tool_response": {"method": "autoencoder", "top_features": [{"feature": "feature33", "mean_reconstruction_error": 0.21}, {"feature": "feature34", "mean_reconstruction_error": 0.17}]},
            "assistant": "自编码器诊断显示冷水机压力（feature33）和温度（feature34）重构误差最大，冷却系统可能异常。"
        },
        {
            "question": "识别相对正常工况分布发生显著偏离的关键变量，时段8月31日16:00-17:00",
            "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": "2025-08-31 16:00:00", "anomaly_end": "2025-08-31 17:00:00"}},
            "tool_response": {"method": "autoencoder", "top_features": [{"feature": "feature22", "mean_reconstruction_error": 0.14}, {"feature": "feature23", "mean_reconstruction_error": 0.11}]},
            "assistant": "相对正常分布偏离最显著的是feature22、feature23（斜向消像散电流）。"
        },
        {
            "question": "AutoEncoder诊断8月30日20:00-21:00，适用于无标注场景",
            "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": "2025-08-30 20:00:00", "anomaly_end": "2025-08-30 21:00:00"}},
            "tool_response": {"method": "autoencoder", "top_features": [{"feature": "feature5", "mean_reconstruction_error": 0.19}, {"feature": "feature6", "mean_reconstruction_error": 0.15}]},
            "assistant": "自编码器不依赖监督标签，诊断显示feature5、feature6（灯丝电源）重构误差最大。"
        },
        {
            "question": "AE分析9月1日06:00-07:00各变量重构误差",
            "tool_call": {"name": "diagnose_by_autoencoder", "arguments": {"anomaly_start": "2025-09-01 06:00:00", "anomaly_end": "2025-09-01 07:00:00", "top_k": 8}},
            "tool_response": {"method": "autoencoder", "top_features": [{"feature": "feature1", "mean_reconstruction_error": 0.16}, {"feature": "feature2", "mean_reconstruction_error": 0.13}]},
            "assistant": "AE分析显示feature1、feature2（抑制电源）重构误差较大，可能是异常原因。"
        },
    ],
    "plot_beam_data": [
        {
            "question": "绘制8月31日凌晨2点到3点的束流时序图",
            "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": "2025-08-31 02:00:00", "end_time": "2025-08-31 03:00:00"}},
            "tool_response": {"success": True, "plot_path": "output/beam_20250831_020000.png", "message": "已生成时序图，包含120条记录", "stats": {"count": 120, "mean": 0.85, "max": 0.92, "min": 0.78}},
            "assistant": "已生成8月31日02:00-03:00的束流时序图，包含120条记录。target均值0.85，最大0.92，最小0.78。图表已保存。"
        },
        {
            "question": "帮我画一下8月31日10点到11点的束流曲线，叠加feature1和feature3",
            "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": "2025-08-31 10:00:00", "end_time": "2025-08-31 11:00:00", "features": ["feature1", "feature3"]}},
            "tool_response": {"success": True, "plot_path": "output/beam_20250831_100000.png", "message": "已生成时序图", "stats": {"count": 60}},
            "assistant": "已绘制8月31日10:00-11:00的束流时序图，主图显示target，下方叠加了feature1和feature3曲线。"
        },
        {
            "question": "可视化8月30日下午3点到4点的束流数据",
            "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": "2025-08-30 15:00:00", "end_time": "2025-08-30 16:00:00"}},
            "tool_response": {"success": True, "plot_path": "output/beam_20250830_150000.png", "message": "已生成时序图，包含60条记录", "stats": {"count": 60, "mean": 0.86}},
            "assistant": "已生成8月30日15:00-16:00的束流时序图，共60条记录，target均值0.86。"
        },
        {
            "question": "画一张8月31日14:00-15:00的束流图，标题写「异常时段束流」",
            "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": "2025-08-31 14:00:00", "end_time": "2025-08-31 15:00:00", "title": "异常时段束流"}},
            "tool_response": {"success": True, "plot_path": "output/beam_20250831_140000.png", "message": "已生成时序图"},
            "assistant": "已生成标题为「异常时段束流」的时序图，涵盖8月31日14:00-15:00的束流数据。"
        },
        {
            "question": "查看8月31日19点到20点的束流趋势，需要图表",
            "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": "2025-08-31 19:00:00", "end_time": "2025-08-31 20:00:00"}},
            "tool_response": {"success": True, "plot_path": "output/beam_20250831_190000.png", "stats": {"count": 60, "mean": 0.71}},
            "assistant": "已生成8月31日19:00-20:00的束流时序图，可直观查看趋势。该时段target均值0.71。"
        },
        {
            "question": "绘制9月1日早上8点到9点的束流折线图",
            "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": "2025-09-01 08:00:00", "end_time": "2025-09-01 09:00:00"}},
            "tool_response": {"success": True, "plot_path": "output/beam_20250901_080000.png", "message": "已生成时序图"},
            "assistant": "已绘制9月1日08:00-09:00的束流折线图，主图显示target（束流强度）。"
        },
        {
            "question": "画束流时序图，时段8月31日12:00-13:00，叠加feature4、feature5、feature6",
            "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": "2025-08-31 12:00:00", "end_time": "2025-08-31 13:00:00", "features": ["feature4", "feature5", "feature6"]}},
            "tool_response": {"success": True, "plot_path": "output/beam_20250831_120000.png", "message": "已生成时序图"},
            "assistant": "已生成束流时序图，包含target主图及feature4、feature5、feature6三条特征曲线。"
        },
        {
            "question": "生成8月31日22点到23点的束流强度可视化",
            "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": "2025-08-31 22:00:00", "end_time": "2025-08-31 23:00:00"}},
            "tool_response": {"success": True, "plot_path": "output/beam_20250831_220000.png", "stats": {"count": 60}},
            "assistant": "已生成8月31日22:00-23:00的束流强度时序图，共60条记录。"
        },
        {
            "question": "我要看图表，8月30日20:00-21:00的束流数据",
            "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": "2025-08-30 20:00:00", "end_time": "2025-08-30 21:00:00"}},
            "tool_response": {"success": True, "plot_path": "output/beam_20250830_200000.png", "message": "已生成时序图，包含60条记录"},
            "assistant": "已生成8月30日20:00-21:00的束流时序图，共60条记录，主图显示target。"
        },
        {
            "question": "绘制8月31日16:00-17:00的束流时序图，主图显示target",
            "tool_call": {"name": "plot_beam_data", "arguments": {"start_time": "2025-08-31 16:00:00", "end_time": "2025-08-31 17:00:00"}},
            "tool_response": {"success": True, "plot_path": "output/beam_20250831_160000.png", "stats": {"count": 60, "mean": 0.84, "max": 0.90, "min": 0.79}},
            "assistant": "已绘制8月31日16:00-17:00的束流时序图，主图显示target，该时段均值0.84，最大0.90，最小0.79。"
        },
    ],
    "explain_diagnosis_features": [
        {
            "question": "解释一下诊断结果中的feature4、feature5、feature6的物理含义",
            "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature4", "feature5", "feature6"]}},
            "tool_response": {"success": True, "results": [{"feature_id": "feature4", "variable_name": "加速电源电流", "parent_system": "加速系统"}, {"feature_id": "feature5", "variable_name": "灯丝电源电压", "parent_system": "灯丝系统"}]},
            "assistant": "feature4对应加速电源电流，属于加速系统；feature5对应灯丝电源电压，属于灯丝系统；feature6对应灯丝电源电流。建议重点检查加速电源和灯丝电源相关设备。"
        },
        {
            "question": "诊断出的feature3、feature4是什么？属于哪个子系统？",
            "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature3", "feature4"]}},
            "tool_response": {"success": True, "results": [{"feature_id": "feature3", "variable_name": "加速电源电压", "parent_system": "加速系统"}, {"feature_id": "feature4", "variable_name": "加速电源电流", "parent_system": "加速系统"}]},
            "assistant": "feature3为加速电源电压，feature4为加速电源电流，均属于加速系统。两者与束流异常高度相关，建议检查加速电源工作状态。"
        },
        {
            "question": "从知识图谱查询feature1、feature2的详细参数",
            "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature1", "feature2"]}},
            "tool_response": {"success": True, "results": [{"feature_id": "feature1", "variable_name": "抑制电源电压", "details": {"range": "0-100V"}}, {"feature_id": "feature2", "variable_name": "抑制电源电流", "details": {}}]},
            "assistant": "feature1为抑制电源电压，feature2为抑制电源电流。抑制电源电压典型范围0-100V。建议结合诊断结果排查抑制电源系统。"
        },
        {
            "question": "解释异常诊断top_features中的feature6、feature7、feature8",
            "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature6", "feature7", "feature8"]}},
            "tool_response": {"success": True, "results": [{"feature_id": "feature6", "variable_name": "灯丝电源电流"}, {"feature_id": "feature7", "variable_name": "引出电源电压"}, {"feature_id": "feature8", "variable_name": "引出电源电流"}]},
            "assistant": "feature6为灯丝电源电流，feature7为引出电源电压，feature8为引出电源电流。三者分别涉及灯丝系统和引出系统，建议逐一排查。"
        },
        {
            "question": "diagnose_by_*返回的top_features有feature10、feature11，解释一下",
            "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature10", "feature11"]}},
            "tool_response": {"success": True, "results": [{"feature_id": "feature10", "variable_name": "C2电源电压"}, {"feature_id": "feature11", "variable_name": "C2电源电流"}]},
            "assistant": "feature10为C2电源电压，feature11为C2电源电流。C2电源异常可能影响束流稳定性，建议检查C2电源模块。"
        },
        {
            "question": "查询feature14、feature15的技术背景和所属子系统",
            "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature14", "feature15"]}},
            "tool_response": {"success": True, "results": [{"feature_id": "feature14", "variable_name": "对中X偏移电源电压", "parent_system": "对中系统"}, {"feature_id": "feature15", "variable_name": "对中X偏移电源电流", "parent_system": "对中系统"}]},
            "assistant": "feature14、feature15分别为对中X偏移电源的电压和电流，属于对中系统。对中系统异常会影响束流对中精度。"
        },
        {
            "question": "解释feature33、feature34的物理含义",
            "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature33", "feature34"]}},
            "tool_response": {"success": True, "results": [{"feature_id": "feature33", "variable_name": "冷水机压力"}, {"feature_id": "feature34", "variable_name": "冷水机内部温度"}]},
            "assistant": "feature33为冷水机压力，feature34为冷水机内部温度。冷却系统异常可能导致设备过热，影响束流稳定性。"
        },
        {
            "question": "诊断结果中feature22、feature23是什么变量？",
            "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature22", "feature23"]}},
            "tool_response": {"success": True, "results": [{"feature_id": "feature22", "variable_name": "斜向消像散1电流"}, {"feature_id": "feature23", "variable_name": "斜向消像散2电流"}]},
            "assistant": "feature22、feature23分别为斜向消像散1电流和斜向消像散2电流，属于像散校正系统，异常可能影响束流质量。"
        },
        {
            "question": "深入理解feature5、feature6的技术细节",
            "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature5", "feature6"], "top_k": 3}},
            "tool_response": {"success": True, "results": [{"feature_id": "feature5", "variable_name": "灯丝电源电压"}, {"feature_id": "feature6", "variable_name": "灯丝电源电流"}]},
            "assistant": "feature5为灯丝电源电压，feature6为灯丝电源电流。灯丝电源为束流产生提供加热，其异常会直接影响束流强度。"
        },
        {
            "question": "从generation知识图谱解释feature1到feature5",
            "tool_call": {"name": "explain_diagnosis_features", "arguments": {"feature_names": ["feature1", "feature2", "feature3", "feature4", "feature5"]}},
            "tool_response": {"success": True, "results": [{"feature_id": "feature1", "variable_name": "抑制电源电压"}, {"feature_id": "feature2", "variable_name": "抑制电源电流"}, {"feature_id": "feature3", "variable_name": "加速电源电压"}, {"feature_id": "feature4", "variable_name": "加速电源电流"}, {"feature_id": "feature5", "variable_name": "灯丝电源电压"}]},
            "assistant": "feature1-5分别对应：抑制电源电压/电流、加速电源电压/电流、灯丝电源电压。这些变量与束流产生和加速过程密切相关，异常时需优先排查。"
        },
    ],
    "explain_variable_meaning": [
        {
            "question": "灯丝电源电流是什么？",
            "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "灯丝电源电流"}},
            "tool_response": {"success": True, "results": [{"variable_name": "灯丝电源电流", "feature_id": "feature6", "parent_system": "灯丝系统", "details": {}}]},
            "assistant": "灯丝电源电流对应feature6，属于灯丝系统。灯丝电源为束流产生提供加热电流，其大小影响束流强度。"
        },
        {
            "question": "feature6是什么意思？",
            "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "feature6"}},
            "tool_response": {"success": True, "results": [{"variable_name": "灯丝电源电流", "feature_id": "feature6", "type": "传感器"}]},
            "assistant": "feature6对应灯丝电源电流，是灯丝系统的关键监测变量，用于反映灯丝加热状态。"
        },
        {
            "question": "加速电源电压是什么？有什么作用？",
            "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "加速电源电压"}},
            "tool_response": {"success": True, "results": [{"variable_name": "加速电源电压", "feature_id": "feature3", "parent_system": "加速系统"}]},
            "assistant": "加速电源电压对应feature3，属于加速系统。用于为束流提供加速电场，其稳定性直接影响束流能量和强度。"
        },
        {
            "question": "查询feature3的含义和用法",
            "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "feature3"}},
            "tool_response": {"success": True, "results": [{"variable_name": "加速电源电压", "feature_id": "feature3"}]},
            "assistant": "feature3对应加速电源电压，是加速系统的核心参数，用于控制束流加速过程。"
        },
        {
            "question": "灯丝电源是什么？",
            "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "灯丝电源是什么"}},
            "tool_response": {"success": True, "results": [{"variable_name": "灯丝电源电压", "feature_id": "feature5"}, {"variable_name": "灯丝电源电流", "feature_id": "feature6"}]},
            "assistant": "灯丝电源包括电压（feature5）和电流（feature6），为束流产生提供加热，是离子源的关键组成部分。"
        },
        {
            "question": "冷水机压力这个变量代表什么？",
            "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "冷水机压力"}},
            "tool_response": {"success": True, "results": [{"variable_name": "冷水机压力", "feature_id": "feature33"}]},
            "assistant": "冷水机压力对应feature33，反映冷却系统循环压力，异常可能导致设备过热，影响束流稳定性。"
        },
        {
            "question": "对中X偏移电源电压是什么意思？",
            "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "对中X偏移电源电压"}},
            "tool_response": {"success": True, "results": [{"variable_name": "对中X偏移电源电压", "feature_id": "feature14", "parent_system": "对中系统"}]},
            "assistant": "对中X偏移电源电压对应feature14，属于对中系统，用于调节束流在X方向的偏移，保证束流对中精度。"
        },
        {
            "question": "feature33和feature34分别是什么？",
            "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "feature33"}},
            "tool_response": {"success": True, "results": [{"variable_name": "冷水机压力", "feature_id": "feature33"}, {"variable_name": "冷水机内部温度", "feature_id": "feature34"}]},
            "assistant": "feature33为冷水机压力，feature34为冷水机内部温度，均属于冷却系统，用于监测设备热管理状态。"
        },
        {
            "question": "引出电源电流的技术细节",
            "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "引出电源电流"}},
            "tool_response": {"success": True, "results": [{"variable_name": "引出电源电流", "feature_id": "feature8", "parent_system": "引出系统"}]},
            "assistant": "引出电源电流对应feature8，属于引出系统，用于控制束流从离子源引出的过程。"
        },
        {
            "question": "C2电源电压是什么？",
            "tool_call": {"name": "explain_variable_meaning", "arguments": {"query": "C2电源电压"}},
            "tool_response": {"success": True, "results": [{"variable_name": "C2电源电压", "feature_id": "feature10"}]},
            "assistant": "C2电源电压对应feature10，是加速器电源系统的一部分，用于提供特定阶段的加速电压。"
        },
    ],
    "search_domain_knowledge": [
        {
            "question": "束流强度如何测量？",
            "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "束流强度如何测量"}},
            "tool_response": {"success": True, "results": [{"content": "束流强度通常通过法拉第杯、束流变压器等探测器测量...", "score": 0.92}]},
            "assistant": "束流强度通常通过法拉第杯、束流变压器等探测器测量。法拉第杯直接收集束流电荷，束流变压器通过感应测量束流。具体方法取决于束流能量和精度要求。"
        },
        {
            "question": "加速器的工作原理是什么？",
            "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "加速器的工作原理"}},
            "tool_response": {"success": True, "results": [{"content": "加速器通过电场或磁场对带电粒子进行加速...", "score": 0.88}]},
            "assistant": "加速器通过电场或磁场对带电粒子进行加速，使其获得高能量。离子注入机等设备利用加速后的离子束进行材料改性。"
        },
        {
            "question": "离子注入工艺流程是怎样的？",
            "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "离子注入工艺流程"}},
            "tool_response": {"success": True, "results": [{"content": "离子注入工艺包括离子源产生、加速、质量分析、扫描注入等步骤...", "score": 0.90}]},
            "assistant": "离子注入工艺包括离子源产生、加速、质量分析、扫描注入等步骤。束流稳定性直接影响注入均匀性和工艺重复性。"
        },
        {
            "question": "加速器真空系统的作用",
            "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "加速器真空系统的作用"}},
            "tool_response": {"success": True, "results": [{"content": "真空系统为束流传输提供无碰撞路径，避免气体散射...", "score": 0.85}]},
            "assistant": "真空系统为束流传输提供无碰撞路径，避免气体散射导致的束流损失和能量分散，是加速器稳定运行的关键。"
        },
        {
            "question": "束流异常可能有哪些原因？",
            "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "束流异常可能的原因"}},
            "tool_response": {"success": True, "results": [{"content": "束流异常可能由电源波动、真空泄漏、对中偏移、冷却故障等引起...", "score": 0.87}]},
            "assistant": "束流异常可能由电源波动、真空泄漏、对中偏移、冷却故障等引起。建议结合诊断工具定位具体变量后逐一排查。"
        },
        {
            "question": "微电子设备中离子注入的应用",
            "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "微电子设备离子注入应用"}},
            "tool_response": {"success": True, "results": [{"content": "离子注入用于半导体掺杂，可精确控制掺杂浓度和深度...", "score": 0.89}]},
            "assistant": "离子注入用于半导体掺杂，可精确控制掺杂浓度和深度，是集成电路制造的关键工艺之一。"
        },
        {
            "question": "灯丝电源故障对束流有什么影响？",
            "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "灯丝电源故障对束流的影响"}},
            "tool_response": {"success": True, "results": [{"content": "灯丝电源异常会导致离子源发射不稳定，束流强度波动或下降...", "score": 0.86}]},
            "assistant": "灯丝电源异常会导致离子源发射不稳定，束流强度波动或下降，严重时可能无法产生束流。"
        },
        {
            "question": "束流对中系统的技术细节",
            "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "束流对中系统"}},
            "tool_response": {"success": True, "results": [{"content": "对中系统通过偏转线圈、对中电源等调节束流位置...", "score": 0.84}]},
            "assistant": "对中系统通过偏转线圈、对中电源等调节束流位置，保证束流准确注入靶材。对中X/Y偏移电源异常会影响注入均匀性。"
        },
        {
            "question": "冷却系统在加速器中的作用",
            "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "加速器冷却系统作用"}},
            "tool_response": {"success": True, "results": [{"content": "冷却系统用于带走加速器运行产生的热量，维持设备温度稳定...", "score": 0.88}]},
            "assistant": "冷却系统用于带走加速器运行产生的热量，维持设备温度稳定。冷水机压力、温度异常可能导致过热，影响束流稳定性。"
        },
        {
            "question": "检索束流测量相关的专业知识",
            "tool_call": {"name": "search_domain_knowledge", "arguments": {"query": "束流测量方法", "top_k": 5}},
            "tool_response": {"success": True, "results": [{"content": "束流测量方法包括积分测量和实时测量...", "score": 0.91}]},
            "assistant": "束流测量方法包括积分测量（法拉第杯）和实时测量（束流变压器）等，可根据精度和响应速度需求选择。"
        },
    ],
}


def format_tool_response(resp) -> str:
    """将 tool_response 转为字符串，与 train.jsonl 格式一致"""
    return str(resp)


def format_tool_call(tc: dict) -> str:
    """格式化 tool_call 的 content"""
    return json.dumps({"name": tc["name"], "arguments": tc.get("arguments", {}) or {}}, ensure_ascii=False)


def sample_to_messages(s: dict) -> list:
    """将单条样本转为 messages 列表。支持 single_tool、tool_chain、no_tool。"""
    messages = [{"role": "user", "content": s["question"]}]
    tool_call = s.get("tool_call")
    tool_response = s.get("tool_response")

    if tool_call is None or tool_response is None:
        # 无工具：仅 user -> assistant
        messages.append({"role": "assistant", "content": s["assistant"]})
        return messages

    if isinstance(tool_call, list):
        # 工具链：user -> tc1 -> tr1 -> tc2 -> tr2 -> ... -> assistant
        for tc, tr in zip(tool_call, tool_response):
            messages.append({"role": "tool_call", "content": format_tool_call(tc)})
            messages.append({"role": "tool_response", "content": format_tool_response(tr)})
    else:
        # 单工具
        messages.append({"role": "tool_call", "content": format_tool_call(tool_call)})
        messages.append({"role": "tool_response", "content": format_tool_response(tool_response)})
    messages.append({"role": "assistant", "content": s["assistant"]})
    return messages


def load_train_samples_from_file(path: str) -> list:
    """从 train_samples.jsonl 加载样本。"""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def main():
    import argparse
    parser = argparse.ArgumentParser(description="生成束流工具训练数据")
    parser.add_argument("-i", "--input", default=None, help="从 train_samples.jsonl 读取（标准化流程输出）")
    parser.add_argument("-o", "--output", default="train_beam_tools.jsonl", help="输出文件路径，默认 train_beam_tools.jsonl")
    args = parser.parse_args()
    project_root = os.path.dirname(os.path.dirname(__file__))
    output_path = args.output
    if not os.path.isabs(output_path):
        output_path = os.path.join(project_root, output_path)
    tools_str = json.dumps(TOOLS, ensure_ascii=False)

    if args.input:
        # 从标准化流程输出读取
        input_path = args.input if os.path.isabs(args.input) else os.path.join(project_root, args.input)
        if not os.path.exists(input_path):
            print(f"输入文件不存在: {input_path}")
            sys.exit(1)
        samples = load_train_samples_from_file(input_path)
        records = []
        for s in samples:
            messages = sample_to_messages(s)
            records.append({"tools": tools_str, "messages": messages})
        print(f"从 {input_path} 加载 {len(records)} 条样本")
    else:
        # 使用内置 TRAIN_SAMPLES（向后兼容）
        records = []
        for tool_name, samples in TRAIN_SAMPLES.items():
            for s in samples:
                messages = sample_to_messages(s)
                records.append({"tools": tools_str, "messages": messages})
        print("使用内置 TRAIN_SAMPLES")

    with open(output_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"已生成 {len(records)} 条训练数据，保存至 {output_path}")


if __name__ == "__main__":
    main()
