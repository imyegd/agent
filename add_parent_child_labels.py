"""
临时脚本：为 qa_dataset.json 添加 parent_child 的 label
直接复制 chapter 的 label，因为父子分块的大块就是 chapter 分块
"""
import json
import os


def add_parent_child_labels(dataset_file="experiment/data/qa_dataset.json"):
    """
    为数据集添加 parent_child 的 label（复制自 chapter）
    
    Args:
        dataset_file: 数据集文件路径
    """
    print("=" * 80)
    print("添加 parent_child 标签到数据集")
    print("=" * 80)
    
    # 1. 读取数据集
    if not os.path.exists(dataset_file):
        print(f"[错误] 数据集文件不存在: {dataset_file}")
        return
    
    print(f"\n[步骤 1] 读取数据集...")
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    print(f"  找到 {len(dataset)} 个问题")
    
    # 2. 添加 parent_child label
    print(f"\n[步骤 2] 添加 parent_child label...")
    
    added_count = 0
    already_exists_count = 0
    no_chapter_label_count = 0
    
    for item in dataset:
        chunk_labels = item.get('chunk_labels', {})
        
        # 检查是否已经有 parent_child label
        if 'parent_child' in chunk_labels:
            already_exists_count += 1
            continue
        
        # 检查是否有 chapter label
        if 'chapter' not in chunk_labels:
            no_chapter_label_count += 1
            continue
        
        # 复制 chapter 的 label 到 parent_child
        chunk_labels['parent_child'] = chunk_labels['chapter'].copy()
        added_count += 1
    
    print(f"  添加了 {added_count} 个 parent_child label")
    
    if already_exists_count > 0:
        print(f"  跳过 {already_exists_count} 个已有 parent_child label 的问题")
    
    if no_chapter_label_count > 0:
        print(f"  跳过 {no_chapter_label_count} 个没有 chapter label 的问题")
    
    # 3. 备份原文件
    print(f"\n[步骤 3] 备份原文件...")
    backup_file = dataset_file + ".backup"
    
    if os.path.exists(backup_file):
        print(f"  备份文件已存在，跳过备份")
    else:
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        print(f"  备份已保存: {backup_file}")
    
    # 4. 保存更新后的数据集
    print(f"\n[步骤 4] 保存更新后的数据集...")
    
    # 重新读取原文件以获取最新数据（防止刚才的备份操作修改了内存中的数据）
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # 再次添加 label
    for item in dataset:
        chunk_labels = item.get('chunk_labels', {})
        if 'parent_child' not in chunk_labels and 'chapter' in chunk_labels:
            chunk_labels['parent_child'] = chunk_labels['chapter'].copy()
    
    with open(dataset_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"  数据集已更新: {dataset_file}")
    
    # 5. 验证
    print(f"\n[步骤 5] 验证更新...")
    
    with open(dataset_file, 'r', encoding='utf-8') as f:
        updated_dataset = json.load(f)
    
    parent_child_count = sum(1 for item in updated_dataset if 'parent_child' in item.get('chunk_labels', {}))
    chapter_count = sum(1 for item in updated_dataset if 'chapter' in item.get('chunk_labels', {}))
    
    print(f"  chapter label 数量: {chapter_count}")
    print(f"  parent_child label 数量: {parent_child_count}")
    
    if parent_child_count == chapter_count:
        print("\n  [成功] parent_child label 数量与 chapter 一致!")
    else:
        print(f"\n  [警告] parent_child ({parent_child_count}) 与 chapter ({chapter_count}) 数量不一致")
    
    # 6. 显示示例
    print(f"\n[步骤 6] 显示示例...")
    
    for i, item in enumerate(updated_dataset[:3], 1):
        chunk_labels = item.get('chunk_labels', {})
        print(f"\n  问题 {i}: {item['question'][:50]}...")
        
        if 'chapter' in chunk_labels:
            print(f"    chapter:      {chunk_labels['chapter'].get('chunk_file', 'N/A')}")
        
        if 'parent_child' in chunk_labels:
            print(f"    parent_child: {chunk_labels['parent_child'].get('chunk_file', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("完成!")
    print("=" * 80)
    print(f"\n现在可以运行实验评估:")
    print(f"  python experiment/run_experiment.py --chunker-types fixed semantic chapter parent_child")
    print("\n或者只评估（不生成新问题）:")
    print(f"  python experiment/evaluate_chunkers.py")


if __name__ == "__main__":
    add_parent_child_labels()
