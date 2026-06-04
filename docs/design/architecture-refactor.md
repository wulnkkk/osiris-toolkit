---
audience: [human]
topic: design
kind: design
updated: 2026-06-04
---

# 架构重构 — 数据模型下沉 + Simulation 拆分 + 死代码清理

> 2026-06-04 | 设计规格
> 版本迭代: v0.14.0

---

## 目标

通过两步重构消除架构债务：
1. **数据模型下沉** — 将 `diagnostics.py` 数据类提取为 `_models.py`，消除 3 处反向依赖
2. **Simulation 拆分 + 死代码清理** — 将 1,120 行的 `Simulation` 拆分为可独立测试的模块；移除废弃 API

## 动机

当前架构的三个痛点有共同根因：

```
根因: diagnostics.py 数据模型放在中层 (sim/)
  ↓
症状1: io/compute 反向依赖 sim (#60)
症状2: Simulation 1,120 行 (#62)，发现+解析+访问+元数据混在一起
症状3: 废弃 API 不敢删，PostProcessor/PostVisHub 半取代
```

---

## 阶段 1：数据模型下沉

### 当前依赖层次

```
底层:  exceptions  _generated  deck  io  units  compute
中层:  sim (含 diagnostics.py 数据类)
上层:  analysis  vis  postproc  workflow
```

### 修复后

```
基础层: exceptions  _generated  _models  ← 新增
底层:    deck  io  units  compute        ← 可安全 import _models
中层:    sim (diagnostics.py → shim)
上层:    analysis  vis  postproc  workflow
```

### 新建 `src/osiris_toolkit/_models.py`

`diagnostics.py` 全部内容（~643 行）移入 `_models.py`。内容不变：

- `GridAxis` — dataclass + `value_to_index()`/`index_to_value()`
- `Field` / `GridData` (alias) — dataclass + 运算符重载 + 物理切片 + `to_npz`/`to_csv`/`to_vtk`
- `ParticleData` — dataclass + `filter()`/`compress()`/`to_npz`/`to_csv`
- `PhasespaceData`, `TrackData`, `HistoryData`, `TimingsData` — 纯 dataclass
- `FieldInfo`, `ParticleInfo`, `TrackInfo` — 轻量元数据 dataclass
- `_eval_particle_expr()` — `ParticleData.filter()` 辅助函数

### `sim/diagnostics.py` → re-export shim

```python
"""Backward-compatible re-exports. Import from _models directly for new code."""
from osiris_toolkit._models import (
    Field, FieldInfo, GridAxis, GridData, HistoryData,
    ParticleData, ParticleInfo, PhasespaceData, TimingsData,
    TrackData, TrackInfo, _eval_particle_expr,
)
__all__ = [...]
```

### Import 更新

| 文件 | 旧 import | 新 import |
|------|-----------|-----------|
| `io/vtk_exporter.py` | `from sim.diagnostics import Field` | `from _models import Field` |
| `compute/deposit.py` | `from sim.diagnostics import Field, GridAxis` | `from _models import Field, GridAxis` |
| `compute/transform.py` | `from sim.diagnostics import Field, GridAxis` | `from _models import Field, GridAxis` |
| `analysis/stats.py` | `from sim.diagnostics import GridData` | `from _models import GridData` |
| `analysis/_result_types.py` | `from sim.diagnostics import GridData` | `from _models import GridData` |
| `vis/raw.py` | `from sim.diagnostics import ParticleData` | `from _models import ParticleData` |
| `vis/tracks.py` | `from sim.diagnostics import TrackData` | `from _models import TrackData` |
| `vis/kspace.py` | `from sim import GridData, Simulation` | `from _models import GridData; from sim import Simulation` |
| `sim/simulation.py` | `from sim.diagnostics import ...` | `from _models import ...` |
| `sim/catalog.py` | `from sim.diagnostics import GridData` | `from _models import GridData` |
| `sim/__init__.py` | `from sim.diagnostics import ...` | `from _models import ...` |
| `__init__.py` | `from sim import Field, ...` | 不变（sim/__init__.py 仍 re-export） |

---

## 阶段 2：Simulation 拆分 + 死代码清理

### 2A. Simulation 拆分

`simulation.py`（1,120 行）→ 4 个文件：

