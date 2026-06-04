---
audience: [human]
topic: design
kind: design
updated: 2026-06-04
---

# 后处理模块架构重设计

> 2026-05-28 | 设计

## 背景

评估发现 `analysis/` 和 `vis/` 两个后处理模块存在以下问题：

1. **边界违规** — `vis/kspace.py::compute_k_space()` 是纯数值 FFT 计算，`vis/scattering.py::analyze_scattering()` 是完整分析流程，均错放在 vis/ 下
2. **重复实现** — `analysis/emf.py::EMFAnalyzer.spectrum()` 和 `vis/kspace.py::compute_k_space()` 都在做 2D FFT
3. **链路断裂** — analysis 层算出的场能量、频谱、Poynting 通量在 vis 层没有对应绑图函数
4. **双入口互不感知** — `Analyzer` 和 `VisEngine` 各自独立，用户需了解两个入口的心智模型
5. **扩展无规范** — 代办中 8 种零覆盖诊断类型无统一扩展模式

## 设计目标

- 建立清晰的三层架构：`compute/` → `analysis/` → `vis/`
- 单一顶层入口 `PostProcessor`
- 分析结果以强类型 dataclass 传递，vis 可直接消费
- 定义 `DiagnosticAnalyzer` 协议，统一新诊断类型扩展模式
- 保持向后兼容，旧 API 通过 deprecation warning 引导迁移

## 新目录结构

```
src/osiris_toolkit/
├── compute/                    # 新增：纯数值计算层
│   ├── __init__.py
│   ├── fft.py                  # compute_k_space, spectral_power
│   └── integrate.py            # mask_energy, trapz_2d, line_integrate
│
├── analysis/                   # 重构：物理语义分析层
│   ├── __init__.py             # PostAnalysisHub
│   ├── _protocol.py            # 新增：DiagnosticAnalyzer 抽象基类
│   ├── _result_types.py        # 新增：所有分析结果 dataclass
│   ├── emf.py                  # EMFAnalyzer (精简，FFT→compute/)
│   ├── scattering.py           # 新增：从 vis/ 迁入 analyze_scattering
│   ├── density.py              # 新增：DensityAnalyzer
│   ├── species.py              # SpeciesAnalyzer (粒子分析保留)
│   ├── phasespace.py           # 新增：PhasespaceAnalyzer
│   ├── kspace.py               # 新增：KSpaceAnalyzer
│   ├── stats.py                # 保留
│   └── parallel.py             # 保留
│
├── vis/                        # 精简：纯绑图层
│   ├── __init__.py             # PostVisHub
│   ├── common.py               # load_sim, get_converter, save_or_show
│   ├── field.py                # plot_field, plot_all_fields
│   ├── density.py              # plot_density
│   ├── phasespace.py           # plot_phasespace
│   ├── kspace.py               # plot_k_space (移除 compute_k_space)
│   ├── scattering.py           # plot_scattering_fraction (移除 analyze_*)
│   ├── composite.py            # plot_composite
│   ├── energy.py               # 新增：场能量/频谱/Poynting 绑图
│   ├── batch.py                # process_simulation
│   └── parallel.py             # batch_process_parallel
│
└── postproc.py                 # 新增：顶层 PostProcessor
```

## 三层架构

### compute/ — 纯数值计算层

- 输入/输出均为 `np.ndarray` 或 `float`
- **不 import sim/，不 import units/，不 import matplotlib**
- 纯函数，无状态，可被 analysis 和 vis 调用
- 公开 API：`compute_k_space()`, `spectral_power()`, `mask_energy()`, `trapz_2d()`, `line_integrate()`

### analysis/ — 物理语义分析层

- 依赖 `compute/` + `sim/` + `units/`
- 每个诊断类型一个 Analyzer 类，实现 `DiagnosticAnalyzer` 协议
- 分析方法返回强类型 dataclass（定义在 `_result_types.py`）
- **不 import matplotlib**
- 子模块：emf, scattering, density, species, phasespace, kspace, stats

### vis/ — 绑图渲染层

