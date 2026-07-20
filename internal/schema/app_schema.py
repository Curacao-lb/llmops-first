from urllib.parse import urlparse
from uuid import UUID

from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import URL, DataRequired, Length, Optional, ValidationError

from internal.model import App, AppConfigVersion
from internal.schema.schema import ListField
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
        # 通过 AppService.get_draft_app_config_in_get_app() 显式完成。
        draft_app_config = data.draft_app_config
        return {
            "id": data.id,
            "debug_conversation_id": (
                data.debug_conversation_id
                if data.debug_conversation_id is not None
                else ""
            ),
            "name": data.name,
            "en_name": data.en_name,
            "icon": data.icon,
            "description": data.description,
            "status": data.status,
            "draft_updated_at": (
                int(draft_app_config.updated_at.timestamp())
                if draft_app_config is not None
                else 0
            ),
            "updated_at": int(data.updated_at.timestamp()),
            "created_at": int(data.created_at.timestamp()),
            "mode": data.mode,
        }


class GetPublishHistoriesWithPageReq(PaginatorReq):
    """获取应用发布历史配置分页列表请求"""

    ...


class GetPublishHistoriesWithPageResp(Schema):
    """获取应用发布历史配置列表分页数据"""

    id = fields.UUID(dump_default="")
    version = fields.Integer(dump_default=0)
    created_at = fields.Integer(dump_default=0)

    @pre_dump
    def process_data(self, data: AppConfigVersion, **kwargs):
        return {
            "id": data.id,
            "version": data.version,
            "created_at": int(data.created_at.timestamp()),
        }


class FallbackHistoryToDraftReq(FlaskForm):
    """回退历史版本到草稿请求结构体"""

    app_config_version_id = StringField(
        "app_config_version_id", validators=[DataRequired("回退配置版本id不能为空")]
    )

    # 自动发现并执行 validate_<字段名> 方法的是 WTForms 的校验机制
    def validate_app_config_version_id(self, field: StringField) -> None:
        """校验回退配置版本id"""
        try:
            UUID(field.data)
        except Exception:
            raise ValidationError("回退配置版本id必须为UUID")  # noqa: B904


class UpdateDebugConversationSummaryReq(FlaskForm):
    """更新应用调试会话长期记忆请求体"""

    summary = StringField("summary", default="")


class DebugChatReq(FlaskForm):
    """应用调试会话请求结构体"""

    image_urls = ListField("image_urls", default=[])
    query = StringField(
        "query",
        validators=[
            DataRequired("用户提问query不能为空"),
        ],
    )

    def validate_image_urls(self, field: ListField) -> None:
        """校验传递的图片URL链接列表"""
        # 校验数据类型，如果不是列表则设置默认值为空列表
        if not isinstance(field.data, list):
            field.data = []

        # 校验数据的长度，最多不能超过5条URL记录
        if len(field.data) > 5:
            raise ValidationError("上传的文件数量不能超过5，请核实后重试")

        # 循环校验image_url是否为URL
        for image_url in field.data:
            result = urlparse(image_url)
            if not all([result.scheme, result.netloc]):
                raise ValidationError("上传的文件URL地址格式错误，请核实后重试")
