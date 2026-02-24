"""
问题生成脚本

功能：
1. 从 parser_output 中随机截取定长文本片段
2. 用 LLM 根据文本片段生成问题
3. 通过最长公共子串匹配，在不同 chunker 方法的输出中找到最匹配的块
4. 保存问题和对应的 chunk 标签
"""
import os
import sys
import json
import random
import time
from typing import List, Dict, Tuple
from openai import OpenAI

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config


def read_all_parsed_texts() -> List[Tuple[str, str]]:
    """
    读取所有解析后的文本
    
    Returns:
        [(filename, content), ...]
    """
    parser_output_dir = "knowledge/parsers/parser_output"
    texts = []
    
    for filename in os.listdir(parser_output_dir):
        if filename.endswith("_parsed.txt"):
            filepath = os.path.join(parser_output_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if len(content) >= 1000:  # 只保留足够长的文档
                        texts.append((filename, content))
            except Exception as e:
                print(f"[警告] 读取文件失败: {filename}: {e}")
    
    return texts


def extract_random_fragments(texts: List[Tuple[str, str]], 
                             fragment_length: int = 1000,
                             num_fragments: int = 5) -> List[Dict]:
    """
    从文档中随机截取文本片段
    
    Args:
        texts: [(filename, content), ...]
        fragment_length: 片段长度
        num_fragments: 要截取的片段数量
        
    Returns:
        [{'filename': str, 'start_pos': int, 'end_pos': int, 'text': str}, ...]
    """
    fragments = []
    
    for _ in range(num_fragments):
        # 随机选择一个文档
        filename, content = random.choice(texts)
        
        # 随机选择起始位置
        if len(content) <= fragment_length:
            start_pos = 0
            end_pos = len(content)
        else:
            start_pos = random.randint(0, len(content) - fragment_length)
            end_pos = start_pos + fragment_length
        
        fragment_text = content[start_pos:end_pos]
        
        fragments.append({
            'filename': filename,
            'start_pos': start_pos,
            'end_pos': end_pos,
            'text': fragment_text
        })
    
    return fragments


def generate_questions_from_fragment(fragment_text: str, 
                                   num_questions: int = 3,
                                   max_retries: int = 3,
                                   retry_delay: int = 5,
                                   request_delay: int = 2) -> List[str]:
    """
    用 LLM 根据文本片段生成问题（带重试机制）
    
    Args:
        fragment_text: 文本片段
        num_questions: 生成问题数量
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        request_delay: 成功请求后的延迟（秒），避免限流
        
    Returns:
        问题列表
    """
    client = OpenAI(
        base_url=Config.BASE_URL,
        api_key=Config.API_KEY
    )
    
    prompt = f"""请根据以下文本内容，生成 {num_questions} 个独立的、高质量的问题。

要求：
1. 问题必须基于文本中的实际内容（不要引用"图X"、"表X"、"如图所示"、"如上所述"等）
2. 问题应该关注核心概念、技术方法、研究结论、系统特性等实质内容
3. 问题应该是知识性的、可以通过文本内容回答的
4. 问题应该多样化，涵盖不同角度（是什么、为什么、怎么做、有什么特点等）
5. 每个问题独立成句，不依赖其他问题或外部上下文
6. 每个问题单独一行，不需要编号

示例对比：
好的问题："BEPCII加速器的束流匹配采用了什么技术方法？"
好的问题："重离子治疗系统相比传统放疗有什么优势？"
好的问题："Q3D磁谱仪的分辨率可以达到多少？"
不好："图9展示的是什么结构？"（引用了图表）
不好："该系统的主要创新点是什么？"（"该系统"指代不明）
不好："如上所述，这种方法的优势在哪？"（依赖上下文）

文本内容：
{fragment_text}

请直接输出问题，每行一个："""
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=Config.MODEL_NAME,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8
            )
            
            questions_text = response.choices[0].message.content.strip()
            
            # 解析问题
            questions = []
            for line in questions_text.split('\n'):
                line = line.strip()
                # 去除可能的编号
                if line and not line.startswith('#'):
                    # 去除前导的数字编号
                    import re
                    cleaned = re.sub(r'^\d+[\.\)、]\s*', '', line)
                    if cleaned:
                        questions.append(cleaned)
            
            # 成功生成，添加延迟避免限流
            if request_delay > 0:
                time.sleep(request_delay)
            
            return questions[:num_questions]  # 确保返回指定数量
        
        except Exception as e:
            error_msg = str(e)
            
            # 检查是否是限流错误（429）
            if "429" in error_msg or "rate limit" in error_msg.lower():
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)  # 指数退避
                    print(f"      [限流] 遇到限流，等待 {wait_time} 秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"[错误] 达到最大重试次数，生成问题失败: {e}")
                    return []
            else:
                # 其他错误，直接返回
                print(f"[错误] 生成问题失败: {e}")
                return []
    
    return []


def calculate_overlap_ratio(fragment_text: str, chunk_text: str) -> float:
    """
    计算两个文本的重叠度（快速版本）
    
    方法：计算 fragment 中有多少字符出现在 chunk 中
    
    Args:
        fragment_text: 文本片段
        chunk_text: chunk 文本
        
    Returns:
        重叠度 (0-1)
    """
    if not fragment_text or not chunk_text:
        return 0.0
    
    # 方法1：简单字符包含检查（最快）
    # 如果 fragment 完全在 chunk 中，直接返回1.0
    if fragment_text in chunk_text:
        return 1.0
    
    # 方法2：计算字符级重叠
    # 将 fragment 分成若干个小窗口（比如100字符），看有多少窗口在 chunk 中
    window_size = 100
    total_windows = 0
    matched_windows = 0
    
    for i in range(0, len(fragment_text), window_size // 2):  # 滑动窗口，步长为窗口的一半
        window = fragment_text[i:i + window_size]
        if len(window) < 50:  # 太短的窗口跳过
            continue
        total_windows += 1
        if window in chunk_text:
            matched_windows += 1
    
    if total_windows == 0:
        return 0.0
    
    return matched_windows / total_windows


def extract_source_filename(parsed_filename: str) -> str:
    """
    从 parsed 文件名中提取源文件名标识
    
    例如：基于CRIO的强流加速器机器快保护系统_叶毅_parsed.txt
    提取：基于CRIO的强流加速器机器快保护系统_叶毅
    
    Args:
        parsed_filename: parsed 文件名
        
    Returns:
        源文件名标识
    """
    if parsed_filename.endswith('_parsed.txt'):
        return parsed_filename[:-11]  # 去除 '_parsed.txt'
    return parsed_filename


def convert_child_to_parent_filename(child_chunk_file: str,
                                    source_filename: str,
                                    chunker_output_dir: str) -> str:
    """
    将 parent_child 的子块文件名转换为对应的父块文件名
    
    通过读取元数据文件，获取子块对应的父块文件名
    
    Args:
        child_chunk_file: 子块文件名 (例如: xxx_parsed_chunk_5.txt)
        source_filename: 源文件名 (例如: xxx_parsed.txt)
        chunker_output_dir: chunker 输出目录
        
    Returns:
        父块文件名 (例如: xxx_parsed_chunk_2.txt，与 chapter 格式一致)
    """
    import json
    
    chunker_dir = os.path.join(chunker_output_dir, "parent_child")
    
    if not os.path.exists(chunker_dir):
        return ""
    
    # 提取源文件标识
    source_identifier = extract_source_filename(source_filename)
    
    # 查找对应的元数据文件
    metadata_filename = f"{source_identifier}_metadata.json"
    metadata_path = os.path.join(chunker_dir, metadata_filename)
    
    if not os.path.exists(metadata_path):
        print(f"      [警告] 元数据文件不存在: {metadata_filename}")
        return ""
    
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # 从子块文件名提取子块索引
        # 文件名格式: xxx_parsed_chunk_N.txt
        if '_chunk_' not in child_chunk_file:
            return ""
        
        parts = child_chunk_file.rsplit('_chunk_', 1)
        if len(parts) != 2:
            return ""
        
        child_idx_str = parts[1].replace('.txt', '')
        try:
            child_idx = int(child_idx_str) - 1  # 文件名从1开始，索引从0开始
        except ValueError:
            return ""
        
        # 从元数据中获取父块索引
        child_to_parent_map = metadata.get('child_to_parent_map', {})
        parent_filenames = metadata.get('parent_filenames', {})
        
        parent_idx = child_to_parent_map.get(str(child_idx))
        
        if parent_idx is not None:
            # 获取父块文件名
            parent_filename = parent_filenames.get(str(parent_idx), parent_filenames.get(parent_idx, ''))
            return parent_filename
        
    except Exception as e:
        print(f"      [错误] 读取元数据失败: {e}")
    
    return ""


def find_best_matching_chunk(fragment_text: str, 
                             source_filename: str,
                             chunker_type: str,
                             chunker_output_dir: str) -> Tuple[str, float]:
    """
    在指定 chunker 方法的输出中找到最匹配的块
    
    优化：只在源文件对应的 chunk 中查找，大大缩小搜索范围
    
    Args:
        fragment_text: 文本片段
        source_filename: 源文件名（parsed.txt）
        chunker_type: chunker 类型 (fixed, semantic, chapter 等)
        chunker_output_dir: chunker 输出目录
        
    Returns:
        (chunk_filename, overlap_ratio)
    """
    chunker_dir = os.path.join(chunker_output_dir, chunker_type)
    
    if not os.path.exists(chunker_dir):
        print(f"[警告] Chunker 输出目录不存在: {chunker_dir}")
        return ("", 0.0)
    
    # 提取源文件标识
    source_identifier = extract_source_filename(source_filename)
    
    best_chunk = ""
    best_ratio = 0.0
    candidate_count = 0
    
    # 遍历所有 chunk 文件，但只处理同源文件的 chunk
    for chunk_file in os.listdir(chunker_dir):
        if not chunk_file.endswith('.txt'):
            continue
        
        # 关键优化：只处理文件名包含源文件标识的 chunk
        if source_identifier not in chunk_file:
            continue
        
        candidate_count += 1
        chunk_path = os.path.join(chunker_dir, chunk_file)
        
        try:
            with open(chunk_path, 'r', encoding='utf-8') as f:
                chunk_text = f.read()
            
            # 计算重叠度（使用优化后的快速方法）
            overlap_ratio = calculate_overlap_ratio(fragment_text, chunk_text)
            
            if overlap_ratio > best_ratio:
                best_ratio = overlap_ratio
                best_chunk = chunk_file
        
        except Exception as e:
            continue
    
    # 如果没有找到匹配的 chunk（可能是文件名格式不同），则警告
    if candidate_count == 0:
        print(f"      [警告] 未找到源文件 {source_identifier} 的 chunk 文件")
    
    return (best_chunk, best_ratio)


def generate_qa_dataset(num_fragments: int = 5,
                       questions_per_fragment: int = 3,
                       fragment_length: int = 1000,
                       chunker_types: List[str] = None,
                       output_file: str = "experiment/data/qa_dataset.json",
                       request_delay: int = 2):
    """
    生成问答数据集
    
    Args:
        num_fragments: 要截取的文本片段数量
        questions_per_fragment: 每个片段生成的问题数量
        fragment_length: 片段长度
        chunker_types: 要评估的 chunker 类型列表
        output_file: 输出文件路径
        request_delay: API 请求间隔（秒），避免限流
    """
    if chunker_types is None:
        chunker_types = ["fixed", "semantic", "chapter"]
    
    chunker_output_dir = "knowledge/chunkers/chunker_output"
    
    print("=" * 80)
    print("生成问答数据集")
    print("=" * 80)
    
    # 1. 读取所有文档
    print("\n[步骤 1] 读取解析后的文档...")
    texts = read_all_parsed_texts()
    print(f"  找到 {len(texts)} 个文档")
    
    if len(texts) == 0:
        print("[错误] 没有找到解析后的文档")
        return
    
    # 2. 截取随机片段
    print(f"\n[步骤 2] 随机截取 {num_fragments} 个文本片段 (长度: {fragment_length})...")
    fragments = extract_random_fragments(texts, fragment_length, num_fragments)
    print(f"  成功截取 {len(fragments)} 个片段")
    
    # 3. 生成问题并匹配 chunks
    print(f"\n[步骤 3] 为每个片段生成 {questions_per_fragment} 个问题并匹配 chunks...")
    
    dataset = []
    
    for i, fragment in enumerate(fragments, 1):
        print(f"\n  [{i}/{len(fragments)}] 处理片段: {fragment['filename']}")
        print(f"    位置: {fragment['start_pos']}-{fragment['end_pos']}")
        
        # 生成问题
        questions = generate_questions_from_fragment(
            fragment['text'], 
            questions_per_fragment,
            request_delay=request_delay
        )
        print(f"    生成了 {len(questions)} 个问题")
        
        if not questions:
            continue
        
        # 对每个 chunker 类型，找到最匹配的 chunk
        chunk_labels = {}
        
        for chunker_type in chunker_types:
            best_chunk, overlap_ratio = find_best_matching_chunk(
                fragment['text'],
                fragment['filename'],  # 传入源文件名
                chunker_type, 
                chunker_output_dir
            )
            
            # 对于 parent_child 类型，需要转换为父块文件名
            if chunker_type == "parent_child" and best_chunk:
                parent_chunk_file = convert_child_to_parent_filename(
                    best_chunk, 
                    fragment['filename'],
                    chunker_output_dir
                )
                if parent_chunk_file:
                    best_chunk = parent_chunk_file
            
            chunk_labels[chunker_type] = {
                'chunk_file': best_chunk,
                'overlap_ratio': overlap_ratio
            }
            
            print(f"    [{chunker_type}] 最佳匹配: {best_chunk} (重合度: {overlap_ratio:.2%})")
        
        # 保存数据
        for question in questions:
            dataset.append({
                'question': question,
                'source_file': fragment['filename'],
                'fragment_start': fragment['start_pos'],
                'fragment_end': fragment['end_pos'],
                'fragment_text': fragment['text'],
                'chunk_labels': chunk_labels
            })
    
    # 4. 保存数据集
    print(f"\n[步骤 4] 保存数据集到 {output_file}...")
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"  成功保存 {len(dataset)} 条问答数据")
    
    # 5. 打印统计信息
    print("\n" + "=" * 80)
    print("数据集统计")
    print("=" * 80)
    print(f"总问题数: {len(dataset)}")
    print(f"文本片段数: {len(fragments)}")
    print(f"每片段问题数: {questions_per_fragment}")
    
    # 打印示例
    if dataset:
        print("\n示例数据:")
        example = dataset[0]
        print(f"\n  问题: {example['question']}")
        print(f"  来源: {example['source_file']}")
        print(f"  片段: {example['fragment_text'][:100]}...")
        print(f"  标签:")
        for chunker_type, label in example['chunk_labels'].items():
            print(f"    [{chunker_type}] {label['chunk_file']} ({label['overlap_ratio']:.2%})")


if __name__ == "__main__":
    # 示例：生成 5 个片段，每个片段 3 个问题
    # 实际使用时可以改成 num_fragments=500
    generate_qa_dataset(
        num_fragments=300,
        questions_per_fragment=3,
        fragment_length=1000,
        chunker_types=["fixed", "semantic", "chapter"],
        output_file="experiment/data/qa_dataset.json",
        request_delay=3  # API 请求间隔 3 秒，避免限流
    )

