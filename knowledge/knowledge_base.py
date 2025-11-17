"""
知识库管理器
"""
import json
import os
from typing import Dict, List, Any, Optional


class KnowledgeBase:
    """知识库管理器"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化知识库
        
        Args:
            data_dir: 知识库数据目录路径，默认为模块下的data目录
        """
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "data")
        
        self.data_dir = data_dir
        self.features = {}
        self.solutions = []
        self.domain_knowledge = []
        self.best_practices = []
        self.troubleshooting_tips = []
        
        self._load_knowledge()
    
    def _load_knowledge(self):
        """加载所有知识库数据"""
        # 加载特征物理含义
        features_path = os.path.join(self.data_dir, "features.json")
        if os.path.exists(features_path):
            with open(features_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.features = data.get('features', {})
            print(f"加载了 {len(self.features)} 个特征定义")
        else:
            print(f"警告: 未找到特征定义文件 {features_path}")
        
        # 加载解决方案
        solutions_path = os.path.join(self.data_dir, "solutions.json")
        if os.path.exists(solutions_path):
            with open(solutions_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.solutions = data.get('solutions', [])
            print(f"加载了 {len(self.solutions)} 个解决方案")
        else:
            print(f"警告: 未找到解决方案文件 {solutions_path}")
        
        # 加载领域知识
        domain_path = os.path.join(self.data_dir, "domain_knowledge.json")
        if os.path.exists(domain_path):
            with open(domain_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.domain_knowledge = data.get('concepts', [])
                self.best_practices = data.get('best_practices', [])
                self.troubleshooting_tips = data.get('troubleshooting_tips', [])
            print(f"加载了 {len(self.domain_knowledge)} 个领域概念")
        else:
            print(f"警告: 未找到领域知识文件 {domain_path}")
    
    def get_feature_info(self, feature_name: str) -> Dict[str, Any]:
        """
        获取特征的物理含义和详细信息
        
        Args:
            feature_name: 特征名称，如 "feature1"
            
        Returns:
            特征信息字典
        """
        return self.features.get(feature_name, {})
    
    def get_multiple_features_info(self, feature_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        获取多个特征的信息
        
        Args:
            feature_names: 特征名称列表
            
        Returns:
            特征名称到信息的映射字典
        """
        result = {}
        for name in feature_names:
            info = self.get_feature_info(name)
            if info:
                result[name] = info
        return result
    
    def search_solutions(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        根据关键词搜索解决方案
        
        Args:
            keywords: 关键词列表
            
        Returns:
            匹配的解决方案列表
        """
        matched_solutions = []
        
        for solution in self.solutions:
            # 在问题描述、症状、根本原因中搜索关键词
            search_text = (
                solution.get('problem', '') + ' ' +
                ' '.join(solution.get('symptoms', [])) + ' ' +
                ' '.join(solution.get('root_causes', []))
            ).lower()
            
            # 检查是否匹配任何关键词
            if any(kw.lower() in search_text for kw in keywords):
                matched_solutions.append(solution)
        
        return matched_solutions
    
    def get_solution_by_priority(self, priority: str) -> List[Dict[str, Any]]:
        """
        按优先级获取解决方案
        
        Args:
            priority: 优先级，如 "critical", "high", "medium", "low"
            
        Returns:
            指定优先级的解决方案列表
        """
        return [s for s in self.solutions if s.get('priority') == priority]
    
    def search_concept(self, term: str) -> Optional[Dict[str, Any]]:
        """
        搜索领域概念
        
        Args:
            term: 术语名称
            
        Returns:
            概念信息字典，未找到则返回None
        """
        for concept in self.domain_knowledge:
            if concept.get('term', '').lower() == term.lower():
                return concept
        return None
    
    def get_all_documents(self) -> List[Dict[str, str]]:
        """
        获取所有文档（用于向量化和检索）
        
        Returns:
            文档列表，每个文档包含text和metadata
        """
        docs = []
        
        # 特征描述文档
        for feat_name, feat_info in self.features.items():
            doc_text = (
                f"{feat_name} {feat_info.get('name', '')}. "
                f"{feat_info.get('description', '')} "
                f"相关系统: {feat_info.get('related_to', '')}. "
                f"可能异常原因: {', '.join(feat_info.get('anomaly_causes', []))}. "
                f"影响: {feat_info.get('impact', '')}"
            )
            docs.append({
                "text": doc_text,
                "metadata": {
                    "type": "feature",
                    "name": feat_name,
                    "source": feat_info
                }
            })
        
        # 解决方案文档
        for solution in self.solutions:
            doc_text = (
                f"问题: {solution.get('problem', '')}. "
                f"症状: {', '.join(solution.get('symptoms', []))}. "
                f"根本原因: {', '.join(solution.get('root_causes', []))}. "
                f"解决方案: {', '.join(solution.get('solutions', []))}"
            )
            docs.append({
                "text": doc_text,
                "metadata": {
                    "type": "solution",
                    "problem": solution.get('problem', ''),
                    "priority": solution.get('priority', 'medium'),
                    "source": solution
                }
            })
        
        # 领域知识文档
        for concept in self.domain_knowledge:
            doc_text = (
                f"{concept.get('term', '')}: {concept.get('definition', '')}. "
                f"{concept.get('interpretation', '')}"
            )
            docs.append({
                "text": doc_text,
                "metadata": {
                    "type": "concept",
                    "term": concept.get('term', ''),
                    "category": concept.get('category', ''),
                    "source": concept
                }
            })
        
        return docs
    
    def get_statistics(self) -> Dict[str, int]:
        """
        获取知识库统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "features_count": len(self.features),
            "solutions_count": len(self.solutions),
            "concepts_count": len(self.domain_knowledge),
            "best_practices_count": len(self.best_practices),
            "tips_count": len(self.troubleshooting_tips)
        }

