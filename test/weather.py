import anthropic
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

client = anthropic.Anthropic(
    base_url="http://192.168.13.12:30001",
    api_key="empty"
)

# 尝试发送一个带有 tools 参数的请求
response = client.messages.create(
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
print(response)