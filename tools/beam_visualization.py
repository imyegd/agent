"""
束流波动分析结果可视化工具
用自然语言整理分析结果，并生成可视化图表
"""

import os
import numpy as np
import pandas as pd

# 在导入 pyplot 之前设置后端，避免 tkinter 多线程问题
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 导入 PLS 分析工具
try:
    from .pls_analysis import PLSAnalysisTool
    from .data_query import DataQueryTool
except ImportError:
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from tools.pls_analysis import PLSAnalysisTool
    from tools.data_query import DataQueryTool


class BeamVisualizationTool:
    """束流波动分析可视化工具类"""
    
    def __init__(self, model_path: Optional[str] = None, data_path: Optional[str] = None):
        """
        初始化可视化工具
        
        Args:
            model_path: PLS 模型文件路径
            data_path: CSV数据文件路径
        """
        self.pls_tool = PLSAnalysisTool(model_path=model_path, data_path=data_path)
        self.data_path = self.pls_tool.data_path
    
    def format_analysis_result(self, analysis_result: Dict[str, Any]) -> str:
        """
        将分析结果格式化为自然语言描述
        
        Args:
            analysis_result: analyze_beam_fluctuation 函数的返回结果
        
        Returns:
            格式化后的自然语言描述文本
        """
        if not analysis_result.get('success', False):
            return f"❌ 分析失败：{analysis_result.get('message', '未知错误')}"
        
        lines = []
        lines.append("=" * 70)
        lines.append("📊 束流波动分析报告")
        lines.append("=" * 70)
        
        # 1. 基本信息
        lines.append("\n【分析时间范围】")
        lines.append(f"  起始时间：{analysis_result['start_time']}")
        lines.append(f"  结束时间：{analysis_result['end_time']}")
        lines.append(f"  数据条数：{analysis_result['data_count']} 条")
        
        # 2. 统计信息
        lines.append("\n【统计指标】")
        stats = analysis_result['statistics']
        thresholds = analysis_result['thresholds']
        
        lines.append(f"  T²统计量：")
        lines.append(f"    - 均值：{stats['T2X_mean']:.4f}")
        lines.append(f"    - 最大值：{stats['T2X_max']:.4f}")
        lines.append(f"    - 最小值：{stats['T2X_min']:.4f}")
        lines.append(f"    - 标准差：{stats['T2X_std']:.4f}")
        lines.append(f"    - 控制上限 (UCL)：{thresholds['UCL_T2X']:.4f}")
        
        lines.append(f"\n  SPE统计量：")
        lines.append(f"    - 均值：{stats['SPEX_mean']:.4f}")
        lines.append(f"    - 最大值：{stats['SPEX_max']:.4f}")
        lines.append(f"    - 最小值：{stats['SPEX_min']:.4f}")
        lines.append(f"    - 标准差：{stats['SPEX_std']:.4f}")
        lines.append(f"    - 控制上限 (UCL)：{thresholds['UCL_SPEX']:.4f}")
        
        # 3. 异常检测结果
        lines.append("\n【异常检测结果】")
        anomaly = analysis_result['anomaly_detection']
        summary = analysis_result['summary']
        
        status_emoji = "✅" if not summary['has_anomaly'] else "⚠️"
        lines.append(f"  状态：{status_emoji} {summary['status']}")
        lines.append(f"  总样本数：{anomaly['total_samples']} 个")
        lines.append(f"  异常点数：{anomaly['anomaly_count']} 个")
        lines.append(f"  异常率：{anomaly['anomaly_rate']:.2%}")
        lines.append(f"  T²异常数：{anomaly['T2X_anomaly_count']} 个")
        lines.append(f"  SPE异常数：{anomaly['SPEX_anomaly_count']} 个")
        
        # 4. 结论性描述
        lines.append("\n【分析结论】")
        if not summary['has_anomaly']:
            lines.append("  ✓ 该时间段内束流运行状况良好，所有数据点均在正常范围内。")
            lines.append("  ✓ T²统计量和SPE统计量均未超出控制上限。")
            lines.append("  ✓ 未检测到显著的异常波动。")
        else:
            lines.append(f"  ⚠ 该时间段内检测到 {anomaly['anomaly_count']} 个异常点。")
            lines.append(f"  ⚠ 异常率为 {anomaly['anomaly_rate']:.2%}，需要关注。")
            
            # 详细分析第一个异常点
            first_anomaly = anomaly.get('first_anomaly')
            if first_anomaly:
                lines.append("\n【首个异常点详情】")
                lines.append(f"  时间：{first_anomaly['time']}")
                lines.append(f"  位置：第 {first_anomaly['index'] + 1} 个数据点")
                lines.append(f"  T²值：{first_anomaly['T2X_value']:.4f} (阈值: {thresholds['UCL_T2X']:.4f})")
                lines.append(f"  SPE值：{first_anomaly['SPEX_value']:.4f} (阈值: {thresholds['UCL_SPEX']:.4f})")
                
                # T² 贡献度分析
                if first_anomaly.get('T2X_anomaly') and 'T2X_top_features' in first_anomaly:
                    lines.append("\n  T²异常主要贡献特征：")
                    for i, (feature, contrib) in enumerate(first_anomaly['T2X_top_features'].items(), 1):
                        lines.append(f"    {i}. {feature}: {contrib:.6f}")
                
                # SPE 贡献度分析
                if first_anomaly.get('SPEX_anomaly') and 'SPEX_top_features' in first_anomaly:
                    lines.append("\n  SPE异常主要贡献特征：")
                    for i, (feature, contrib) in enumerate(first_anomaly['SPEX_top_features'].items(), 1):
                        lines.append(f"    {i}. {feature}: {contrib:.6f}")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
    
    def plot_analysis_result(
        self,
        start_time: str,
        end_time: str,
        save_path: Optional[str] = None,
        figsize: Tuple[int, int] = (14, 10)
    ) -> Optional[str]:
        """
        绘制分析结果的可视化图表
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            save_path: 图表保存路径，如果为 None 则显示图表
            figsize: 图表大小
        
        Returns:
            保存的文件路径，如果只是显示则返回 None
        """
        try:
            # 1. 获取数据和计算统计量
            query_tool = DataQueryTool(data_path=self.data_path)
            query_tool.df['时间'] = pd.to_datetime(query_tool.df['时间'])
            
            start_dt = pd.to_datetime(start_time)
            end_dt = pd.to_datetime(end_time)
            mask = (query_tool.df['时间'] >= start_dt) & (query_tool.df['时间'] <= end_dt)
            data_df = query_tool.df[mask].copy()
            
            if len(data_df) == 0:
                print(f"警告：在 {start_time} 到 {end_time} 范围内未找到数据")
                return None
            
            # 提取特征数据
            feature_cols = [col for col in data_df.columns if col.startswith('feature')]
            feature_cols.sort(key=lambda x: int(x.replace('feature', '')))
            X_data = data_df[feature_cols].values
            
            # 标准化
            X_scaled = self.pls_tool.scaler_X.transform(X_data)
            
            # 计算统计量
            T2X, SPEX, E_X = self.pls_tool._compute_pls_stats(X_scaled)
            
            # 检测异常
            anomalies_T2X = T2X > self.pls_tool.UCL_T2X
            anomalies_SPEX = SPEX > self.pls_tool.UCL_SPEX
            anomalies_combined = anomalies_T2X | anomalies_SPEX
            
            # 2. 创建图表
            fig, axes = plt.subplots(2, 1, figsize=figsize)
            fig.suptitle('束流波动 PLS 分析结果', fontsize=16, fontweight='bold')
            
            time_points = data_df['时间'].values
            
            # 绘制 T² 图
            ax1 = axes[0]
            ax1.plot(time_points, T2X, 'b-', linewidth=1, label='T² 统计量', alpha=0.7)
            ax1.axhline(y=self.pls_tool.UCL_T2X, color='r', linestyle='--', 
                       linewidth=2, label=f'UCL = {self.pls_tool.UCL_T2X:.2f}')
            
            # 标注 T² 异常点
            if np.any(anomalies_T2X):
                ax1.scatter(time_points[anomalies_T2X], T2X[anomalies_T2X], 
                           color='red', s=50, marker='o', label='异常点', zorder=5)
            
            ax1.set_ylabel('T² 统计量', fontsize=12)
            ax1.set_title('T² 统计量监控图', fontsize=14, pad=10)
            ax1.legend(loc='upper right')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # 绘制 SPE 图
            ax2 = axes[1]
            ax2.plot(time_points, SPEX, 'g-', linewidth=1, label='SPE 统计量', alpha=0.7)
            ax2.axhline(y=self.pls_tool.UCL_SPEX, color='r', linestyle='--', 
                       linewidth=2, label=f'UCL = {self.pls_tool.UCL_SPEX:.2f}')
            
            # 标注 SPE 异常点
            if np.any(anomalies_SPEX):
                ax2.scatter(time_points[anomalies_SPEX], SPEX[anomalies_SPEX], 
                           color='red', s=50, marker='o', label='异常点', zorder=5)
            
            ax2.set_xlabel('时间', fontsize=12)
            ax2.set_ylabel('SPE 统计量', fontsize=12)
            ax2.set_title('SPE 统计量监控图', fontsize=14, pad=10)
            ax2.legend(loc='upper right')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            # 添加统计信息文本框
            anomaly_count = np.sum(anomalies_combined)
            anomaly_rate = anomaly_count / len(T2X) if len(T2X) > 0 else 0
            info_text = f'样本数: {len(T2X)}\n异常数: {anomaly_count}\n异常率: {anomaly_rate:.2%}'
            
            fig.text(0.02, 0.98, info_text, 
                    transform=fig.transFigure,
                    fontsize=10,
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            plt.tight_layout(rect=[0, 0, 1, 0.96])
            
            # 3. 保存或显示
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"图表已保存至: {save_path}")
                plt.close(fig)
                return save_path
            else:
                plt.show()
                return None
                
        except Exception as e:
            print(f"绘图失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


# 定义可视化工具的工具描述（OpenAI Function Calling格式）
VISUALIZATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "visualize_beam_fluctuation",
            "description": """分析并可视化束流波动数据。该工具会执行 PLS 分析，
            生成易读的自然语言报告，并绘制包含 T² 和 SPE 统计量的可视化图表。
            适合需要全面了解束流状态和生成报告的场景。""",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_time": {
                        "type": "string",
                        "description": "开始时间，支持格式：'YYYY-MM-DD HH:MM:SS' 或 'YYYY-MM-DDTHH:MM:SS'。例如：'2025-08-30 17:23:26'"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "结束时间，支持格式：'YYYY-MM-DD HH:MM:SS' 或 'YYYY-MM-DDTHH:MM:SS'。例如：'2025-08-30 18:23:30'"
                    },
                    "save_path": {
                        "type": "string",
                        "description": "图表保存路径（可选），例如 'output/beam_analysis.png'。如果不提供，会自动生成文件名并保存到 output/ 目录"
                    },
                    "show_plot": {
                        "type": "boolean",
                        "description": "是否生成图表，默认为 True"
                    }
                },
                "required": ["start_time", "end_time"]
            }
        }
    }
]


