"""
Flask Web 应用 - 束流数据智能分析系统
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime

from agents import BeamDataAgent
from config import Config
from tools import TOOL_FUNCTIONS

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化配置
config = Config.get_api_config()

# 全局 Agent 实例（避免重复初始化）
agent = None

def get_agent():
    """获取或创建 Agent 实例"""
    global agent
    if agent is None:
        agent = BeamDataAgent(
            api_key=config['api_key'],
            base_url=config['base_url'],
            model=config['model']
        )
    return agent


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """聊天接口 - 自然语言对话"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': '消息不能为空'
            }), 400
        
        # 调用 Agent
        agent_instance = get_agent()
        result = agent_instance.chat(user_message)
        
        # 处理图片路径，确保前端可以访问
        images = []
        for img_path in result.get('images', []):
            # 如果是绝对路径，转换为相对路径
            if os.path.isabs(img_path):
                # 提取 output 目录下的文件名
                img_name = os.path.basename(img_path)
                images.append(f'/output/{img_name}')
            elif img_path.startswith('output/') or img_path.startswith('output\\'):
                # 已经是相对路径，添加前导斜杠
                img_name = os.path.basename(img_path)
                images.append(f'/output/{img_name}')
            else:
                images.append(f'/{img_path}')
        
        return jsonify({
            'success': True,
            'response': result.get('response', ''),
            'images': images,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/query', methods=['POST'])
def query_data():
    """数据查询接口"""
    try:
        data = request.json
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        columns = data.get('columns', None)
        
        if not start_time or not end_time:
            return jsonify({
                'success': False,
                'error': '请提供开始和结束时间'
            }), 400
        
        # 调用工具函数
        result = TOOL_FUNCTIONS['query_beam_data'](
            start_time=start_time,
            end_time=end_time,
            columns=columns
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analyze', methods=['POST'])
def analyze_fluctuation():
    """波动分析接口"""
    try:
        data = request.json
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not start_time or not end_time:
            return jsonify({
                'success': False,
                'error': '请提供开始和结束时间'
            }), 400
        
        # 调用 PLS 分析工具
        result = TOOL_FUNCTIONS['analyze_beam_fluctuation'](
            start_time=start_time,
            end_time=end_time
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/visualize', methods=['POST'])
def visualize():
    """可视化接口"""
    try:
        data = request.json
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        
        if not start_time or not end_time:
            return jsonify({
                'success': False,
                'error': '请提供开始和结束时间'
            }), 400
        
        # 调用可视化工具
        result = TOOL_FUNCTIONS['visualize_beam_fluctuation'](
            start_time=start_time,
            end_time=end_time,
            show_plot=True
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/knowledge/search', methods=['POST'])
def search_knowledge():
    """知识库搜索接口"""
    try:
        data = request.json
        query = data.get('query', '')
        top_k = data.get('top_k', 3)
        doc_type = data.get('doc_type', None)
        
        if not query:
            return jsonify({
                'success': False,
                'error': '查询不能为空'
            }), 400
        
        # 调用知识库搜索
        result = TOOL_FUNCTIONS['search_knowledge'](
            query=query,
            top_k=top_k,
            doc_type=doc_type
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/knowledge/features', methods=['POST'])
def explain_features():
    """特征解释接口"""
    try:
        data = request.json
        feature_names = data.get('feature_names', [])
        
        if not feature_names:
            return jsonify({
                'success': False,
                'error': '请提供特征名称'
            }), 400
        
        # 调用特征解释
        result = TOOL_FUNCTIONS['explain_features'](
            feature_names=feature_names
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/data/info', methods=['GET'])
def get_data_info():
    """获取数据集信息接口"""
    try:
        result = TOOL_FUNCTIONS['get_data_info']()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """重置对话历史"""
    try:
        agent_instance = get_agent()
        agent_instance.reset_conversation()
        return jsonify({
            'success': True,
            'message': '对话历史已清空'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/output/<path:filename>')
def serve_output(filename):
    """提供输出文件（如图表）"""
    return send_file(os.path.join('output', filename))


if __name__ == '__main__':
    # 确保输出目录存在
    os.makedirs('output', exist_ok=True)
    
    print("=" * 60)
    print("束流数据智能分析系统 - Web 服务")
    print("=" * 60)
    print(f"访问地址: http://localhost:5000")
    print(f"API 文档: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
