"""数据库初始化脚本：执行 Alembic 迁移 + 确保 pgvector 向量表（PostgreSQL 扩展/表/HNSW 索引）。

用法（在项目根目录）：
    python scripts/init_db.py
"""
import asyncio
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))


def run_alembic() -> None:
    print("==> 执行 Alembic 数据库迁移…")
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        check=True,
    )
    print("    迁移完成")


async def ensure_vector_table() -> None:
    print("==> 检查 pgvector 向量表…")
    from app.rag import vector_store

    await vector_store.ensure_vector_table()
    print("    pgvector 向量表就绪")


if __name__ == "__main__":
    try:
        run_alembic()
    except subprocess.CalledProcessError as e:
        print(f"    [警告] Alembic 迁移失败：{e}", file=sys.stderr)
    try:
        asyncio.run(ensure_vector_table())
    except Exception as e:  # noqa: BLE001
        print(f"    [警告] pgvector 向量表初始化失败（请确认 PostgreSQL 已启动）：{e}", file=sys.stderr)
    print("初始化完成 ✅")
