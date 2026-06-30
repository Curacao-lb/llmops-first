import math
from dataclasses import dataclass
from typing import Any

from flask_wtf import FlaskForm
from wtforms import IntegerField
from wtforms.validators import Optional, NumberRange

from pkg.sqlalchemy import SQLAlchemy


class PaginatorReq(FlaskForm):
    """分页请求基础类,涵盖当前页数、每页条数,如果接口请求需要携带分页信息,可直接继承该类"""

    current_page = IntegerField(
        "current_page",
        default=1,
        validators=[
            Optional(),
            NumberRange(min=1, max=9999, message="分页范围在1-9999"),
        ],
    )
    page_size = IntegerField(
        "page_size",
        default=20,
        validators=[
            Optional(),
            NumberRange(min=1, max=50, message="每页数据条数在在1-50"),
        ],
    )


@dataclass
class Paginator:
    """分页器"""

    total_page: int = 0  # 总页数
    total_record: int = 0  # 总条数
    current_page: int = 1  # 当前页数
    page_size: int = 20  # 每页条数

    def __init__(self, db: SQLAlchemy, req: PaginatorReq = None):
        if req is not None:
            self.current_page = req.current_page.data
            self.page_size = req.page_size.data
        self.db = db

    def paginate(self, select) -> list[Any]:
        if hasattr(select, "statement"):
            select = select.statement
        p = self.db.paginate(
            select, page=self.current_page, per_page=self.page_size, error_out=False
        )
        self.total_record = p.total
        self.total_page = math.ceil(p.total / self.page_size)
        return p.items


@dataclass
class PageModel:
    list: list[Any]
    paginator: Paginator
