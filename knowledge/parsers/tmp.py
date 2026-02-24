import os

# def count_chars(directory):
#     total = 0
#     for root, dirs, files in os.walk(directory):
#         for f in files:
#             if f.endswith('.txt'):
#                 with open(os.path.join(root, f), 'r', encoding='utf-8') as file:
#                     total += len(file.read().replace(' ', '').replace('\n', '').replace('\t', ''))
#     return total

# gen_chars = count_chars("knowledge/parsers/parser_output/generations")
# all_chars = count_chars("knowledge/parsers/parser_output")

# print(f"generations文件夹总字数: {gen_chars:,}")
# print(f"parser_output总字数: {all_chars:,}")
# print(f"books文件夹占总字数的比例: {all_chars - gen_chars}")

import glob

def gather_papers_txt(papers_dir="knowledge/parsers/parser_output/books", output_dir="knowledge/parsers/parser_output/gather"):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "books_merged.txt")

    txt_files = sorted(glob.glob(os.path.join(papers_dir, "*.txt")))
    all_contents = []

    for txt_file in txt_files:
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            header = f"\n\n# ===== {os.path.basename(txt_file)} =====\n\n"
            all_contents.append(header + content)

    merged_content = "\n".join(all_contents)
    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write(merged_content)
    print(f"已聚合{len(txt_files)}个txt文件，输出到: {output_path}")

# 用法示例
gather_papers_txt()

