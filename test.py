import os

def find_files_with_keyword(root_dir, keyword):
    result = []
    # os.walk 会递归遍历 root_dir 下所有子目录和文件
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if keyword in filename:
                full_path = os.path.join(dirpath, filename)
                result.append(full_path)
    return result

if __name__ == "__main__":
    root_dir = r"D:\\"      # 要搜索的根目录
    keyword = "生产"        # 要匹配的关键字

    paths = find_files_with_keyword(root_dir, keyword)
    if not paths:
        print(f"未找到包含“{keyword}”的文件。")
    else:
        print("找到以下文件：")
        for p in paths:
            print(p)