- 依赖 `analysis/` 结果类型 + `sim/` 原始数据 + `compute/`（仅 colormap 范围等辅助用途）
- 每个诊断类型一个绑图函数或简单的 Vis 门面类
- **不直接做 FFT、积分等数值计算**
- 结果保存到文件或显示

## 数据流

```
sim/                         compute/               analysis/              vis/
────────────────────────────────────────────────────────────────────────────────
Simulation.get_field() ──►  compute_k_space() ──►  EMFAnalyzer ──► EMDynamicsResult
                             mask_energy()             .em_dynamics()   │
                             trapz_2d()                .field_energy()  │
                                                        .spectrum()     ▼
                                                                  plot_energy_timeline()
                                                                  plot_spectrum()
                                                                  plot_poynting()
```

## 诊断分析协议

```python
class DiagnosticAnalyzer(ABC):
    """所有诊断类型分析器的抽象基类。"""

    @property
    @abstractmethod
    def diagnostic_kind(self) -> str:
        """OSIRIS 诊断种类名。"""

    @abstractmethod
    def list_available(self) -> list[str]:
        """返回该诊断下可分析的量/物种列表。"""
```

不强制统一的 `analyze()` 签名——不同诊断类型的参数差异大（field_energy 需要 quantity+iteration，density_profile 需要 species+axis），因此协议只约束元信息和发现接口。

## 结果类型

所有分析方法返回明确命名的 dataclass，定义在 `analysis/_result_types.py`：

```python
@dataclass
class FieldEnergyResult:
    quantity: str
    iteration: int
    time: float
    total_energy: float
    grid: GridData | None

@dataclass
class EMDynamicsResult:
    iteration: int
    time: float
    e2_total: float
    b2_total: float
    total: float

@dataclass
class EMSpectrumResult:
    quantity: str
    iteration: int
    time: float
    kx_k0: np.ndarray
    ky_k0: np.ndarray
    spectrum: np.ndarray

@dataclass
class ScatteringResult:
    quantity: str
    iterations: list[int]
    times: list[float]
    scattered_fraction: list[float]
    side_scatter_fraction: list[float]
    back_scatter_fraction: list[float]
    mask_info: dict
```

## 顶层 API

```python
from osiris_toolkit import Simulation
from osiris_toolkit.postproc import PostProcessor

sim = Simulation("/path/to/output")
pp = PostProcessor(sim)

# ── 分析 ──
pp.analyze.emf.field_energy("e1", iteration=50)      # → FieldEnergyResult
pp.analyze.emf.em_dynamics(iteration=50)              # → EMDynamicsResult
pp.analyze.emf.spectrum("e1", iteration=50)           # → EMSpectrumResult
pp.analyze.scattering.analyze("e3")                   # → ScatteringResult
pp.analyze.density.profile("electrons", iteration=50) # → DensityProfileResult
pp.analyze.species.energy_spectrum("electrons", 50)   # → ParticleSpectrumResult

# ── 可视化 ──
pp.vis.field.plot("e1", iteration=50, x_unit="um")   # 直接读 sim 数据
pp.vis.energy.timeline(emd_result)                     # 消费分析结果
pp.vis.energy.spectrum(spec_result)                    # 消费分析结果
pp.vis.scattering.plot(result)                         # 消费分析结果

# ── 批处理 ──
pp.batch(sim_name="run_01", x_unit="um")
```

### 内部结构

```python
class PostProcessor:
    def __init__(self, sim, converter=None):
        self._sim = sim
        self._converter = converter

    @cached_property
    def analyze(self) -> PostAnalysisHub: ...
    
    @cached_property
    def vis(self) -> PostVisHub: ...

class PostAnalysisHub:
    @cached_property
    def emf(self) -> EMFAnalyzer: ...
    @cached_property
    def scattering(self) -> ScatteringAnalyzer: ...
    # ... 每个诊断类型一个 cached_property

class PostVisHub:
    @cached_property
    def field(self) -> FieldVis: ...
    @cached_property
    def energy(self) -> EnergyVis: ...
    # ...
```

所有 analyzer 和 vis 门面均为懒加载，只在首次访问时初始化。

