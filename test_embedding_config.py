"""
测试 Embedding 配置
验证从 .env 文件读取配置是否正常
"""

import numpy as np
from config.config import Config
from knowledge.embeddings import create_embedder


def cosine_similarity(vec1, vec2):
    """计算余弦相似度"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)

def test_config():
    """测试配置加载"""
    print("=" * 50)
    print("配置测试")
    print("=" * 50)
    
    # 显示当前配置
    print(f"\n✓ API Key: {Config.API_KEY[:20]}..." if Config.API_KEY else "✗ API Key 未配置")
    print(f"✓ Base URL: {Config.BASE_URL}")
    print(f"✓ Embedding Model: {Config.EMBEDDING_MODEL}")
    
    # 获取 Embedding 配置
    embedding_config = Config.get_embedding_config()
    print(f"\n📦 Embedding 配置:")
    for key, value in embedding_config.items():
        if key == 'api_key' and value:
            print(f"  - {key}: {value[:20]}...")
        else:
            print(f"  - {key}: {value}")
    
    return Config.API_KEY is not None and Config.API_KEY != ''


def test_embedder():
    """测试 Embedder 初始化"""
    print("\n" + "=" * 50)
    print("Embedder 测试")
    print("=" * 50 + "\n")
    
    try:
        # 测试 API Embedder
        print("1. 测试 API Embedder...")
        api_embedder = create_embedder("api")
        print(f"   ✓ API Embedder 创建成功")
        print(f"   模型: {api_embedder.model}")
        print(f"   Base URL: {api_embedder.base_url}")
        
        # 测试简单的 embedding
        print("\n2. 测试 Embedding 调用...")
        test_text = "你好，世界！"
        result = api_embedder.embed(test_text)
        print(f"   ✓ Embedding 成功")
        print(f"   输入: {test_text}")
        print(f"   向量维度: {result.shape}")
        print(f"   向量前5个值: {result[0][:5]}")
        
        return True
        
    except ValueError as e:
        print(f"   ✗ 配置错误: {e}")
        return False
    except Exception as e:
        print(f"   ✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_similarity():
    """测试句子相似度"""
    print("\n" + "=" * 50)
    print("句子相似度测试")
    print("=" * 50 + "\n")
    
    try:
        # 创建 API Embedder
        print("创建 Embedder...")
        embedder = create_embedder("api")
        print("✓ Embedder 创建成功\n")
        
        # 测试句子
        text1 = "我的家在东北"
        text2 = "大河南是我滴家乡"
        
        print(f"句子 1: {text1}")
        print(f"句子 2: {text2}")
        print()
        
        # 获取 embeddings
        print("正在计算 embeddings...")
        embedding1 = embedder.embed(text1)
        embedding2 = embedder.embed(text2)
        
        print(f"✓ Embedding 完成")
        print(f"  向量 1 维度: {embedding1.shape}")
        print(f"  向量 2 维度: {embedding2.shape}")
        
        # 计算余弦相似度
        similarity = cosine_similarity(embedding1[0], embedding2[0])
        
        print(f"\n📊 相似度分析:")
        print(f"  余弦相似度: {similarity:.6f}")
        print(f"  相似度百分比: {similarity * 100:.2f}%")
        
        # 相似度评价
        if similarity > 0.9:
            level = "非常相似 🎯"
        elif similarity > 0.8:
            level = "很相似 ✅"
        elif similarity > 0.7:
            level = "比较相似 👍"
        elif similarity > 0.5:
            level = "有一定相似 🤔"
        else:
            level = "不太相似 ❌"
        
        print(f"  相似度等级: {level}")
        
        # 额外测试：对比不相似的句子
        print(f"\n🔍 对比测试（不相似的句子）:")
        text3 = "今天天气真好"
        embedding3 = embedder.embed(text3)
        similarity_diff = cosine_similarity(embedding1[0], embedding3[0])
        
        print(f"  \"{text1}\" vs \"{text3}\"")
        print(f"  相似度: {similarity_diff:.6f} ({similarity_diff * 100:.2f}%)")
        
        print(f"\n✓ 相似度对比:")
        print(f"  相关句子: {similarity:.6f}")
        print(f"  不相关句子: {similarity_diff:.6f}")
        print(f"  差异倍数: {similarity / similarity_diff:.2f}x")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hybrid_embedder():
    """测试混合 Embedder"""
    print("\n" + "=" * 50)
    print("混合 Embedder 测试")
    print("=" * 50 + "\n")
    
    try:
        print("创建混合 Embedder...")
        hybrid_embedder = create_embedder("hybrid")
        print("✓ 混合 Embedder 创建成功\n")
        
        # 测试一些语料
        corpus = [
            "束流强度是加速器的重要参数",
            "质子束流的测量需要高精度仪器",
            "HIRFL加速器可以产生重离子束流"
        ]
        
        # 如果有 simple embedder，先训练
        if hybrid_embedder.simple_embedder:
            hybrid_embedder.fit(corpus)
            print("✓ TF-IDF 向量化器训练完成")
        
        # 测试 embedding
        test_text = "如何测量束流强度？"
        result = hybrid_embedder.embed(test_text)
        print(f"\n测试文本: {test_text}")
        print(f"✓ Embedding 成功")
        print(f"向量维度: {result.shape}")
        
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 开始测试 Embedding 配置\n")
    
    # 测试配置加载
    config_ok = test_config()
    

        # 测试句子相似度
    similarity_ok = test_similarity()


