# 06 代码审查记录（2026-10-29）

范围：本地 `2f52b0a` 加当前未提交改动，重点审查跨请求幂等、确认边界、任务完成状态与保存失败；同时检查相关原有路径。按 [需求](01-requirements.md) 与 [方案](02-solution.md) 核对，未将已有文档的自述当作验收通过证据。审查与复现执行者为 Codex。

结论：已确认 **3 个 P1、1 个 P2**。现有测试全绿，但上述核心契约仍有遗漏。本轮只补文档和 review，未修改生产代码，以下问题均为待修复。

| 优先级 | 编号 | 代码位置（当前工作树行号） | 影响 | 来源 |
|---|---|---|---|---|
| P1 | R1 | `src/scheduler_agent/guard.py:89–95,155–156` | 跨请求结果可以虚构确认状态与渠道 | 新增跨请求路径 |
| P1 | R2 | `src/scheduler_agent/guard.py:131–141` | 审核阻断仍可能报完成 | 本轮完成状态改动 |
| P1 | R3 | `src/scheduler_agent/tools.py:265,282–290` | 实际落盘失败导致循环崩溃，不能返回失败报告 | 原有路径；并非由当前 diff 引入 |
| P2 | R4 | `src/scheduler_agent/store.py:19,92–94`；`domain.py:56–60` | 原请求元数据过期，跨请求判定产生错误待确认 | 原有哈希与新增跨请求比较的组合 |

## R1 · P1：跨请求结果必须核对草稿的确认状态和渠道

已有 REQ-A 将 M07 从要求的 19:00 改到 20:00，以 `pending` 保存，且没有任何用户确认。REQ-B 提交相同要求后，模型在 finish 中填写 `confirmation_status=confirmed`、`suggested_channel=xiaohongshu`、`suggested_slot=20:00`、`in_draft=false`。

**实际**：`validate_finish` 返回空 issues；报告使用模型提供的 `confirmed` 和小红书渠道，但真实草稿仍是抖音、`pending`。整体状态仍为 `needs_confirmation`，并不能抵消条目里虚构确认事实的问题；没有发生真实发布或草稿状态修改。

**原因**：本次成功保存的分支会核对时段、渠道及确认状态，`in_other_draft` 分支只核对时段和是否需要说明；`build_report` 随后直接采纳模型的渠道、确认状态。

**建议**：对已有草稿也使用统一的事实核对；确认状态和渠道从存储读取，不允许模型将 pending 升级为 confirmed。新的确认应通过原请求的显式更新流程落盘。

**回归验收**：其他草稿为 pending 时，伪造 confirmed/not_required 或不同渠道的 finish 均须被退回；合法的 pending 结果必须携带待确认项；原请求经真实确认更新后仍可正确引用。

## R2 · P1：完成状态必须考虑当前复检结果

REQ-A 把 M07 按 19:00 保存为 `not_required`。之后素材文案改成含“100% 最有效”，REQ-B 以相同渠道和时间重提。本轮在隔离上下文中修改素材副本，使用真实规则引擎和 `run_agent(..., MockModel())` 复现。

**实际**：当前审核为 `blocked`、草稿状态为 `in_other_draft`，但整体 `task_status=completed`。Mock 正确给出阻断结论，错误发生在账本汇总层。

**原因**：`done` 只看草稿和原请求是否一致、旧确认是否有效，未合并最近一次 `check_rules` 的结果。同一运行先保存通过、再复检阻断时，本次已保存分支也存在相同风险。

**建议**：完成判定同时要求当前审核有效、实际草稿满足要求、确认有效；审核变为 block/incomplete/review 时不得沿用旧完成状态。规格还应明确旧草稿变为不可用后的占位和重审策略。

**回归验收**：已有草稿后再遇到 block、incomplete、review，均不得 completed；同会话“保存后重新审核”也需覆盖；审核仍通过且要求一致的正常重复提交继续完成。

## R3 · P1：将真实 I/O 异常纳入保存失败契约

模拟 `DraftStore._write` 抛出 `OSError(28, "No space left on device")`，通过正常的 `dispatch(..., "save_schedule_draft", ...)` 调用保存。此处使用 mock 注入系统错误，没有填满磁盘或修改权限。