## 新诊断类型扩展模式

每新增一种诊断类型（RAW、TRACKS、HISTORY、UDIST、CELL_AVG、CURRENT、CHARGE_CONS、TIMINGS），遵循三步：

1. **`analysis/<name>.py`** — 实现 `XxxAnalyzer(DiagnosticAnalyzer)` + 结果 dataclass（添加到 `_result_types.py`）
2. **`vis/<name>.py`** — 绑图函数，接收 analysis 结果类型和/或原始 sim 数据
3. **`postproc.py`** — `PostAnalysisHub` 和 `PostVisHub` 各加一个 `@cached_property`

无需手动注册表。

### 优先级映射

| 诊断类型 | analysis/ | vis/ | 代办 # |
|----------|-----------|------|--------|
| RAW | `raw.py` → RawAnalyzer | `raw.py` | 23 |
| TRACKS | `tracks.py` → TracksAnalyzer | `tracks.py` | 24 |
| HISTORY | `history.py` → HistoryAnalyzer | `history.py` | 27 |
| UDIST | `udist.py` → UdistAnalyzer | `udist.py` | 28 |
| CELL_AVG | `cell_avg.py` → CellAvgAnalyzer | `cell_avg.py` | 29 |
| CURRENT | `current.py` → CurrentAnalyzer | `current.py` | 30 |
| CHARGE_CONS | `charge_cons.py` → ChargeConsAnalyzer | `charge_cons.py` | 31 |
| TIMINGS | `timings.py` → TimingsAnalyzer | `timings.py` | 32 |

## 搬迁清单

| 当前位置 | 迁往 | 处理 |
|----------|------|------|
| `vis/kspace.py::compute_k_space()` | `compute/fft.py` | 移动，旧位置 re-export + deprecation |
| `vis/scattering.py::analyze_scattering()` | `analysis/scattering.py` | 移动，旧位置 re-export + deprecation |
| `vis/scattering.py::ScatteringResult` | `analysis/_result_types.py` | 移动，旧位置兼容导入 |
| `vis/scattering.py::_mask_energy()` | `compute/integrate.py` 改名为 `mask_energy()` | 移动，去掉前导下划线 |
| `analysis/emf.py::EMFAnalyzer.spectrum()` | 内部改为调 `compute/fft.py` | 消除重复 |
| `vis/__init__.py::VisEngine` | 保留，加 deprecation warning | 引导到 PostProcessor |
| `analysis/__init__.py::Analyzer` | 保留，加 deprecation warning | 引导到 PostProcessor |

## 向后兼容

- 所有搬移的符号在旧位置保留 re-export，并发出 `DeprecationWarning`
- 以下公开 API 签名和行为不变：`plot_field()`, `plot_all_fields()`, `plot_density()`, `plot_phasespace()`, `plot_k_space()`, `process_simulation()`, `batch_process_parallel()`
- CLI 入口不在本次重构范围
- `Simulation` 和 `GridData` 等 sim/ 层接口不变

## 实施顺序

1. **Phase 1** — 新建 `compute/` 模块（`fft.py`, `integrate.py`），消除 `EMFAnalyzer.spectrum()` 重复
2. **Phase 2** — 新建 `analysis/_result_types.py`、`_protocol.py`，搬迁 `analyze_scattering` 到 `analysis/scattering.py`
3. **Phase 3** — 新建 `postproc.py`（`PostProcessor` + `PostAnalysisHub` + `PostVisHub`），整合现有 analyzer
4. **Phase 4** — 在 vis/ 层新增 `energy.py`，补全 analysis→vis 链路
5. **Phase 5** — 旧入口添加 deprecation warning
6. **Phase 6** — 按代办优先级逐个扩展新诊断类型（RAW P0 → TRACKS P0 → ...）

## 关联

- 上游: 2026-05-26-eval-diagnostic-coverage.md, 2026-05-28-eval-osiris-toolkit-architecture.md
- 下游: 2026-05-28-plan-postproc-architecture.md
- TODO: 23, 24, 25, 26, 27, 28, 29, 30, 31, 32
