from flask_wtf import FlaskForm
from marshmallow import Schema, fields, pre_dump
from wtforms import StringField
from wtforms.validators import DataRequired, Length, URL, Email

from internal.lib.helper import datetime_to_timestamp
from internal.model import Account


class GetCurrentUserResp(Schema):
    """获取当前登录账号信息响应"""

    id = fields.UUID(dump_default="")
    name = fields.String(dump_default="")
    email = fields.String(dump_default="")
    avatar = fields.String(dump_default="")
    last_login_at = fields.Integer(dump_default=0)
    last_login_ip = fields.String(dump_default="")
    created_at = fields.Integer(dump_default=0)

    """
    钩子方法名叫什么无所谓（process_data 只是自定义名字），起作用的是 @pre_dump 这个装饰器。
    """

    @pre_dump
    def process_data(self, data: Account, **kwargs):
        """处理数据方法"""

        return {
            "id": data.id,
            "name": data.name,
            "email": data.email,
            "avatar": data.avatar,
            "last_login_at": datetime_to_timestamp(data.last_login_at),
            "last_login_ip": data.last_login_ip,
            "created_at": datetime_to_timestamp(data.created_at),
        }


class UpdatePasswordReq(FlaskForm):
    """更新账号密码请求"""

    # 所以 req 这个对象里，业务字段只有一个：password。
    # 前端提交类似 password=xxxx 的字段后，会被自动绑定到 req.password 上。
    password = StringField(
        "password",
        validators=[
            DataRequired("登录密码不能为空"),
        ],
    )


class UpdateNameReq(FlaskForm):
    """更新账号名称请求"""

    name = StringField(
        "name",
        validators=[
            DataRequired("账号名字不能为空"),
            Length(min=3, max=30, message="账号名称长度在3-30位"),
        ],
    )


class UpdateAvatarReq(FlaskForm):
    """更新账号头像请求"""

    avatar = StringField(
        "avatar",
        validators=[
            DataRequired("账号头像不能为空"),
            URL("账号头像必须是URL图片地址"),
        ],
    )


class RegisterReq(FlaskForm):
    email = StringField(
        "email",
        validators=[
            DataRequired("邮箱不能为空"),
            Email("邮箱格式不正确"),
        ],
    )
    password = StringField(
        "password",
        validators=[
            DataRequired("密码不能为空"),
        ],
    )
    confirmPassword = StringField(
        "confirmPassword",
        validators=[
            DataRequired("确认密码不能为空"),
        ],
    )
    verificationCode = StringField(
        "verificationCode",
        validators=[
            DataRequired("验证码不能为空"),
        ],
    )


class SendVerificationCodeReq(FlaskForm):
    email = StringField(
        "email",
        validators=[
            DataRequired("邮箱不能为空"),
            Email("邮箱格式不正确"),
        ],
    )