**实际**：异常直接传播，`save_attempts` 没有 `storage_failure`。Agent 循环不会生成正常的 `save_failed` 报告；单独尝试从账本构建报告，草稿也被记成 `rejected`。本次注入没有落盘文件。

**原因**：只有专门的 `save_fail` 注入分支标记存储失败；真实 `upsert` 没有 I/O 异常处理，而 dispatch 只捕获 TypeError。

**建议**：在保存边界捕获预期文件 I/O 异常，记录失败并返回结构化错误，保留此前成功保存的事实；是否 retryable 应区分错误原因。原子替换仅防止部分写入，不能替代失败报告。

**回归验收**：首次保存与更新旧草稿时分别注入临时文件写入失败、`os.replace` 失败，验证没有虚报、旧文件不被破坏、账本和报告正确表达失败。

## R4 · P2：参与跨请求判定的原请求字段必须同步落盘

REQ-A 要求 19:00，允许窗口 19:00–20:00，草稿实际安排 20:00、`not_required`。随后用相同 REQ-A 将硬性要求改为 20:00，仍保存 20:00、`not_required`。

**实际**：由于语义哈希没有变化，保存返回 `duplicate`，磁盘 `requested_slot` 仍为 19:00。REQ-B 再提交 20:00 时，`same_requirement` 认定要求不同，Mock 报 `needs_confirmation`，尽管已接受的新要求与实际排期一致。

**原因**：原请求字段原先不影响排期哈希，但现在又被用作跨请求判定依据；duplicate 提前返回阻止了其更新，当前运行账本与持久化数据可能不一致。

**建议**：把影响判定的请求字段加入版本判定，或单独、明确地更新请求元数据；同时在规格中约定原请求改变、实际排期不变时的修订语义。继续排除 note 等模型自由文本。

**回归验收**：覆盖同一请求“只改原要求、实际排期不变”再跨请求重提的完整链路；仍确保仅 note 措辞变化保持 duplicate。

## 已执行验证与边界

- 全量 pytest：47 passed。
- Mock：11/11 场景、103/103 检查通过。
- 历史模型记录重放：4 个参数化测试通过，覆盖 44 次历史场景运行；它们已包含在 47 个测试内。
- 定向复现：R1–R4 均复现。脚本中的 assert 确认的是当前缺陷存在，不能将脚本退出码 0 当作业务验收通过。
- 未调用真实模型 API；原有 Flash 记录未被覆盖。现有 11 场景与历史重放不能证明新增跨请求路径的模型决策质量。
- 未做完整安全审计；JSON 并发锁、跨渠道同素材分发等原文已声明的限制不重复列为新发现。

建议先修 R1–R3，再修 R4；每项先补回归用例。修复若改变工具返回或报告，历史重放失败应核对原因并更新证据，不能删除断言来保持全绿。

## 复现脚本与实际输出