```
sim/
├── _parse.py         # NEW: ~80 行，解析辅助函数
│   ├── _ITER_FILE_RE
│   ├── _parse_iter_file()
│   ├── _parse_quantity()
│   ├── _REPORT_SUFFIXES
│   ├── _parse_history_file()
│   └── _parse_timings_file()
│
├── _accessors.py     # NEW: ~400 行，数据访问器 mixin
│   └── class _DataAccessors:
│       ├── get_field() / get_density() / get_cell_avg()
│       ├── get_udist() / get_raw() / get_tracks()
│       ├── get_phasespace() / get_chargecons()
│       ├── get_current() / get_ion() / get_wall()
│       ├── _read_grid() / _read_particle() / _read_phasespace() / _read_tracks()
│       └── list_fields() / list_species() / list_*()
│
├── _info.py          # NEW: ~80 行，元数据访问器 mixin
│   └── class _InfoAccessors:
│       ├── info_field() / info_raw() / info_tracks()
│       └── _read_info()
│
├── simulation.py     # ~400 行，Simulation 核心
│   └── class Simulation(_DataAccessors, _InfoAccessors):
│       ├── __init__() / _discover() / _discover_ms()
│       ├── _discover_fld() / _discover_chargecons() / ...
│       ├── to_dict() / from_dict()
│       └── path / output_root / config / run_info 等 property
```

`Simulation` 通过多重继承获取访问器方法，对外 API 完全不变。

### 2B. 死代码清理

| 位置 | 内容 | 操作 | 理由 |
|------|------|------|------|
| `analysis/__init__.py` | `Analyzer` 基类 (deprecated) | 移除 | `Protocol` 已替代 |
| `vis/__init__.py` | `VisEngine` (deprecated) | 移除 | `PostVisHub` 已完全替代 |
| `vis/kspace.py:25` | `compute_k_space` (deprecated wrapper) | 移除 | 用户用 `compute.fft.compute_k_space` |
| `vis/scattering.py:61` | `analyze_scattering` (deprecated) | 移除 | 用户用 `analysis.scattering.ScatteringAnalyzer` |

移除前确认无残留引用：
```bash
grep -rn "VisEngine\|from.*Analyzer[^s]\|vis\.kspace\.compute_k_space\|vis\.scattering\.analyze_scattering" src/ tests/
```

---

## 公共 API 保证

阶段 2 完成后，以下所有用法保持不变：

```python
# 顶层 import
from osiris_toolkit import Field, Simulation, GridData, ParticleData

# sim 层 import
from osiris_toolkit.sim import Field, Simulation
from osiris_toolkit.sim.diagnostics import Field  # 通过 shim 仍有效

# Simulation 使用方式完全不变
sim = Simulation("/path/to/output")
field = sim.get_field("e1", iteration=50)
info = sim.info_field("e1", iteration=50)
sim.list_fields()

# PostVisHub 不变
from osiris_toolkit.vis import PostVisHub
hub = PostVisHub(sim)
hub.plot_field("e1", iteration=50)
```

---

## 测试

| 文件 | 测试内容 |
|------|----------|
| `tests/test_models.py` (新建) | Field 运算符、切片、序列化；ParticleData filter/compress；GridAxis 坐标转换 |
| `tests/test_sim/test_parse.py` (新建) | _parse_iter_file 边界情况；_parse_quantity 修饰符检测 |
| `tests/test_sim/test_accessors.py` (新建) | get_field/get_raw/get_tracks；各诊断类型访问器；_read_* 错误处理 |
| `tests/test_sim/test_info.py` (新建) | info_field/info_raw/info_tracks 元数据读取 |
| 现有测试 | 所有 import 路径保持兼容（shim），全部应通过 |

## 文件变更汇总

| 操作 | 文件 | 行数 |
|------|------|------|
| 新建 | `_models.py` | +643 |
| 改写 | `sim/diagnostics.py` | 643→15 |
| 新建 | `sim/_parse.py` | +80 |
| 新建 | `sim/_accessors.py` | +400 |
| 新建 | `sim/_info.py` | +80 |
| 改写 | `sim/simulation.py` | 1,120→400 |
| 更新 | 12 个文件的 import 路径 | ~30 |
| 删除 | 4 处死代码 | -120 |
| 新建 | 4 个测试文件 | +~40 tests |

---

## 范围边界

### 本次包含
- 数据模型提取到 `_models.py`
- Simulation 拆分为 parse + accessors + info
- 4 处死代码移除
- 12 个文件的 import 更新
- 向后兼容 shim
- 新测试

### 本次不包含
- 功能新增（HISTORY/UDIST 等）
- PostPostProcessor/PostVisHub 重构
- 其他模块的重构

## 关联

- 上游: `docs/note/analysis/2026-06-03-comprehensive-project-review.md`
- 下游: `docs/note/execution/2026-06-04-plan-architecture-refactor.md`
- TODO: #60, #62
