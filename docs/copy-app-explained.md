# 复制应用接口（copy_app）简要说明

作用：把一个已有应用复制成一份全新的、草稿状态的独立副本，返回新应用的 id。

路由：`POST /apps/<app_id>/copy`，绑定到 `app_handler.copy_app`。

调用链路：

- Router：解析 `app_id`（UUID），转发给 Handler。
- Handler：`@login_required` 鉴权，调用 service，返回 `{"id": 新应用id}`。
- Service（核心）：完成实际复制。

Service 核心逻辑：

1. 校验权限并取出原应用及其草稿配置。
2. 把应用、草稿配置转成字典，剔除 `id`、关联 id、状态、时间戳、`_sa_instance_state` 等不能复制的字段。
3. 在同一事务里：新建应用（重新生成 id，状态设为草稿）→ 新建草稿配置并关联新应用 → 回写应用的 `draft_app_config_id`。
4. 返回新应用。

关键点：复制的是「应用 + 草稿配置」两条记录；剔除主键等字段保证副本完全独立；写入放在一个事务里，保证一致性。
