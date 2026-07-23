# Translation Result Object Storage Design

## 1. Goal

为翻译结果文件增加部署级、可选的对象存储能力。默认继续使用本地存储；部署管理员可在 `backend/.env` 中将结果存储切换为阿里云 OSS。源文件、翻译过程和各文档处理器仍使用本地文件路径。

首期只实现 `local` 和 `oss` 两个结果存储适配器。接口保持供应商无关，为后续增加 S3、MinIO 或 COS 留出扩展点，但本期不实现这些供应商。

## 2. Scope

包含：

- 单文件、普通多文件批次、ZIP 批次和 MCP 翻译结果的持久化。
- 用户端、管理端、MCP 的单文件和批量下载。
- 用户端、管理端、MCP 删除结果文件时调用对应存储适配器。
- OSS 配置校验、数据库迁移、旧记录兼容和自动化测试。

不包含：

- 将用户上传的源文件存入 OSS。
- 每个终端用户分别配置 Bucket 或访问凭据。
- 在前端或管理端增加对象存储配置页面。
- 自动把历史本地结果迁移到 OSS。
- 公开 Bucket、永久公开 URL 或客户端直接提交对象 key。

## 3. Architecture

新增独立的结果存储服务，业务代码只通过统一接口保存、读取、判断和删除翻译结果。文档翻译器始终把结果写入本地目标路径；翻译核心成功后，由任务完成阶段执行结果持久化。

```text
本地源文件
    -> 翻译器生成本地结果
    -> ResultStorage.finalize_result()
       -> local: 保留本地结果
       -> oss: 上传私有 Bucket，记录对象 key，清理本地临时结果
    -> 持久化成功后任务才进入 done
```

不得让 Word、Excel、PPTX、PDF、Doc2X 或批量处理器直接依赖 OSS SDK。这样可以保留现有文件处理代码，并把对象存储影响限制在任务完成、下载和删除边界。

## 4. Configuration

`backend/.env` 和 `backend/.env.example` 增加：

```env
# local（默认）或 oss；只控制翻译结果文件
RESULT_STORAGE_BACKEND=local

OSS_ENDPOINT=
OSS_BUCKET=
OSS_ACCESS_KEY_ID=
OSS_ACCESS_KEY_SECRET=
OSS_PREFIX=translations/
```

当 `RESULT_STORAGE_BACKEND=local` 时，不加载或校验 OSS 凭据。当配置为 `oss` 时，启动阶段必须校验 endpoint、bucket、access key id 和 access key secret；缺失配置直接阻止服务启动，不能静默退回本地。

`OSS_PREFIX` 必须被规范化为不以 `/` 开头、以 `/` 结尾的相对前缀，并拒绝 `..`、反斜杠和控制字符。首期下载统一由后端流式返回，不增加未使用的签名 URL 配置。

## 5. Object Key

对象 key 不包含 `customer_id`、邮箱、用户名或其他用户标识。推荐格式：

```text
translations/YYYY/MM/DD/{task_uuid}/{safe_filename}
```

`task_uuid` 使用现有翻译任务 UUID；若旧记录没有 UUID，则服务端生成新的随机 UUID 并持久化后再构造 key。`safe_filename` 使用现有文件名安全工具处理，只保留显示文件名和正确扩展名。对象 key 完全由服务端生成，API、MCP 和客户端都不能传入或覆盖。

同一任务重试使用同一个 key，上传成功时覆盖旧结果；不同任务由 UUID 隔离，不依赖文件名避免冲突。

`customer_id` 只用于数据库中的文件归属和下载权限查询，不写入对象 key、OSS metadata 或返回给 OSS 的文件名。

## 6. Data Model

`translate` 表增加：

- `target_storage_backend`：字符串，非空，默认 `local`，允许 `local`、`oss`。
- `target_storage_key`：字符串，可空；OSS 结果保存对象 key，本地结果保持为空。

继续保留：

- `origin_filepath`：本地源文件路径，语义不变。
- `target_filepath`：本地结果或翻译过程中的本地临时结果路径。
- `target_filesize`：结果文件字节数，适用于本地和 OSS。

Alembic migration 为所有历史记录填充 `target_storage_backend='local'`。旧记录不做文件搬迁，即使当前部署已切换到 OSS，也仍按记录自身的 backend 从本地读取。部署后新完成的任务使用当前配置的结果存储后端。

不要仅根据当前环境变量判断历史记录位置；数据库字段是每条结果的存储位置来源。

## 7. Storage Interface

在后端新增结果存储模块，接口至少包含：

```python
class ResultStorage:
    backend_name: str

    def put_file(self, local_path, object_key, content_type=None): ...
    def open_reader(self, record): ...
    def exists(self, record): ...
    def delete(self, record): ...
```

`LocalResultStorage` 使用 `target_filepath`，不得改变当前目录结构和下载行为。`OssResultStorage` 使用 `target_storage_key`，通过官方 `oss2` SDK 访问私有 Bucket。业务资源层不得直接导入 OSS SDK。

读取接口必须返回可流式读取或可作为临时文件管理的上下文对象，确保单文件下载、ZIP 归档和 MCP Base64 下载共用同一套实现，并在结束后关闭网络流和临时文件。

## 8. Translation Completion Flow

任务完成顺序固定为：

