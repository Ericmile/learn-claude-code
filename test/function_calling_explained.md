# Function Calling 完整流程说明

## 问题：为什么没有查询出天气？

**答案**：Anthropic API 的 function calling 需要手动执行工具调用，分为 3 个步骤：

---

## 流程图

```
用户提问 → 模型分析 → 模型返回"要调用工具" → 代码执行工具 → 将结果返回模型 → 模型给出最终回复
   ↓                                    ↑
  "北京天气怎么样？"              get_weather(location="北京")
                                      ↓
                                  实际查询天气数据
                                      ↓
                                  {"temperature": "22°C", ...}
```

---

## 三步详解

### **第一步**：模型决定调用工具
```python
response = client.messages.create(
    model="...",
    tools=[...],
    messages=[{"role": "user", "content": "北京天气怎么样？"}]
)
# 返回：stop_reason="tool_use"
#       content 包含：ToolUseBlock(name="get_weather", input={"location": "北京"})
```

**此时还没有真正执行工具！** 模型只是说："我想调用 get_weather，参数是北京"

---

### **第二步**：代码执行工具（关键！）
```python
# 代码中需要手动提取并执行
tool_use = response.content[1]  # 获取 ToolUseBlock
if tool_use.name == "get_weather":
    result = get_weather(tool_use.input["location"])  # 真正执行！
```

**这是缺失的步骤！** 原脚本停在这里，所以没有查询天气。

---

### **第三步**：将工具结果返回给模型
```python
# 构建完整对话历史
messages = [
    {"role": "user", "content": "北京天气怎么样？"},
    {"role": "assistant", "content": response.content},  # 模型要调用工具
    {
        "role": "user",
        "content": [{
            "type": "tool_result",
            "tool_use_id": tool_use.id,
            "content": str(result)  # 工具执行结果
        }]
    }
]

# 再次调用，模型会基于工具结果给出最终回复
final_response = client.messages.create(model="...", messages=messages)
```

---

## 原脚本 vs 完整脚本对比

| 项目 | weather.py（原脚本） | weather_complete.py（完整版） |
|------|---------------------|---------------------------|
| 模型调用工具 | ✅ | ✅ |
| 代码执行工具 | ❌ **缺失** | ✅ |
| 返回结果给模型 | ❌ | ✅ |
| 获取最终回复 | ❌ | ✅ |
| 输出 | 工具调用请求 | 完整天气信息 |

---

## 关键要点

1. **Anthropic API 不会自动执行工具**，只告诉你"要调用什么工具"
2. **必须手动执行工具函数**（第二步）
3. **必须将结果返回给模型**才能得到最终回复（第三步）
4. 这不同于 OpenAI 的自动 function calling

---

## 运行完整示例

```bash
python test/weather_complete.py
```

输出：
```
第一步：模型响应（请求调用工具）
Stop Reason: tool_use

第二步：执行工具 - get_weather
查询结果: {'temperature': '22°C', 'condition': '晴', 'humidity': '45%'}

第三步：将工具结果返回给模型
最终回复:
根据最新的天气信息，北京目前的天气状况如下：
🌡️ 温度：22°C
☀️ 天气：晴
💧 湿度：45%
```
