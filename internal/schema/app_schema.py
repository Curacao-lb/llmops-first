from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Optional, URL
from marshmallow import Schema, fields, pre_dump

from internal.model import App
from pkg.paginator import PaginatorReq


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


class CreateAppReq(FlaskForm):
    """创建Agent应用请求结构体"""

    name = StringField(
        "name",
        validators=[
            DataRequired("应用名称不能为空"),
            Length(max=40, message="应用名称长度最大不能超过40个字符"),
        ],
    )
    en_name = StringField(
        "en_name",
        validators=[
            DataRequired("应用英文名称不能为空"),
            Length(max=40, message="应用英文名称长度最大不能超过40个字符"),
        ],
    )
    icon = StringField(
        "icon",
        validators=[
            DataRequired("应用图标不能为空"),
            URL(message="应用图标必须是图片URL链接"),
        ],
    )
    description = StringField(
        "description",
        validators=[Length(max=800, message="应用描述的长度不能超过800个字符")],
    )
