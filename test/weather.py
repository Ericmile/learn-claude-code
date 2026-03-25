import anthropic
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

client = anthropic.Anthropic(
    base_url=os.getenv("ANTHROPIC_BASE_URL"),
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

# 尝试发送一个带有 tools 参数的请求
response = client.messages.create(
    model=os.getenv("MODEL_ID"),
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