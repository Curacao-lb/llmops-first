from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Optional
from marshmallow import Schema, fields, pre_dump

from internal.model import App
from pkg.paginator import PaginatorReq


# 定义方法和对应的请求名保持一致
class CompletionReq(FlaskForm):
    """基础聊天接口请求验证"""

    # 验证规则：1.必填 2.长度最大为2000
    query = StringField(
        "query",
        validators=[
            # 这里的 message 指的是如果数据不符合规则时，返回什么提示
            DataRequired(message="用户的提问是必填的"),
            Length(max=2000, message="用户的提问最大长度是2000"),
        ],
    )


class GetAppsWithPageReq(PaginatorReq):
    """获取应用分页列表请求"""

    search_word = StringField("search_word", validators=[Optional()])
    status = StringField("status", validators=[Optional()])


class GetAppsWithPageResp(Schema):
    """获取应用分页列表数据响应"""

    id = fields.UUID()
    name = fields.String()
    icon = fields.String()
    description = fields.String()
    status = fields.String()
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: App, **kwargs):
        return {
            "id": data.id,
            "name": data.name,
            "icon": data.icon,
            "description": data.description,
            "status": data.status,
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
        }