将下方 Python 代码保存为 `/tmp/scheduler-review-repro.py`，在项目根目录执行：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python /tmp/scheduler-review-repro.py
```

脚本使用临时草稿目录，不读密钥、不请求外部 API、不修改源码或数据文件。

```python
"""Reproduce known review findings; assertions confirm defects, not acceptance.

Run from the repository with PYTHONPATH=src. No API calls or source changes.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from scheduler_agent.agent import run_agent
from scheduler_agent.evaluation import build_context
from scheduler_agent.guard import build_report, validate_finish
from scheduler_agent.mock_model import MockModel
from scheduler_agent.tools import check_rules, dispatch, save_schedule_draft


def ctx(path, key, at="2026-11-04T19:00", window=None):
    item = {"material_id": "M07", "channel": "douyin", "publish_at": at}
    if window:
        item["acceptable_window"] = window
    return build_context({"request_id": key, "items": [item]}, path)


def save(c, at="2026-11-04T19:00", status="not_required"):
    check_rules(c, "M07", at)
    result = save_schedule_draft(c, [{"material_id": "M07", "channel": "douyin", "slot": at,
                                    "confirmation_status": status, "note": "改期需用户确认"}])
    assert result["ok"], result
    return result


def reproduce(root):
    observed = {}

    path = root / "confirmation.json"
    first = ctx(path, "REQ-A")
    save(first, "2026-11-04T20:00", "pending")
    second = ctx(path, "REQ-B")
    check_rules(second, "M07", "2026-11-04T20:00")
    finish = {"items": [{"material_id": "M07", "review_status": "pass", "risk_reasons": [],
                        "suggested_channel": "xiaohongshu", "suggested_slot": "2026-11-04T20:00",
                        "confirmation_status": "confirmed", "pending_items": [], "in_draft": False}],
              "summary": "该排期已确认"}
    issues = validate_finish(second, finish)
    report = build_report(second, finish, {})
    assert issues == [] and report["items"][0]["confirmation_status"] == "confirmed"
    observed["R1"] = {"finish_issues": issues, "stored_confirmation": "pending",
                      "reported_confirmation": report["items"][0]["confirmation_status"],
                      "stored_channel": "douyin", "reported_channel": report["items"][0]["suggested_channel"]}

    path = root / "recheck.json"
    save(ctx(path, "REQ-A"))
    second = ctx(path, "REQ-B")
    second.materials["M07"]["caption"] = "100% 最有效"
    report = run_agent(second, MockModel()).report
    assert report["items"][0]["review_status"] == "blocked" and report["task_status"] == "completed"
    observed["R2"] = {"task_status": report["task_status"],
                      "review_status": report["items"][0]["review_status"],
                      "draft_status": report["items"][0]["draft_status"]}

    path = root / "io.json"
    c = ctx(path, "REQ-IO")
    check_rules(c, "M07", "2026-11-04T19:00")
    escaped = None
    with patch.object(c.store, "_write", side_effect=OSError(28, "No space left on device")):
        try:
            dispatch(c, "save_schedule_draft", {"items": [{"material_id": "M07", "channel": "douyin",
                     "slot": "2026-11-04T19:00", "confirmation_status": "not_required"}]})
        except OSError as exc:
            escaped = type(exc).__name__
    report = build_report(c, None, {})
    assert escaped == "OSError" and not c.ledger.save_attempts[-1].get("storage_failure")
    observed["R3"] = {"escaped_exception": escaped,
                      "storage_failure_recorded": c.ledger.save_attempts[-1].get("storage_failure", False),
                      "fallback_draft_status": report["draft"]["status"], "file_exists": path.exists()}

    path = root / "metadata.json"
    window = {"start": "2026-11-04T19:00", "end": "2026-11-04T20:00"}
    save(ctx(path, "REQ-A", window=window), "2026-11-04T20:00")
    updated = ctx(path, "REQ-A", "2026-11-04T20:00")
    result = save(updated, "2026-11-04T20:00")
    stored = updated.store.get("REQ-A")["items"][0]
    report = run_agent(ctx(path, "REQ-B", "2026-11-04T20:00"), MockModel()).report
    assert result["status"] == "duplicate" and stored["requested_slot"] == "2026-11-04T19:00"
    assert report["task_status"] == "needs_confirmation"
    observed["R4"] = {"upsert_status": result["status"], "stored_requested_slot": stored["requested_slot"],
                      "current_requested_slot": "2026-11-04T20:00", "resubmission_task_status": report["task_status"]}
    return observed


if __name__ == "__main__":
    with tempfile.TemporaryDirectory(prefix="scheduler-review-") as tmp:
        print(json.dumps(reproduce(Path(tmp)), ensure_ascii=False, indent=2))

```

本轮实际输出：

```json
{
  "R1": {
    "finish_issues": [],
    "stored_confirmation": "pending",
    "reported_confirmation": "confirmed",
    "stored_channel": "douyin",
    "reported_channel": "xiaohongshu"
  },
  "R2": {
    "task_status": "completed",
    "review_status": "blocked",
    "draft_status": "in_other_draft"
  },
  "R3": {
    "escaped_exception": "OSError",
    "storage_failure_recorded": false,
    "fallback_draft_status": "rejected",
    "file_exists": false
  },
  "R4": {
    "upsert_status": "duplicate",
    "stored_requested_slot": "2026-11-04T19:00",
    "current_requested_slot": "2026-11-04T20:00",
    "resubmission_task_status": "needs_confirmation"
  }
}
```
