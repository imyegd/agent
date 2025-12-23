"""MinerU API PDF解析器"""
import os
import sys
import requests
import time
import uuid
import zipfile
import io
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from knowledge.parsers.base_parser import BaseParser
else:
    from .base_parser import BaseParser


class MinerUPdfParser(BaseParser):
    """MinerU PDF解析器 - 批量上传模式"""
    
    BASE_URL = "https://mineru.net/api/v4"
    
    def __init__(self):
        # 从环境变量读取API Key
        api_key = os.getenv("MINERU_API_KEY")
        if not api_key:
            raise ValueError("未设置 MINERU_API_KEY 环境变量，请在 .env 文件中配置")
        
        self.header = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def _upload_file(self, file_path):
        """上传文件并返回batch_id"""
        file_name = os.path.basename(file_path)
        data_id = str(uuid.uuid4())[:8]
        
        # 1. 申请上传URL
        data = {
            "files": [{"name": file_name, "data_id": data_id}],
            "model_version": "vlm"
        }
        
        response = requests.post(
            f"{self.BASE_URL}/file-urls/batch",
            headers=self.header,
            json=data
        )
        result = response.json()
        
        if result["code"] != 0:
            raise Exception(f"申请上传URL失败: {result.get('msg', result)}")
        
        batch_id = result["data"]["batch_id"]
        upload_url = result["data"]["file_urls"][0]
        
        # 2. 上传文件
        with open(file_path, 'rb') as f:
            res_upload = requests.put(upload_url, data=f)
            if res_upload.status_code != 200:
                raise Exception(f"上传失败: {res_upload.status_code}")
        
        return batch_id, file_name
    
    def _get_batch_result(self, batch_id, file_name):
        """查询批量任务结果"""
        while True:
            response = requests.get(
                f"{self.BASE_URL}/extract-results/batch/{batch_id}",
                headers=self.header
            )
            result = response.json()
            
            if result["code"] != 0:
                raise Exception(f"查询失败: {result.get('msg', result)}")
            
            # 找到对应文件的结果
            for item in result["data"]["extract_result"]:
                if item["file_name"] == file_name:
                    state = item["state"]
                    
                    if state == "done":
                        return item["full_zip_url"]
                    elif state == "failed":
                        raise Exception(f"解析失败: {item.get('err_msg', '未知错误')}")
                    else:
                        # waiting-file, pending, running, converting
                        print(f"状态: {state}")
            
            time.sleep(3)
    
    def _extract_text_from_zip(self, zip_url):
        """下载zip并提取markdown文本"""
        response = requests.get(zip_url)
        if response.status_code != 200:
            raise Exception(f"下载zip失败: {response.status_code}")
        
        # 解析zip
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # 查找markdown文件
            md_files = [f for f in z.namelist() if f.endswith('.md')]
            if md_files:
                with z.open(md_files[0]) as f:
                    return f.read().decode('utf-8')
            
            # 如果没有md，尝试找txt
            txt_files = [f for f in z.namelist() if f.endswith('.txt')]
            if txt_files:
                with z.open(txt_files[0]) as f:
                    return f.read().decode('utf-8')
        
        raise Exception("zip中未找到可读取的文本文件")
    
    def parse(self, file_path: str) -> str:
        """解析PDF"""
        try:
            # 1. 上传文件（系统会自动提交解析任务）
            print(f"[1/3] 上传文件: {os.path.basename(file_path)}")
            batch_id, file_name = self._upload_file(file_path)
            
            # 2. 等待解析完成
            print(f"[2/3] 等待解析完成 (batch_id: {batch_id})")
            zip_url = self._get_batch_result(batch_id, file_name)
            
            # 3. 下载并提取文本
            print(f"[3/3] 提取文本")
            text = self._extract_text_from_zip(zip_url)
            
            print(f"✓ 解析完成: {len(text)} 字符")
            return text
            
        except Exception as e:
            print(f"✗ 解析失败: {e}")
            return ""


if __name__ == "__main__":
    parser = MinerUPdfParser()
    
    file_path = sys.argv[1] if len(sys.argv) > 1 else \
                "knowledge\data\电子枪单能电子束流强度稳定装置的研制_郝绿原.pdf"
    filename = os.path.basename(file_path)
    output_dir = "knowledge/parsers/test_output"
    
    text = parser.parse(file_path)
    
    if text:
        output_filename = os.path.splitext(filename)[0] + "_parsed.txt"
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"\n前500字符:\n{text[:500]}")
