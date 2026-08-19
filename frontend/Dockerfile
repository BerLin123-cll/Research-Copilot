# 智研助手前端镜像：Node 构建 → Nginx 托管
# ---------- 构建阶段 ----------
FROM node:20-alpine AS build

WORKDIR /app

# 优先利用 Docker 层缓存安装依赖；国内使用 npmmirror 镜像加速
COPY package.json package-lock.json* ./
RUN npm install --registry=https://registry.npmmirror.com

COPY . .
RUN npm run build

# ---------- 运行阶段 ----------
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
