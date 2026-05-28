from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


# 定义方法和对应的请求名保持一致
class ValidateOpenAPISchema(FlaskForm):
    """校验OPENAPI规范字符串请求"""

    openapi_schema = StringField(
        "openapi_schema",
        validators=[DataRequired(message="openapi_schema字符串不能为空")],
    )
