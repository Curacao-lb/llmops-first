from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length

# 定义方法和对应的请求名保持一致
class CompletionReq(FlaskForm):
    """基础聊天接口请求验证"""
    # 验证规则：1.必填 2.长度最大为2000
    query = StringField('query', validators=[
      # 这里的 message 指的是如果数据不符合规则时，返回什么提示
      DataRequired(message="用户的提问是必填的"),
      Length(max=2000, message="用户的提问最大长度是2000")
    ])