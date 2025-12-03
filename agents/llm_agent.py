"""
LLM代理模块
实现与Qwen模型的交互，支持函数调用（Function Calling）
"""

from openai import OpenAI
import json
from typing import Dict, Any, List, Optional
import sys
import os

# 添加父目录到路径以便导入tools模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools import TOOLS, TOOL_FUNCTIONS


class BeamDataAgent:
    """束流数据查询代理"""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        """
        初始化代理
        
        Args:
            api_key: API密钥
            base_url: API基础URL
            model: 模型名称
        """
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key
        )
        self.model = model
        self.conversation_history = []
        self.system_prompt = """你是一个专业的束流数据分析助手。你可以帮助用户查询和分析束流数据。

当用户提出查询请求时，你需要：
1. 理解用户的意图，提取时间范围等关键信息
2. 调用合适的工具函数来获取数据
3. 以清晰、友好的方式向用户展示结果

可用的工具：
- query_beam_data: 查询指定时间范围内的束流数据
- get_data_info: 获取数据集的概要信息
- analyze_beam_fluctuation: 分析指定时间范围内数据的波动情况，检测异常点（纯数据分析，不生成图表）
- visualize_beam_fluctuation: 分析并可视化束流波动数据，会生成详细的文字报告和可视化图表（当用户需要看图、生成图表、可视化分析时使用）

注意：
- 时间格式需要是完整的日期时间，如 "2025-08-31 02:00:00"
- 如果用户只说了日期没说时间，请合理推断（如"两点到三点"指的是凌晨2点到3点）
- 返回结果时，要突出关键信息，如数据条数、统计信息等
- 当用户询问数据波动、异常检测、是否超过阈值等问题时，使用 analyze_beam_fluctuation 工具
- 当用户需要查看图表、生成可视化报告、画图等时，使用 visualize_beam_fluctuation 工具
- visualize_beam_fluctuation 会自动生成图表，图表会展示给用户，你只需告诉用户分析结果即可
"""
    
    def _add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def _call_llm(self, messages: List[Dict], tools: Optional[List] = None) -> Any:
        """
        调用LLM
        
        Args:
            messages: 消息列表
            tools: 工具定义列表
        
        Returns:
            LLM响应
        """
        params = {
            "model": self.model,
            "messages": messages,
        }
        
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"
        
        response = self.client.chat.completions.create(**params)
        return response
    
    def _execute_tool_call(self, tool_call) -> Dict[str, Any]:
        """
        执行工具调用
        
        Args:
            tool_call: 工具调用对象
        
        Returns:
            包含工具执行结果和元数据的字典：
            - result_str: JSON格式的结果字符串（用于传给LLM）
            - images: 生成的图片路径列表（用于前端展示）
        """
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        print(f"\n[工具调用] {function_name}")
        print(f"[参数] {json.dumps(function_args, ensure_ascii=False, indent=2)}")
        
        images = []
        
        # 执行工具函数
        if function_name in TOOL_FUNCTIONS:
            result = TOOL_FUNCTIONS[function_name](**function_args)
            print(f"[结果] 查询成功，返回 {result.get('count', 0)} 条记录")
            
            # 检查是否有生成的图片
            if result.get('plot_path'):
                images.append(result['plot_path'])
                print(f"[图片] 生成图片: {result['plot_path']}")
            
            return {
                "result_str": json.dumps(result, ensure_ascii=False),
                "images": images
            }
        else:
            return {
                "result_str": json.dumps({"error": f"未知的工具函数: {function_name}"}, ensure_ascii=False),
                "images": []
            }
    
    def chat(self, user_input: str) -> Dict[str, Any]:
        """
        与用户对话
        
        Args:
            user_input: 用户输入
        
        Returns:
            包含回复内容和附加信息的字典：
            - response: 助手回复文本
            - images: 生成的图片路径列表
        """
        # 添加用户消息
        self._add_message("user", user_input)
        
        # 构建完整的消息列表
        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
        
        # 第一次调用LLM（可能会返回工具调用请求）
        response = self._call_llm(messages, TOOLS)
        assistant_message = response.choices[0].message
        
        # 收集所有生成的图片
        all_images = []
        
        # 检查是否需要调用工具
        max_iterations = 5  # 防止无限循环
        iteration = 0
        
        while assistant_message.tool_calls and iteration < max_iterations:
            iteration += 1
            
            # 添加助手消息（包含工具调用）
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in assistant_message.tool_calls
                ]
            })
            
            # 执行所有工具调用
            for tool_call in assistant_message.tool_calls:
                tool_result = self._execute_tool_call(tool_call)
                
                # 收集图片
                all_images.extend(tool_result.get("images", []))
                
                # 添加工具调用结果
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result["result_str"]
                })
            
            # 再次调用LLM，让它基于工具结果生成最终回复
            messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
            response = self._call_llm(messages, TOOLS)
            assistant_message = response.choices[0].message
        
        # 获取最终回复
        final_response = assistant_message.content or "抱歉，我无法处理您的请求。"
        
        # 添加最终回复到历史
        if not assistant_message.tool_calls:
            self._add_message("assistant", final_response)
        
        return {
            "response": final_response,
            "images": all_images
        }
    
    def reset_conversation(self):
        """重置对话历史"""
        self.conversation_history = []
        print("对话历史已重置")