1. 翻译器成功生成本地结果文件。
2. 校验结果文件存在并记录 `target_filesize`。
3. 根据当前 `RESULT_STORAGE_BACKEND` 选择适配器。
4. `local` 模式保留文件，并设置记录 backend 为 `local`。
5. `oss` 模式生成对象 key、上传文件，并通过 SDK 确认上传成功。
6. 保存 `target_storage_backend`、`target_storage_key` 和结果大小。
7. 只有存储信息提交成功后，任务状态才更新为 `done`。
8. OSS 模式在数据库提交成功后尽力删除本地结果临时文件；清理失败只记录警告，不改变已完成状态。

OSS 上传失败时，任务进入 `failed`，`failed_reason` 使用可操作但不泄露凭据的错误信息。本地结果暂时保留，允许任务重试或管理员排查。不得在日志、API 响应或任务错误中输出 access key secret、签名 URL 或完整请求头。

若 OSS 上传成功但数据库提交失败，立即尽力删除刚上传的对象并将任务标记失败。对象删除失败需要记录对象 key 和任务 ID 供运维清理，但不能把凭据写入日志。

## 9. Download Flow

所有下载先执行现有权限检查，再读取存储：

- 用户接口继续按 `id + JWT customer_id + deleted_flag='N'` 查询。
- 批次接口继续按 `batch_id + JWT customer_id` 查询。
- 管理端接口继续要求 `admin_required`。
- MCP 接口继续使用 MCP key 解析出的用户或管理员身份。

权限通过后，根据记录的 `target_storage_backend` 选择适配器。Local 使用现有文件响应；OSS 由后端流式读取并返回原始显示文件名。首期不把永久 OSS URL 返回给客户端，也不让对象 key 代替业务文件 ID。

批量 ZIP 下载逐个通过适配器读取成功结果，写入 `SpooledTemporaryFile`。ZIP 内文件名继续使用 `origin_filename` 或 `batch_relative_path`，对象 key 不进入 ZIP。单个对象读取失败时，批次下载返回明确错误，不返回伪装成功的空文件。

## 10. Delete and Quota

删除使用数据库记录定位存储对象：

- Local 删除 `target_filepath` 指向的结果文件。
- OSS 删除 `target_storage_key` 指向的对象。
- 删除操作必须幂等；对象已经不存在时仍视为删除成功。
- 存储删除成功后再执行现有软删除或物理删除流程。
- 用户存储配额只按现有规则扣减一次，不因重复请求或对象不存在重复扣减。

管理员删除接口也必须同步修正存储配额，避免结果已经删除但用户存储仍被占用。源文件仍按现有本地文件策略处理，本设计不改变源文件生命周期。

## 11. Security

- OSS Bucket 必须为私有，服务端凭据只保存在环境变量或部署平台密钥系统中。
- 推荐使用只允许指定 Bucket 和 `OSS_PREFIX` 下读、写、删的最小权限 RAM 用户。
- Bucket endpoint 只能来自部署配置，客户端不能指定 endpoint、bucket 或对象 key。
- 对象 key 不包含 `customer_id` 或其他用户身份信息。
- 下载权限由数据库记录和身份令牌决定，不能依赖对象 key 的不可猜测性。
- 文件名、Content-Disposition 和 ZIP 相对路径继续使用现有安全校验。

## 12. Compatibility and Rollout

默认配置为 `RESULT_STORAGE_BACKEND=local`，未配置 OSS 的现有部署行为不变。切换到 OSS 后：

- 历史本地结果继续从本地下载。
- 新完成的翻译结果写入 OSS。
- 切回 local 只影响之后完成的任务，已有 OSS 结果仍从 OSS 下载。
- Docker 的 `/app/storage` 挂载继续保留，因为源文件、翻译临时文件和历史结果仍依赖本地存储。

部署文档必须说明 OSS 网络、权限、费用和生命周期策略。由于下载经过后端流式返回，首期不要求浏览器直接访问 OSS，也不需要配置 Bucket CORS。

## 13. Testing

至少覆盖：

- 默认 local 配置和现有下载行为不回归。
- OSS 配置缺失或 prefix 非法会阻止启动。
- 使用 fake storage 验证普通、PDF、批量和 MCP 任务在结果上传成功后才进入 `done`。
- OSS 上传失败时任务进入 `failed`，且不会写入虚假的 storage key。
- 历史 `local` 记录在当前部署为 OSS 时仍从本地读取。
- OSS 记录在部署切回 local 后仍通过 OSS 适配器读取。
- 普通用户不能下载其他用户的本地或 OSS 文件。
- 管理员、MCP、单文件、下载全部和批量 ZIP 均通过统一适配器。
- 删除幂等、重复请求不重复扣减配额。
- 对象 key 不包含 customer ID，并拒绝路径穿越。
- 上传成功但数据库提交失败时会尝试清理对象。

验证命令沿用项目要求：

```bash
cd backend
python -m compileall -q app worker.py celery_worker.py
python -m unittest discover -s tests -v
```

另外增加针对存储工厂、Local 适配器和 fake OSS 适配器的单元测试。OSS 真环境测试作为部署验收项，不要求在默认 CI 中访问外部网络。

## 14. Implementation Boundaries

本期只修改结果存储相关边界、必要的下载/删除调用点、模型迁移和配置文档。不要顺带重构所有文件工具，不把源文件迁入 OSS，也不引入新的后台同步服务。对象存储实现必须同时兼容数据库队列 worker 和 Celery worker。
