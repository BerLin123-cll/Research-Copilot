"""占位 pgvector.sqlalchemy.Vector：离线验证时无需真实 pgvector 也能完成模型定义。"""
from sqlalchemy.types import UserDefinedType


class Vector(UserDefinedType):
    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim

    def get_col_spec(self, **kw: object) -> str:
        return f"VECTOR({self.dim})" if self.dim else "VECTOR"