class StreamingBeamDataAgent(BeamDataAgent):
    """支持流式输出的束流数据查询代理"""
    
    def chat_stream(self, user_input: str):
        """
        与用户对话（流式输出）
        
        Args:
            user_input: 用户输入
        
        Yields:
            助手回复的文本片段
        """
        # 添加用户消息
        self._add_message("user", user_input)
        
        # 构建完整的消息列表
        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
        
        # 调用LLM（流式）
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            stream=True
        )
        
        # 收集响应
        full_content = ""
        tool_calls_data = []
        current_tool_call = None
        
        for chunk in response:
            delta = chunk.choices[0].delta
            
            # 处理内容
            if delta.content:
                full_content += delta.content
                yield delta.content
            
            # 处理工具调用
            if delta.tool_calls:
                for tool_call_chunk in delta.tool_calls:
                    if tool_call_chunk.index is not None:
                        # 确保列表足够长
                        while len(tool_calls_data) <= tool_call_chunk.index:
                            tool_calls_data.append({
                                "id": "",
                                "type": "function",
                                "function": {"name": "", "arguments": ""}
                            })
                        
                        current_tool_call = tool_calls_data[tool_call_chunk.index]
                        
                        if tool_call_chunk.id:
                            current_tool_call["id"] = tool_call_chunk.id
                        if tool_call_chunk.function:
                            if tool_call_chunk.function.name:
                                current_tool_call["function"]["name"] = tool_call_chunk.function.name
                            if tool_call_chunk.function.arguments:
                                current_tool_call["function"]["arguments"] += tool_call_chunk.function.arguments
        
        # 如果有工具调用，执行并生成最终回复
        if tool_calls_data and any(tc["function"]["name"] for tc in tool_calls_data):
            yield "\n\n"
            
            # 添加助手消息（包含工具调用）
            self.conversation_history.append({
                "role": "assistant",
                "content": full_content,
                "tool_calls": tool_calls_data
            })
            
            # 执行工具调用
            for tool_call_data in tool_calls_data:
                if tool_call_data["function"]["name"]:
                    # 创建工具调用对象
                    class ToolCall:
                        def __init__(self, data):
                            self.id = data["id"]
                            self.type = data["type"]
                            self.function = type('obj', (object,), {
                                'name': data["function"]["name"],
                                'arguments': data["function"]["arguments"]
                            })
                    
                    tool_result = self._execute_tool_call(ToolCall(tool_call_data))
                    
                    # 添加工具调用结果
                    self.conversation_history.append({
                        "role": "tool",
                        "tool_call_id": tool_call_data["id"],
                        "content": tool_result
                    })
            
            # 再次调用LLM生成最终回复（流式）
            messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True
            )
            
            final_content = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    final_content += content
                    yield content
            
            # 添加最终回复到历史
            self._add_message("assistant", final_content)
        else:
            # 没有工具调用，直接添加回复到历史
            self._add_message("assistant", full_content)

