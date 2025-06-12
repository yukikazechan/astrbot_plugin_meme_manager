# 如何为 AstrBot 插件添加 LLM 函数工具

本文档旨在提供一个清晰、分步的指南，帮助开发者为 AstrBot 插件正确地添加可由大型语言模型（LLM）调用的函数工具。

## 核心概念

LLM 函数工具允许您将插件中的特定功能（Python 方法）暴露给 LLM。当用户用自然语言提出请求时，LLM 可以智能地判断是否需要调用您的某个工具来完成任务，并自动提取所需参数。

## 关键步骤

要成功注册一个 LLM 函数工具，必须严格遵循以下四个关键步骤。任何一步的遗漏都可能导致工具无法在 AstrBot 管理界面显示或被 LLM 正确调用。

### 步骤 1：正确导入所需模块

您需要从 `astrbot` 的 `api` 和 `core` 中导入所有必要的组件。

```python
# 导入事件和上下文相关的基本组件
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register

# 关键：从 astrbot.api.event.filter 导入 llm_tool 装饰器
from astrbot.api.event.filter import llm_tool

# 关键：导入一个具体的平台事件类型，而不是通用的 AstrMessageEvent
# 例如，如果您的插件主要用于 aiocqhttp (QQ个人号)
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)
```

### 步骤 2：定义函数并使用装饰器

在您的插件类（继承自 `Star`）中定义一个异步方法作为您的工具。

```python
class YourPlugin(Star):
    # ... __init__ 和其他方法 ...

    # 关键：使用 @llm_tool 装饰器，并**强制要求**提供一个唯一的 `name` 参数
    @llm_tool(name="your_unique_tool_name")
    # 关键：函数签名必须是 async def
    # 关键：event 参数必须使用具体的事件类型注解，如 AiocqhttpMessageEvent
    # 关键：函数的返回类型必须注解为 -> MessageEventResult
    async def your_tool_function(self, event: AiocqhttpMessageEvent, param1: str, param2: int) -> MessageEventResult:
        """
        这里是函数的文档字符串，用于向LLM描述工具的功能。
        
        Args:
            param1(string): 参数1的描述。
            param2(number): 参数2的描述。
        """
        # ... 您的工具逻辑代码 ...
```

### 步骤 3：编写符合规范的 Docstring

LLM 会解析函数的文档字符串（docstring）来理解工具的功能和参数。请务必遵循以下格式：
1.  第一行是工具功能的简短描述。
2.  空一行后，使用 `Args:` 来开始参数描述。
3.  每一行描述一个参数，格式为 `参数名(类型): 描述`。类型应为 `string`, `number`, `boolean` 等。

### 步骤 4：实现逻辑并返回 `MessageEventResult`

函数内部实现您的具体业务逻辑，并且**必须**返回一个 `MessageEventResult` 对象。通常使用 `event.plain_result()` 或 `event.chain_result()` 来创建。

```python
# ... 在你的工具函数内部 ...
try:
    # 执行你的逻辑
    result_text = f"成功处理了 {param1} 和 {param2}"
    # 使用 return 返回结果
    return event.plain_result(result_text)
except Exception as e:
    logger.error(f"工具执行失败: {e}")
    return event.plain_result(f"工具执行出错: {e}")
```

## 完整示例

以下是 `astrbot_plugin_galinfo` 插件中的 `search_galgame_tool` 作为完整示例：

```python
# in class galgame(Star):

@llm_tool(name="search_galgame_tool")
async def search_galgame_tool(self, event: AiocqhttpMessageEvent, game_name: str) -> MessageEventResult:
    """
    精确搜索Galgame游戏信息。

    Args:
        game_name(string): 需要搜索的游戏的准确名称。
    """
    logger.info(f"LLM tool 'search_galgame_tool' called with game_name: {game_name}")
    try:
        allinfo = await self._get_precise_search_data(game_name)
        return await self._format_and_create_result(event, allinfo)
    except Exception as e:
        logger.error(f"Error in search_galgame_tool: {type(e).__name__}:{e}")
        return event.plain_result(f"工具执行出错: {e}")
```

## 排查清单

如果您的函数工具没有在管理界面显示，请对照以下清单逐一排查：

1.  **[ ] 导入路径是否正确？**
    *   `llm_tool` 是否从 `astrbot.api.event.filter` 导入？

2.  **[ ] 装饰器是否正确？**
    *   是否使用了 `@llm_tool`？
    *   `@llm_tool` 是否**强制**带有 `name="your_tool_name"` 参数？

3.  **[ ] 函数签名是否正确？**
    *   函数是否为 `async def`？
    *   `event` 参数的类型注解是否为**具体**的事件类型（如 `AiocqhttpMessageEvent`），而不是通用的 `AstrMessageEvent`？
    *   函数的返回类型注解是否为 `-> MessageEventResult`？

4.  **[ ] 函数实现是否正确？**
    *   函数是否明确 `return` 一个 `MessageEventResult` 对象？

遵循以上所有要点，您就可以成功地为您的 AstrBot 插件添加强大的 LLM 函数工具了。