# 定义供 LLM 调用的工具函数
def visualize_beam_fluctuation(
    start_time: str, 
    end_time: str,
    save_path: Optional[str] = None,
    show_plot: bool = True
) -> Dict[str, Any]:
    """
    分析并可视化束流波动数据
    
    该函数会执行以下操作：
    1. 调用 PLS 模型分析指定时间范围的束流数据
    2. 将分析结果转换为易读的自然语言描述
    3. 生成包含 T² 和 SPE 统计量的可视化图表
    
    Args:
        start_time: 开始时间，格式如 "2025-08-30 17:23:26"
        end_time: 结束时间，格式如 "2025-08-30 18:23:30"
        save_path: 图表保存路径（可选），例如 "output/beam_analysis.png"
                  如果不提供，图表将显示在屏幕上
        show_plot: 是否生成图表，默认为 True
    
    Returns:
        包含以下内容的字典：
        - success: 是否成功
        - text_report: 自然语言格式的分析报告
        - plot_path: 图表保存路径（如果保存了的话）
        - raw_result: 原始分析结果
    """
    try:
        # 1. 执行 PLS 分析
        tool = PLSAnalysisTool()
        analysis_result = tool.analyze_fluctuation(start_time, end_time)
        
        if not analysis_result.get('success', False):
            return {
                "success": False,
                "error": analysis_result.get('error', '未知错误'),
                "message": analysis_result.get('message', '分析失败'),
                "text_report": None,
                "plot_path": None,
                "raw_result": analysis_result
            }
        
        # 2. 生成自然语言报告
        viz_tool = BeamVisualizationTool()
        text_report = viz_tool.format_analysis_result(analysis_result)
        
        # 3. 生成可视化图表
        plot_path = None
        if show_plot:
            # 如果没有指定保存路径，自动生成一个
            if save_path is None:
                # 创建 output 目录
                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output')
                os.makedirs(output_dir, exist_ok=True)
                
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(output_dir, f'beam_analysis_{timestamp}.png')
            
            plot_path = viz_tool.plot_analysis_result(start_time, end_time, save_path=save_path)
        
        return {
            "success": True,
            "text_report": text_report,
            "plot_path": plot_path,
            "raw_result": analysis_result,
            "message": "分析和可视化完成"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"可视化分析失败: {str(e)}",
            "text_report": None,
            "plot_path": None,
            "raw_result": None
        }


# 可视化工具函数映射
VISUALIZATION_TOOL_FUNCTIONS = {
    "visualize_beam_fluctuation": visualize_beam_fluctuation
}

