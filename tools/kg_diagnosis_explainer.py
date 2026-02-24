"""
基于知识图谱的异常诊断解释工具
在异常诊断后，从知识图谱中查找相关信息，提供详细解释和解决方案
"""

import os
import sys
from typing import Dict, Any, List, Optional

# 添加父目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


# =========================
# Feature 到变量名的映射
# =========================
FEATURE_MAPPING = {
    "feature1": "抑制电源电压",
    "feature2": "抑制电源电流",
    "feature3": "加速电源电压",
    "feature4": "加速电源电流",
    "feature5": "灯丝电源电压",
    "feature6": "灯丝电源电流",
    "feature7": "引出电源电压",
    "feature8": "引出电源电流",
    "feature9": "C1电源电压",
    "feature10": "C2电源电压",
    "feature11": "C2电源电流",
    "feature12": "C3电源电压",
    "feature13": "C3电源电流",
    "feature14": "对中X偏移电源电压",
    "feature15": "对中X偏移电源电流",
    "feature16": "对中Y偏移电源电压",
    "feature17": "对中Y偏移电源电流",
    "feature18": "对中X倾斜电源电压",
    "feature19": "对中X倾斜电源电流",
    "feature20": "对中Y倾斜电源电压",
    "feature21": "对中Y倾斜电源电流",
    "feature22": "斜向消像散1电流",
    "feature23": "斜向消像散2电流",
    "feature24": "斜向消像散3电流",
    "feature25": "斜向消像散4电流",
    "feature26": "轴向消像散1电流",
    "feature27": "轴向消像散2电流",
    "feature28": "轴向消像散3电流",
    "feature29": "轴向消像散4电流",
    "feature30": "微调焦电流",
    "feature31": "工件台位置X",
    "feature32": "工件台位置Y",
    "feature33": "冷水机压力",
    "feature34": "冷水机内部温度",
}

# 子系统和功能的中文名称
SUBSYSTEM_NAMES = {
    "ElectronGunPowerSystem": "电子枪电源系统",
    "BeamAccelerationSystem": "束流加速系统",
    "BeamAlignmentSystem": "束流对中系统",
    "AstigmatismCorrectionSystem": "消像散校正系统",
    "BeamFocusingSystem": "束流聚焦系统",
    "AuxiliaryEnvironmentSystem": "辅助环境系统"
}

FUNCTION_NAMES = {
    "ElectronEmissionControl": "电子发射控制",
    "BeamEnergyRegulation": "束流能量调节",
    "BeamTrajectoryAlignment": "束流轨迹校准",
    "BeamShapeCorrection": "束流形状修正",
    "BeamFocusAdjustment": "束流聚焦调整",
    "ThermalMechanicalStability": "热力学与机械稳定性"
}


# =========================
# 知识图谱查询客户端
# =========================

