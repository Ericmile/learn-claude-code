import anthropic
import os
import re
import uuid
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

client = anthropic.Anthropic(
    base_url="http://192.168.13.12:30001",
    api_key="empty"
)

# 模拟天气查询函数
def get_weather(location):
    """模拟获取天气信息"""
    weather_data = {
        "北京": {"temperature": "22°C", "condition": "晴", "humidity": "45%"},
        "上海": {"temperature": "25°C", "condition": "多云", "humidity": "60%"},
        "广州": {"temperature": "28°C", "condition": "小雨", "humidity": "75%"},
    }
    return weather_data.get(location, {"temperature": "未知", "condition": "未知", "humidity": "未知"})

def parse_qwen_tool_use(raw_response):
    """解析 Qwen 的 <function=xxx> 格式，转换为 ToolUseBlock"""
    if not raw_response.content:
        return raw_response

    text = raw_response.content[0].text

    # 解析 <function=name>\n<parameter=key>\nvalue\n</parameter>\n</function> 格式
    func_pattern = r'<function=(\w+)>(.*?)</function>'
    func_matches = re.findall(func_pattern, text, re.DOTALL)

    if not func_matches:
        return raw_response

    content_blocks = []
    tool_use_id = f"call_{uuid.uuid4().hex[:24]}"

    # 提取思考部分（function 标签之前的文本）
    first_match_start = text.find('<function=')
    if first_match_start > 0:
        thinking = text[:first_match_start].strip()
        if thinking:
            content_blocks.append(anthropic.types.TextBlock(type="text", text=thinking))

    # 解析每个 function 调用
    for func_name, params_block in func_matches:
        # 解析参数 <parameter=key>\nvalue\n</parameter>
        param_pattern = r'<parameter=(\w+)>(.*?)</parameter>'
        param_matches = re.findall(param_pattern, params_block, re.DOTALL)
        tool_input = {k: v.strip() for k, v in param_matches}

        content_blocks.append(
            anthropic.types.ToolUseBlock(
                type="tool_use",
                id=tool_use_id,
                name=func_name,
                input=tool_input
            )
        )

    # 修改 response 的 content 和 stop_reason
    raw_response.content = content_blocks
    raw_response.stop_reason = "tool_use"

    return raw_response

# ========== 第一步：发送请求，模型决定调用工具 ==========
raw_response = client.messages.create(
    model="Qwen3.5-9B",
    max_tokens=1024,
    tools=[{
        "name": "get_weather",
        "description": "Get the weather in a location",
        "input_schema": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"]
        }
    }],
    messages=[{"role": "user", "content": "北京天气怎么样？"}]
)

# 解析 Qwen 输出，转换为 ToolUseBlock 格式
response = parse_qwen_tool_use(raw_response)

print("=" * 50)
print("第一步：模型响应（请求调用工具）")
print("=" * 50)
print(f"Stop Reason: {response.stop_reason}")
print(f"Content: {response.content}")

# ========== 第二步：检查模型是否请求调用工具 ==========
if response.stop_reason == "tool_use":
    # 提取工具调用信息
    tool_use = next(block for block in response.content if block.type == "tool_use")
    tool_name = tool_use.name
    tool_input = tool_use.input

    print("\n" + "=" * 50)
    print(f"第二步：执行工具 - {tool_name}")
    print("=" * 50)
    print(f"参数: {tool_input}")

    # 真正执行工具函数
    if tool_name == "get_weather":
        weather_result = get_weather(tool_input["location"])
        print(f"查询结果: {weather_result}")

        # ========== 第三步：将工具结果返回给模型 ==========
        print("\n" + "=" * 50)
        print("第三步：将工具结果返回给模型，获取最终回复")
        print("=" * 50)

        # 构建消息历史（包含原始用户消息、模型的工具调用请求、和工具执行结果）
        messages = [
            {"role": "user", "content": "北京天气怎么样？"},
            {"role": "assistant", "content": response.content},
            {
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": str(weather_result)
                }]
            }
        ]

        # 再次调用模型，这次会给出最终回复
        final_response = client.messages.create(
            model="Qwen3.5-9B",
            max_tokens=1024,
            tools=[{
                "name": "get_weather",
                "description": "Get the weather in a location",
                "input_schema": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"]
                }
            }],
            messages=messages
        )

        print("\n最终回复:")
        print(final_response.content[0].text)
else:
    print("模型没有请求调用工具")
