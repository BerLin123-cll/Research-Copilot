# 智研助手后端镜像（生产）
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# fastembed/onnxruntime 运行时依赖（slim 镜像默认缺少 libgomp）
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖（利用 Docker 层缓存；国内镜像源：阿里云为主、清华兜底，超时/重试增强稳定性）
# 如镜像源不可达导致 "No matching distribution found"，可在构建时传 --build-arg PIP_INDEX_URL=其它源
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ARG PIP_EXTRA_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
COPY requirements.txt .
RUN pip install --no-cache-dir \
    -i ${PIP_INDEX_URL} \
    --extra-index-url ${PIP_EXTRA_INDEX_URL} \
    --timeout 60 --retries 5 \
    -r requirements.txt

# 拷贝应用代码
COPY . .

# 预下载本地开源嵌入模型（默认 BAAI/bge-small-zh-v1.5 约 100MB；效果优先可换 intfloat/multilingual-e5-large 约 2GB）
# 模型名由构建参数 EMBEDDING_MODEL 传入（docker-compose 自动读取 .env 中的 EMBEDDING_MODEL）
# 国内网络：HF_ENDPOINT 走 hf-mirror.com；HF_HUB_DISABLE_XET=1 关闭 Xet 走普通 HTTP（镜像更兼容）
# 如需跳过预下载（构建完成后首次使用知识库时再下载），构建时传 --build-arg PRELOAD_MODEL=false
ARG EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
ARG PRELOAD_MODEL=true
ENV HF_ENDPOINT=https://hf-mirror.com \
    HF_HUB_DISABLE_XET=1
RUN if [ "$PRELOAD_MODEL" = "true" ]; then \
      for i in 1 2 3; do \
        python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='$EMBEDDING_MODEL')" && exit 0; \
        echo "==> 嵌入模型下载失败（第 $i 次），5 秒后重试…"; sleep 5; \
      done; \
      echo "==> 嵌入模型预下载失败，请检查网络；或改用 --build-arg PRELOAD_MODEL=false 跳过（首次使用时再下载）"; \
      exit 1; \
    fi

EXPOSE 8000

# 启动前执行数据库迁移（自动创建 pgvector 扩展 + 表 + HNSW 索引），再启动服务
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
