"""测试 PLS 分析工具"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.pls_analysis import analyze_beam_fluctuation

if __name__ == "__main__":
    print("测试 PLS 分析工具...")
    print("=" * 60)
    
    # 测试时间范围
    start_time = "2025-08-30 17:23:26"
    end_time = "2025-08-31 21:23:59"
    
    print(f"\n分析时间范围: {start_time} 到 {end_time}")
    print("-" * 60)
    
    try:
        result = analyze_beam_fluctuation(start_time, end_time)
        
        if result.get('success'):
            print("\n✓ 分析成功！")
            print(f"\n数据条数: {result.get('data_count', 0)}")
            print(f"\n统计信息:")
            stats = result.get('statistics', {})
            print(f"  T2X - 均值: {stats.get('T2X_mean', 0):.4f}, 最大值: {stats.get('T2X_max', 0):.4f}")
            print(f"  SPEX - 均值: {stats.get('SPEX_mean', 0):.4f}, 最大值: {stats.get('SPEX_max', 0):.4f}")
            
            print(f"\n阈值:")
            thresholds = result.get('thresholds', {})
            print(f"  UCL_T2X: {thresholds.get('UCL_T2X', 0):.4f}")
            print(f"  UCL_SPEX: {thresholds.get('UCL_SPEX', 0):.4f}")
            
            anomaly = result.get('anomaly_detection', {})
            print(f"\n异常检测:")
            print(f"  总样本数: {anomaly.get('total_samples', 0)}")
            print(f"  异常数量: {anomaly.get('anomaly_count', 0)}")
            print(f"  异常率: {anomaly.get('anomaly_rate', 0):.2%}")
            
            summary = result.get('summary', {})
            print(f"\n状态: {summary.get('status', '未知')}")
            print(f"消息: {summary.get('message', '')}")
            
            if anomaly.get('first_anomaly'):
                print(f"\n第一个异常点:")
                first = anomaly['first_anomaly']
                print(f"  时间: {first.get('time', '')}")
                print(f"  T2X值: {first.get('T2X_value', 0):.4f}")
                print(f"  SPEX值: {first.get('SPEX_value', 0):.4f}")
        else:
            print(f"\n✗ 分析失败: {result.get('error', '未知错误')}")
            print(f"消息: {result.get('message', '')}")
            
    except Exception as e:
        print(f"\n✗ 发生异常: {e}")
        import traceback
        traceback.print_exc()

