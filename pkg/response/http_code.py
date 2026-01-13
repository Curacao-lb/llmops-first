# 类HttpCode,这个类它是一个字符串的枚举类型，用来记录我们的业务状态码
class HttpCode(str):
    """HTTP基础业务状态码"""

    SUCCESS = "success"  # 成功状态
    FAIL = "fail"  # 失败状态
    NOT_FOUND = "not_found"  # 未找到状态
    UNAUTHORIZED = "unauthorized"  # 未授权状态
    FORBIDDEN = "forbidden"  # 无权限状态
    VALIDATE_ERROR = "validate_error"  # 数据验证错误状态
