import os
import sys
from pathlib import Path

# 获取当前插件目录的绝对路径
PLUGIN_DIR = Path(__file__).parent.absolute()

# 定义表情包文件夹路径 - 避免使用相对路径如 ../..
# 直接使用绝对路径，或者相对于插件目录的路径
MEMES_BASE_DIR = Path(os.path.join(PLUGIN_DIR, "..", "..", "memes_data")).resolve()
MEMES_DIR = MEMES_BASE_DIR / "memes"

# 确保目录存在
os.makedirs(MEMES_DIR, exist_ok=True)

# 添加日志输出帮助调试
print(f"插件目录: {PLUGIN_DIR}", file=sys.stderr)
print(f"表情包基础目录: {MEMES_BASE_DIR}", file=sys.stderr)

# 获取当前文件所在目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 基础路径配置
BASE_DATA_DIR = os.path.join(CURRENT_DIR, "../../memes_data")
MEMES_DATA_PATH_DEFAULT = os.path.join(BASE_DATA_DIR, "memes_data_default.json")  # 默认类别描述数据文件路径
TEMP_DIR = os.path.join(CURRENT_DIR, "../../temp")

# 默认的类别描述
DEFAULT_CATEGORY_DESCRIPTIONS = {
    "angry": "当对话包含抱怨、批评或激烈反对时使用（如用户投诉/观点反驳）",
    "happy": "用于成功确认、积极反馈或庆祝场景（问题解决/获得成就）",
    "sad": "表达伤心, 歉意、遗憾或安慰场景（遇到挫折/传达坏消息）",
    "surprised": "响应超出预期的信息（重大发现/意外转折）注意：轻微惊讶慎用",
    "confused": "请求澄清或表达理解障碍时（概念模糊/逻辑矛盾）或对于用户的请求感到困惑",
    "color": "社交场景中的暧昧表达（调情）使用频率≤1次/对话", 
    "cpu": "技术讨论中表示思维卡顿（复杂问题/需要加载时间）",
    "fool": "自嘲或缓和气氛的幽默场景（小失误/无伤大雅的玩笑）",
    "givemoney": "涉及报酬讨论时使用（服务付费/奖励机制）需配合明确金额",
    "like": "表达对事物或观点的喜爱（美食/艺术/优秀方案）",
    "see": "表示偷瞄或持续关注（监控进度/观察变化）常与时间词搭配",
    "shy": "涉及隐私话题或收到赞美时（个人故事/外貌评价）", 
    "work": "工作流程相关场景（任务分配/进度汇报）",
    "reply": "等待用户反馈时（提问后/需要确认）最长间隔30分钟",
    "meow": "卖萌或萌系互动场景（宠物话题/安抚情绪）慎用于正式场合",
    "baka": "轻微责备或吐槽（低级错误/可爱型抱怨）禁用程度：友善级",
    "morning": "早安问候专用（UTC时间6:00-10:00）跨时区需换算",
    "sleep": "涉及作息场景（熬夜/疲劳/休息建议）",
    "sigh": "表达无奈, 无语或感慨（重复问题/历史遗留难题）"
}