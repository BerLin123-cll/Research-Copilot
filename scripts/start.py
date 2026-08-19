"""智研助手一键启动脚本（无需任何预先准备，只需已安装 Python 与 Node.js）。

用法：
    python scripts/start.py                # 同时启动后端(8000)与前端(5173)
    python scripts/start.py --backend-only # 只启动后端
    python scripts/start.py --frontend-only
    python scripts/start.py --pip-index https://pypi.tuna.tsinghua.edu.cn/simple   # 国内加速

首次运行会自动：
1. 复制 .env.example 为 .env（若不存在）
2. 创建后端虚拟环境 .venv 并安装依赖（较慢，仅一次；中断后重跑会断点续传）
3. 前端 node_modules 缺失时执行 npm install（较慢，仅一次）

启动后打开 http://localhost:5173 即可使用。
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
BACKEND_PORT = 8000
FRONTEND_PORT = 5173


def step(msg: str) -> None:
    print(f"\n==> {msg}")


def _run(cmd: list[str], cwd: str | None = None) -> None:
    """运行子进程；Ctrl+C 中断时给出友好提示（不视为报错）。"""
    try:
        subprocess.run(cmd, cwd=cwd, check=True)
    except KeyboardInterrupt:
        print("\n已取消。直接重新运行本脚本即可继续，已下载完成的包不会重复下载。")
        sys.exit(130)


def ensure_env_file() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        shutil.copy(ROOT / ".env.example", env_path)
        step("已创建 .env（请编辑填入 LLM_API_KEY，否则研究任务会因 LLM 调用失败）")
    else:
        step(".env 已存在，跳过")


def ensure_backend_env(pip_index: str) -> Path:
    venv = BACKEND / ".venv"
    py = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    if not py.exists():
        step("创建后端虚拟环境 .venv …")
        _run([sys.executable, "-m", "venv", str(venv)])
    marker = BACKEND / ".deps_installed"
    if not marker.exists():
        step("安装后端依赖（首次较慢，请耐心等待；中断后重跑会从断点继续）…")
        cmd = [str(py), "-m", "pip", "install", "--timeout", "60", "-r", str(BACKEND / "requirements.txt")]
        if pip_index:
            cmd += ["-i", pip_index]
        _run(cmd)
        marker.touch()
    else:
        step("后端依赖已安装，跳过")
    return py


def ensure_frontend(npm_registry: str) -> None:
    if not (FRONTEND / "node_modules").exists():
        step("安装前端依赖（首次较慢）…")
        cmd = ["npm", "install"]
        if npm_registry:
            cmd += ["--registry", npm_registry]
        _run(cmd, cwd=str(FRONTEND))
    else:
        step("前端依赖已安装，跳过")


def run_backend(py: Path) -> subprocess.Popen:
    step(f"启动后端 http://localhost:{BACKEND_PORT}（首次会自动下载嵌入模型约100MB）…")
    return subprocess.Popen(
        [str(py), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1",
         "--port", str(BACKEND_PORT), "--reload"],
        cwd=str(BACKEND),
    )


def run_frontend() -> subprocess.Popen:
    step(f"启动前端 http://localhost:{FRONTEND_PORT} …")
    return subprocess.Popen(
        ["npm", "run", "dev"], cwd=str(FRONTEND),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="智研助手一键启动")
    parser.add_argument("--pip-index", help="PyPI 镜像源（国内加速示例：https://pypi.tuna.tsinghua.edu.cn/simple）")
    parser.add_argument("--npm-registry", help="npm 镜像源（国内加速示例：https://registry.npmmirror.com）")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--backend-only", action="store_true")
    group.add_argument("--frontend-only", action="store_true")
    args = parser.parse_args()

    # 优先命令行参数，其次环境变量，最后官方源
    pip_index = args.pip_index or os.environ.get("PIP_INDEX_URL") or ""
    npm_registry = args.npm_registry or os.environ.get("NPM_REGISTRY") or ""

    ensure_env_file()
    procs: list[subprocess.Popen] = []

    if not args.frontend_only:
        py = ensure_backend_env(pip_index)
        procs.append(run_backend(py))
    if not args.backend_only:
        ensure_frontend(npm_registry)
        procs.append(run_frontend())

    if args.backend_only:
        step(f"后端已启动：http://localhost:{BACKEND_PORT}   API 文档：http://localhost:{BACKEND_PORT}/docs")
        step("按 Ctrl+C 停止")
    elif args.frontend_only:
        step(f"前端已启动：http://localhost:{FRONTEND_PORT}")
    else:
        step(f"全部启动完成！浏览器打开 http://localhost:{FRONTEND_PORT}")
        step("提示：后端 .env 中 LLM_API_KEY 未填时，研究任务会失败；Embedding/向量库均为本地开源，无需配置")

    try:
        for p in procs:
            p.wait()
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()
        print("\n已停止")


if __name__ == "__main__":
    main()
