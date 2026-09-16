# 应用默认配置项
DEFAULT_CONFIG = {
    # SQLAlchemy数据库配置
    "SQLALCHEMY_DATABASE_URI": "",
    "SQLALCHEMY_POOL_SIZE": 30,
    "SQLALCHEMY_POOL_RECYCLE": 3600,
    "SQLALCHEMY_ECHO": "True",
    # WTF的CSRF保护
    "WTF_CSRF_ENABLED": "FALSE",
    # 日志配置。不同服务请设置不同的 LOG_SERVICE_NAME，例如 web、worker。
    "LOG_DIR": "storage/logs",
    "LOG_SERVICE_NAME": "web",
    "LOG_LEVEL": "INFO",
    "LOG_BACKUP_COUNT": "30",
    "LOG_TO_CONSOLE": "FALSE",
}