class KGDiagnosisExplainer:
    """知识图谱诊断解释器"""
    
    def __init__(
        self,
        neo4j_uri: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "12345678"
    ):
        """
        初始化知识图谱连接
        
        Args:
            neo4j_uri: Neo4j 数据库 URI
            neo4j_user: 用户名
            neo4j_password: 密码
        """
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                neo4j_uri, 
                auth=(neo4j_user, neo4j_password)
            )
            self.kg_available = True
        except Exception as e:
            print(f"知识图谱连接失败: {e}")
            self.driver = None
            self.kg_available = False
    
    def get_variable_context(self, variable_name: str) -> Optional[Dict[str, Any]]:
        """
        从知识图谱查询变量的上下文信息
        
        Args:
            variable_name: 变量名称（中文）
            
        Returns:
            包含子系统、功能角色等信息的字典
        """
        if not self.kg_available or not self.driver:
            return None
        
        def query_context(tx, var_name):
            result = tx.run("""
            MATCH (v:Variable {name: $name})
            OPTIONAL MATCH (v)-[:BELONGS_TO]->(s)
            OPTIONAL MATCH (v)-[:HAS_FUNCTION]->(f)
            OPTIONAL MATCH (v)-[:MAY_AFFECT]->(m)
            RETURN v.name AS variable,
                   s.name AS subsystem,
                   f.name AS function,
                   m.name AS metric
            """, name=var_name)
            record = result.single()
            return dict(record) if record else None
        
        try:
            with self.driver.session() as session:
                context = session.execute_read(query_context, variable_name)
                return context
        except Exception as e:
            print(f"查询知识图谱失败: {e}")
            return None
    
    def explain_anomaly_feature(
        self,
        feature_name: str,
        anomaly_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        解释异常特征的物理含义和可能原因
        
        Args:
            feature_name: 特征名称（如 feature4）
            anomaly_info: 可选的异常信息（统计值、偏差等）
            
        Returns:
            包含详细解释和建议的字典
        """
        # 1. 映射 feature 到实际变量名
        variable_name = FEATURE_MAPPING.get(feature_name)
        if not variable_name:
            return {
                "success": False,
                "error": f"未找到 {feature_name} 的映射"
            }
        
        # 2. 从知识图谱查询上下文
        kg_context = self.get_variable_context(variable_name)
        
        # 3. 构建解释
        explanation = {
            "success": True,
            "feature": feature_name,
            "variable_name": variable_name,
            "subsystem": None,
            "subsystem_cn": None,
            "function": None,
            "function_cn": None,
            "physical_meaning": None,
            "possible_causes": [],
            "troubleshooting_steps": [],
            "related_variables": []
        }
        
        if kg_context:
            subsystem = kg_context.get("subsystem")
            function = kg_context.get("function")
            
            explanation["subsystem"] = subsystem
            explanation["subsystem_cn"] = SUBSYSTEM_NAMES.get(subsystem, subsystem)
            explanation["function"] = function
            explanation["function_cn"] = FUNCTION_NAMES.get(function, function)
            
            # 4. 生成物理含义解释
            explanation["physical_meaning"] = self._generate_physical_meaning(
                variable_name, 
                explanation["subsystem_cn"], 
                explanation["function_cn"]
            )
            
            # 5. 生成可能的异常原因
            explanation["possible_causes"] = self._generate_possible_causes(
                variable_name,
                explanation["subsystem_cn"],
                anomaly_info
            )
            
            # 6. 生成故障排查步骤
            explanation["troubleshooting_steps"] = self._generate_troubleshooting_steps(
                variable_name,
                explanation["subsystem_cn"]
            )
        else:
            # 知识图谱不可用时的降级处理
            explanation["physical_meaning"] = f"{variable_name} 的物理参数"
            explanation["possible_causes"] = [
                "参数偏离正常范围",
                "设备老化或故障",
                "环境因素影响"
            ]
        
        return explanation
    
    def _generate_physical_meaning(
        self, 
        variable: str, 
        subsystem: str, 
        function: str
    ) -> str:
        """生成变量的物理含义说明"""
        meanings = {
            "电子枪电源系统": f"{variable} 控制电子束的发射强度和稳定性",
            "束流加速系统": f"{variable} 决定电子束的能量和速度",
            "束流对中系统": f"{variable} 用于调整束流的空间位置和角度",
            "消像散校正系统": f"{variable} 用于修正束流的椭圆形变",
            "束流聚焦系统": f"{variable} 控制束流的聚焦程度和束斑大小",
            "辅助环境系统": f"{variable} 影响设备的热力学稳定性和机械精度"
        }
        return meanings.get(subsystem, f"{variable} 的物理参数")
    
    def _generate_possible_causes(
        self,
        variable: str,
        subsystem: str,
        anomaly_info: Optional[Dict] = None
    ) -> List[str]:
        """生成可能的异常原因"""
        causes_map = {
            "电子枪电源系统": [
                "电源供电不稳定或波动",
                "灯丝老化导致发射效率下降",
                "电极污染或磨损",
                "高压放电或绝缘问题"
            ],
            "束流加速系统": [
                "加速电压设置偏差",
                "电源纹波过大",
                "真空度不足影响加速效率",
                "加速管老化"
            ],
            "束流对中系统": [
                "偏转线圈磁场不均匀",
                "机械振动导致位置偏移",
                "控制电路漂移",
                "校准参数需要重新调整"
            ],
            "消像散校正系统": [
                "消像散器线圈失调",
                "磁场补偿不当",
                "透镜组件机械偏移",
                "电流控制精度下降"
            ],
            "束流聚焦系统": [
                "聚焦透镜磁场强度偏离",
                "透镜组件热膨胀",
                "电源调节精度问题",
                "透镜位置机械漂移"
            ],
            "辅助环境系统": [
                "冷却水温度或压力异常",
                "环境温度波动导致热胀冷缩",
                "机械台架振动",
                "传感器测量误差"
            ]
        }
        return causes_map.get(subsystem, ["参数偏离正常工作范围"])
    
    def _generate_troubleshooting_steps(
        self,
        variable: str,
        subsystem: str
    ) -> List[str]:
        """生成故障排查建议"""
        steps_map = {
            "电子枪电源系统": [
                "1. 检查电源供电稳定性和输出波形",
                "2. 测量灯丝电阻，判断是否老化",
                "3. 检查高压绝缘和连接状态",
                "4. 必要时更换灯丝或电源模块"
            ],
            "束流加速系统": [
                "1. 校验加速电压设定值",
                "2. 测量电源纹波和稳定度",
                "3. 检查真空系统压力",
                "4. 清洁或更换加速管组件"
            ],
            "束流对中系统": [
                "1. 重新进行束流对中校准",
                "2. 检查偏转线圈连接和电流",
                "3. 排查机械振动源",
                "4. 验证控制电路参数"
            ],
            "消像散校正系统": [
                "1. 重新调整消像散补偿参数",
                "2. 检查线圈电流和磁场分布",
                "3. 验证透镜组件对齐",
                "4. 必要时进行全系统校准"
            ],
            "束流聚焦系统": [
                "1. 调整聚焦电流至最佳工作点",
                "2. 检查透镜冷却和温度稳定性",
                "3. 验证电源输出精度",
                "4. 检查机械固定和对齐"
            ],
            "辅助环境系统": [
                "1. 检查冷却水系统运行状态",
                "2. 监控环境温度和湿度",
                "3. 排查振动源并加固设备",
                "4. 校准传感器或更换故障传感器"
            ]
        }
        return steps_map.get(subsystem, ["检查相关参数和设备状态"])
    
    def explain_multiple_features(
        self,
        feature_list: List[str]
    ) -> Dict[str, Any]:
        """
        批量解释多个异常特征
        
        Args:
            feature_list: 特征名称列表
            
        Returns:
            包含所有特征解释的字典
        """
        results = []
        for feature in feature_list:
            explanation = self.explain_anomaly_feature(feature)
            if explanation["success"]:
                results.append(explanation)
        
        return {
            "success": True,
            "count": len(results),
            "explanations": results
        }
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()


# =========================
# 工具定义（LLM Function Calling Schema）
# =========================

KG_DIAGNOSIS_TOOLS = []

KG_DIAGNOSIS_TOOL_FUNCTIONS = {}
