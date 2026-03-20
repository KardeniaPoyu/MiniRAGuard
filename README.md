# 青居智选（Qingju）

基于 API 与轻量级 RAG 的租房合同审查系统（微信小程序 + FastAPI）。

## 目标与边界

- **目标**：帮助在校大学生在签约前快速识别租房合同中的潜在法律风险条款，并支持基于审查结果的多轮追问。
- **边界**：不提供正式法律咨询，不替代律师意见；输出仅作辅助参考。

## API 契约（MVP 必须稳定）

### 1) 合同审查

- **POST** `/api/analyze`
- **请求**：`{ "images": [base64_p1, base64_p2, ...] }`
- **响应**：包含 `overall_risk / summary / analysis_results`
- **字段约束**：
  - `analysis_results[].risk_level`：仅允许「高风险 / 中风险 / 低风险」
  - `analysis_results[].legal_basis`：固定格式「《法规名称》第X条」
  - `analysis_results[].original_text`：用于前端合同全文字符串匹配高亮

### 2) 多轮对话

- **POST** `/api/chat`
- **请求**：`{ "question": "...", "context": {...}, "history": [{"role":"user|assistant","content":"..."}] }`
- **响应**：`{ "answer": "..." }`（自由文本）

## 部署与安装

- **服务器安装命令**：`pip install -r requirements.txt`
- **注意**：`torch` 不在依赖列表中，`sentence-transformers` 会自动安装适合 CPU 的依赖，无需手动指定。

## Git 协作约定（建议）

- **分支**：`main` 保持可部署/可演示；日常开发使用 `feat/*`、`fix/*` 等功能分支并通过 PR 合并。
- **提交信息**：Conventional Commits（例如 `feat: add analyze endpoint`）。
- **敏感信息**：`.env` 禁止入库（已在 `.gitignore` 忽略）。
- **运行产物**：`rent_agent_backend/cache.db`、`rent_agent_backend/vector_store/` 禁止入库（已忽略）。

## 上线前置条件（验收红线）

- 后端对外 **HTTPS**
- 使用 **已 ICP 备案域名** 并在微信公众平台配置为 `request` 合法域名

