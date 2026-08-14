🎉 **DocTranslator Pro 版本现已发布！** 欢迎体验，功能更强大！

## ✨ Pro 版本核心优势

- **智能分块策略**: 能更好地识别段落、列表等结构，提升翻译质量与上下文连贯性。
- **成本优化**: 通过更高效的提示词设计和注入策略，显著减少 Token 消耗，有效降低翻译成本。
- **术语库**: 支持用户定义术语对照表，确保专业术语翻译的准确性和一致性。
- **翻译记忆库**: 智能复用历史翻译，提升效率、降低成本。
- **AI模型服务商管理**: 可配置 OpenAI, Qwen, DeepSeek 等多种大模型，用户可根据需求选择或由系统智能路由。
- **批量处理**: 支持文档上传选择多个术语库和翻译记忆，并发翻译，处理效率更高更准确。
- **消耗统计**: 提供Token消耗统计等管理后台功能。

[![Pro版在线体验](https://img.shields.io/badge/Pro%20版-在线体验-71a7f4?style=for-the-badge&logoColor=white)](https://pro.doctranslator.cn)  

---

# 📄 DocTranslator - 文档 AI 翻译工具 🚀

**DocTranslator** 文档翻译，支持多种文件格式的翻译，兼容 OpenAI 格式的 API，并支持批量操作和多线程处理。无论是个人用户还是企业团队，DocTranslator 都能帮助你高效完成文档翻译任务！✨

[[English]](README_en.md)

---


| 🌐 **在线体验**     | [立即访问](https://dc.starpms.cn/) |
|:--------------------:|:----------------------------------:|
| 📚 **官方文档**     | [查看文档](https://www.doctranslator.cn/)      |
| 👉 **推荐API中转站**    | [立即使用](https://www.ezworkapi.com)     |





[🔥GPT中转站推荐-低价优惠-点击此处跳转🔥](https://www.ezworkapi.com) 

---

## 🌟 功能特性

- **支持多种文档格式**  
  📑 **txt**、📝 **markdown**、📄 **word**、📊 **csv**、📈 **excel**、📑 **pdf(非扫描版)**、📽️ **ppt** 文档的 AI 翻译。
  
- **兼容 OpenAI 格式的 API**  
  🤖 支持任何符合 OpenAI 格式的端点 API（中转 API），灵活适配多种 AI 模型。

- **批量操作**  
  🚀 支持批量上传和翻译文档，提升工作效率。

- **多线程支持**  
  ⚡ 利用多线程技术，加速文档翻译过程。

- **Docker 部署**  
  🐳 支持 Docker 一键部署，简单易用。

---

## 🛠️ 技术栈

- **前端**：Vue 3 + Vite  
- **后端**：Python + Flask+MySQL/SQLite  
- **AI 翻译**：兼容 OpenAI 格式 
- **部署**：Docker + Nginx  

---

## 效果如图:
### 用户端页面演示
![用户端页面](docs/images/image1.png)
![用户端页面2](docs/images/image2.png)
![用户端页面3](docs/images/image.png)

### 管理端页面演示
![管理端页面](docs/images/image3.png)
![管理端页面2](docs/images/image4.png)
![管理端页面3](docs/images/image5.png)

## Linux 系统部署（推荐）

推荐在 Linux 系统中使用 Docker Engine。

### 首次部署：仅准备一次

```bash
git clone https://github.com/mingchen666/DocTranslator.git
cd DocTranslator
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，将 `FLASK_ENV` 设为 `production`，并填写真实的
`PROD_DATABASE_URL`、`SECRET_KEY` 和 `JWT_SECRET_KEY`。

### 一行部署

```bash
bash deploy.sh
```

脚本会校验部署配置、自动构建 `backend/Dockerfile`、执行数据库迁移，并按
`TRANSLATION_QUEUE_BACKEND` 启动 API、Nginx 和对应 worker。默认 `database` 启动
数据库队列 worker；`celery` 启动 Redis 及普通文档、PDF 两个 Celery worker。

### 一行更新

```bash
bash update.sh
```

更新脚本要求工作区干净，并且只接受 `main` 分支的快进更新，随后复用同一部署流程重建
后端镜像。已提交的 `frontend/dist` 和 `admin/dist` 会直接被 Nginx 使用，无需在服务器
构建前端。



<details>
<summary>Windows 部署</summary>

<br>

`deploy.sh` 和 `update.sh` 面向 Linux/macOS 的 Bash。Windows 用户可在 Docker Desktop
的 Linux containers 模式下，通过 PowerShell 在项目根目录执行：

```powershell
# 首次部署或默认数据库队列模式
docker compose up -d --build --force-recreate

# 日常更新
git pull --ff-only; if ($LASTEXITCODE -eq 0) { docker compose up -d --build --force-recreate } else { exit $LASTEXITCODE }
```

该方式同样自动构建后端镜像，并直接使用已提交的 `frontend/dist` 与 `admin/dist`。
Celery 模式使用 `docker compose --profile celery up -d --build --force-recreate`。

</details>

## 🚀 本地开发

### 1. 克隆项目

```bash
git clone https://github.com/mingchen666/DocTranslator.git
cd DocTranslator
```

### 2. 配置环境变量

在 `backend/.env` 文件中填写必要的环境变量


### 3. 启动后端

进入后端目录安装依赖：

```bash
cd backend
pip install -r requirements.txt
```

### 4. 启动后端

```bash
python run.py
```

`python run.py` 会先执行 Alembic 数据库迁移和幂等初始化，再启动开发服务器。
也可以单独运行 `python migrate_startup.py` 只执行迁移。生产数据库升级前必须先备份。

### 5. 启动前端和管理端
> **/dist 文件夹已经是打包好了的，直接部署使用即可，不本地开发可以忽略下面步骤**
>

*前端*

```bash
cd frontend
pnpm install
pnpm dev
```

*管理端*

```bash
cd admin
pnpm install
pnpm dev
```


### 6. 访问项目

- **前端**：http://localhost:1475  
- **管理端**：http://localhost:8081  
- **后端 API**：http://localhost:5000  

---


<details>
<summary>其他部署方式：Docker Compose、Celery、对象存储和独立容器</summary>

<br>

### Docker Compose 部署

生产环境优先使用上方 `deploy.sh`。旧版只启动 API 和 Nginx 的手工命令不会启动
翻译队列 worker，不能用于当前版本。需要手工管理容器时，请使用本节末尾的完整示例。

新数据库不会创建默认管理员。首次启动前可在 `backend/.env` 同时配置
`ADMIN_EMAIL` 和 `ADMIN_PASSWORD`；创建成功后应移除 `ADMIN_PASSWORD`。

#### 启动项目
```shell
cd DocTranslator
docker compose up -d --build --force-recreate
```

Docker Compose 从 `backend/.env` 读取数据库和密钥配置，并在启动服务前同步完成迁移。

默认 `TRANSLATION_QUEUE_BACKEND=database`，只运行数据库 worker，不需要 Redis。
需要 Celery + Redis 时，在 `backend/.env` 设置：

```env
TRANSLATION_QUEUE_BACKEND=celery
CELERY_BROKER_URL=redis://redis:6379/0
```

然后使用 Celery profile：

```shell
docker compose --profile celery up -d --build --force-recreate
```

#### 翻译结果对象存储

默认情况下，翻译结果继续保存在 `/app/storage`。如需把新完成的结果保存到
阿里云 OSS，可在 `backend/.env` 设置：

```env
RESULT_STORAGE_BACKEND=oss
OSS_ENDPOINT=https://oss-cn-hangzhou.aliyuncs.com
OSS_BUCKET=your-private-bucket
OSS_ACCESS_KEY_ID=your-access-key-id
OSS_ACCESS_KEY_SECRET=your-access-key-secret
OSS_PREFIX=translations/
```


历史本地结果不会自动迁移；每条记录仍从它完成时使用的存储后端读取。
`/app/storage` 挂载仍然必须保留，用于源文件、翻译临时文件和历史结果。

#### 独立 Docker 容器

不使用 Compose 时，所有容器使用同一个镜像、同一个 `.env`、同一个数据库和
`/app/storage` 挂载。

先构建镜像并创建网络：

```shell
docker build -t doctranslator ./backend
docker network create my-network
```

数据库队列模式：

```shell
docker run -d --name backend-container --env-file backend/.env \
  --network my-network -p 5000:5000 \
  -v $(pwd)/backend/db:/app/db \
  -v $(pwd)/backend/storage:/app/storage doctranslator

docker run -d --name backend-worker-container --env-file backend/.env \
  --network my-network \
  -v $(pwd)/backend/db:/app/db \
  -v $(pwd)/backend/storage:/app/storage \
  doctranslator python worker.py
```

Celery 模式额外启动 Redis 和两个 Celery worker：

```shell
docker run -d --name redis --network my-network \
  redis:7-alpine redis-server --appendonly yes

docker run -d --name celery-document-worker --env-file backend/.env \
  --network my-network \
  -v $(pwd)/backend/db:/app/db \
  -v $(pwd)/backend/storage:/app/storage \
  doctranslator celery -A app.celery_app:celery worker \
  --queues=translation.default --concurrency=2

docker run -d --name celery-pdf-worker --env-file backend/.env \
  --network my-network \
  -v $(pwd)/backend/db:/app/db \
  -v $(pwd)/backend/storage:/app/storage \
  doctranslator celery -A app.celery_app:celery worker \
  --queues=translation.pdf --concurrency=1
```

独立容器部署在多台主机时，`/app/storage` 必须使用共享文件系统；普通本地 Docker
volume 不能跨主机共享翻译源文件和结果文件。

#### 更新项目
```shell
cd /DocTranslator
git pull --ff-only && docker compose up -d --build --force-recreate
```

</details>

## 我的其他项目

- [Reviva](https://github.com/mingchen666/Reviva) - AI 学习工作台

## 💖 赞赏支持

维护此项目需要耗费大量精力，如果DocTranslator对你有帮助，欢迎赞赏支持！你的支持是我持续开发的动力！😊  
<img src="docs/e652698b250efb6e5151b084bd08814.jpg" alt="赞赏码" width="300">
---

## 📢 交流群
有任何问题想交流，欢迎加入我们的交流群
<img src="docs/images/qq-group.png" alt="交流群" width="300">


## 🤝 贡献指南

欢迎贡献代码！

---

## 📜 许可

[Apache-2.0 license](LICENSE)

---



## 📞 联系我

如有任何问题或建议，请联系我：  
---

## 👋 关于我

在读生一枚，有点喜欢前端，喜欢探索AI应用和工具开发
🎉 感谢大家的支持！欢迎 Star ⭐️ 和 Fork 🍴，一起完善 DocTranslator！


## 📌 说明

本项目基于 [ezwork](https://github.com/EHEWON/ezwork-ai-doc-translation) 进行重构优化，感谢原作者的贡献！🙏

## 🙏 感谢

  [BabelDOC](https://github.com/funstory-ai/BabelDOC)

[![Star History](https://api.star-history.com/svg?repos=mingchen666/DocTranslator&type=Date)](https://star-history.com/#mingchen666/DocTranslator)gen
