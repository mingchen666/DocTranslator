# 使用 Nginx 作为生产环境服务器
FROM nginx:stable-alpine

# 删除默认的 Nginx 配置
RUN rm -rf /etc/nginx/conf.d/default.conf

# 复制自定义的 Nginx 配置文件
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 将打包后的静态文件复制到 Nginx 的默认静态文件目录
COPY dist /usr/share/nginx/html

# 暴露自定义端口（例如 8080）
EXPOSE 8080

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
