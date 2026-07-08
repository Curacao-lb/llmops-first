from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Optional, URL
from marshmallow import Schema, fields, pre_dump

from internal.model import App
from pkg.paginator import PaginatorReq
from internal.lib.helper import datetime_to_timestamp


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


class GetAppResp(Schema):
    """获取应用基础信息响应结构"""

    id = fields.UUID(dump_default="")
    debug_conversation_id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    en_name = fields.String(dump_default="")
    icon = fields.String(dump_default="")
    description = fields.String(dump_default="")
    status = fields.String(dump_default="")
    draft_updated_at = fields.Integer(dump_default=0)
    mode = fields.Integer(dump_default=0)
    updated_at = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: App, **kwargs):
        # draft_app_config 现在是纯读取属性，草稿不存在时会返回 None，
        # 因此这里做空值保护，避免序列化时报错。
        # 注意：确保草稿配置存在的「取不到就创建」逻辑应在 handler/service 中
        # 通过 AppService.get_draft_app_config() 显式完成。
        draft_app_config = data.draft_app_config
        return {
            "id": data.id,
            "debug_conversation_id": (
                data.debug_conversation_id if data.debug_conversation_id else ""
            ),
            "name": data.name,
            "en_name": data.en_name,
            "icon": data.icon,
            "description": data.description,
            "status": data.status,
            "draft_updated_at": (
                datetime_to_timestamp(draft_app_config.updated_at)
                if draft_app_config is not None
                else 0
            ),
            "updated_at": datetime_to_timestamp(data.updated_at),
            "created_at": datetime_to_timestamp(data.created_at),
            "mode": data.mode,
        }
