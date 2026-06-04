---
audience: [human]
topic: design
kind: design
updated: 2026-06-04
---

# UnitSystem 架构设计 — 单位处理的全面重构

> 日期：2026-06-04
> 类型：设计文档
> 版本目标：v0.15.0（或 v1.0.0）
> 上游分析：
>   - `docs/note/analysis/2026-06-04-agent-data-processing-review.md`
>   - `docs/note/analysis/2026-06-04-kspace-2pi-unit-architecture.md`

---

## 1. 动机

当前 `UnitConverter` 存在以下结构性缺陷：

1. **k 空间完全绕过** — `compute_k_space`、`plot_k_space`、`mask_energy` 手写单位转换（×2π, /ω₀, ÷2π），不经 UnitConverter，导致轴标签偏离 2π、xlim 硬编码不匹配数据
2. **单体耦合** — 所有单位尺度硬编码在 `_build_scales()` 一个 100 行函数中，加新量纲需改函数体
3. **代码重复** — 每个 vis 函数重复 `if converter is not None` 分支 × 3-5 处（值转换、坐标转换、标签生成）
4. **无类型安全** — `convert(data, "length", "um")` 三个裸字符串，拼写错误运行时才暴露
5. **不可扩展** — 第三方无法注册自定义量纲

## 2. 设计原则

- **compute 层只做数学，units 层管单位** — FFT 不碰归一化参数
- **数据与单位系统通过外观（Facade）组合** — `GridData` 保持纯粹，`QuantifiedGrid` 叠加单位能力
- **自动推导为主，显式消歧义为辅** — `grid.to("um")` 自动识别 length，歧义时用 `grid.as_quantity("e_field").to("um")`
- **硬切换，不兼容旧 API** — 一次大版本更新中完成，`UnitConverter` → `UnitSystem`，`converter` 参数 → `system` 参数
- **严格报错** — 无 system 时只能使用 `"norm"` 单位，任何非 norm 查询抛异常，不使用虚设 omega_p

## 3. 架构总览

```
┌──────────────────────────────────────────────────────────┐
│  UnitSystem (omega_p, params)                            │
│  ├── length: QuantityKind                                │
│  ├── time: QuantityKind                                  │
│  ├── e_field: QuantityKind                               │
│  ├── b_field: QuantityKind                               │
│  ├── wavenumber: QuantityKind      ← 新增                │
│  ├── momentum: QuantityKind                              │
│  ├── energy: QuantityKind                                │
│  ├── density: QuantityKind                               │
│  ├── frequency: QuantityKind                             │
│  ├── velocity: QuantityKind                              │
│  ├── charge: QuantityKind                                │
│  ├── current: QuantityKind                               │
│  └── mass: QuantityKind                                  │
└──────────────┬───────────────────────────────────────────┘
               │ attach to data
               ▼
┌──────────────────────────────────────────────────────────┐
│  QuantifiedGrid(grid, system)                            │
│  ├── .to(unit)          → auto-infer quantity            │
│  ├── .as_quantity(name) → explicit quantity view         │
│  ├── .norm()            → raw normalized data            │
│  ├── .x / .y / .time    → _AxisView with .to(), .label() │
│  └── .label / .latex()  → unit-aware labels              │
└──────────────┬───────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│  QuantifiedSpectrum(result, system)                      │
│  ├── .kx / .ky            → _QuantityView (wavenumber)   │
│  ├── .spectrum            → np.ndarray                   │
│  └── from_field(grid)     → factory                      │
└──────────────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────┐
│  vis / analysis 层                                       │
│  - 接收 system 参数（替代 converter）                      │
│  - 内部用 QuantifiedGrid / QuantifiedSpectrum            │
│  - 标签从 QuantityKind.latex() 获取                      │
│  - 单位转换经过单一入口 UnitSystem                        │
│  - CLI 暴露 --k-unit, --omega0-norm, --xlim, --ylim...   │
└──────────────────────────────────────────────────────────┘
```

## 4. 核心组件

### 4.1 QuantityKind

每个物理量是一个独立的 frozen dataclass 实例，不可变。

```python
@dataclass(frozen=True)
class QuantityKind:
    name: str                    # "length", "wavenumber", ...
    description: str             # "Spatial coordinate"
    norm_unit_label: str         # "c/omega_p"
    norm_unit_latex: str         # r"c/\omega_p"
    scales: dict[str, float]     # {"norm": 1.0, "um": ..., "nm": ...}
    auto_unit: str               # "um" for length
    label_template: str          # r"x [${unit}$]"  — uses "${unit}$" placeholder
    latex_template: str | None   # r"$x\ [\mathrm{${unit}$}]$"  — same placeholder
    axis_types: tuple[int, ...]  # e.g., (0, 1) for spatial axes

    def to(self, data, unit="auto") -> np.ndarray: ...
    def label(self, unit="auto") -> str: ...
    def latex(self, unit="auto") -> str: ...
```

预定义实例：`LENGTH`, `TIME`, `E_FIELD`, `B_FIELD`, `WAVENUMBER`, `MOMENTUM`, `ENERGY`, `DENSITY`, `FREQUENCY`, `VELOCITY`, `CHARGE`, `CURRENT`, `MASS`。

`scales` 中的具体数值在 `UnitSystem.__init__` 中计算并填充（通过 `dataclasses.replace`）。

### 4.2 UnitSystem

```python
class UnitSystem:
    def __init__(self, omega_p: float, params: SimulationParams | None = None):
        # omega_p 必须 > 0
        # params 可选；Wavenumber 等量纲通过 params 访问额外仿真参数
        
    # 属性访问：system.length, system.wavenumber, ...
    def __getitem__(self, name: str) -> QuantityKind: ...
    
    @classmethod
    def from_params(cls, params: SimulationParams) -> "UnitSystem": ...
```

### 4.3 QuantifiedGrid

```python
@dataclass
class QuantifiedGrid:
    grid: GridData
    system: UnitSystem | None
    
    def to(self, unit="auto") -> np.ndarray:
        """Auto-infer quantity from unit → convert data."""
        
    def as_quantity(self, name: str) -> _QuantityView: ...
    def norm(self) -> np.ndarray: ...  # always works
    
    @property
    def x(self) -> _AxisView: ...
    @property
    def y(self) -> _AxisView: ...
    @property
    def time(self) -> _AxisView: ...
```

当 `system=None` 时：
- `.to(unit)` 只在 `unit in ("auto", "norm")` 时工作，其他抛 `UnitConversionError`
- `.as_quantity()` 总是抛异常
- `.norm()` 总是可用
- `_AxisView.to(unit)` 同上；`_AxisView.label()` 回退到 `GridAxis.units`

### 4.4 QuantifiedSpectrum

```python
@dataclass
class QuantifiedSpectrum:
    kx_norm: np.ndarray
    ky_norm: np.ndarray
    spectrum: np.ndarray
    quantity: str
    iteration: int
    time: float
    system: UnitSystem
    
    @property
    def kx(self) -> _QuantityView: ...
    @property
    def ky(self) -> _QuantityView: ...
    
    @classmethod
    def from_field(cls, grid: GridData, system: UnitSystem) -> "QuantifiedSpectrum": ...
```

### 4.5 辅助类

```python
@dataclass
class _QuantityView:
    data: np.ndarray
    quantity: QuantityKind
    def to(self, unit="auto") -> np.ndarray: ...
    def label(self, unit="auto") -> str: ...
    def latex(self, unit="auto") -> str: ...

@dataclass
class _AxisView:
    grid: GridData
    axis_index: int
    system: UnitSystem | None
    force_quantity: str | None = None
    def to(self, unit="auto") -> tuple[float, float]: ...  # (min, max)
    def label(self, unit="auto") -> str: ...
    def latex(self, unit="auto") -> str: ...
```

## 5. Wavenumber 量纲

### 5.1 `_build_wavenumber_scales`

```python
def _build_wavenumber_scales(
    k_p_si: float,                   # ω_p / c  [rad/m]
    params: SimulationParams | None,
) -> dict[str, float]:
    scales = {
        "norm": 1.0,                 # k/k_p
        "rad/m": k_p_si,
        "rad/um": k_p_si / 1e6,
        "rad/nm": k_p_si / 1e9,
        "um^-1": k_p_si / (2 * np.pi * 1e6),
    }
    if params is not None and params.omega0_norm is not None:
        scales["k0"] = 1.0 / params.omega0_norm   # k/k₀
    return scales
```

### 5.2 K-space 管道

```
ZDF grid → compute_k_space(data, dx, dy) → kx, ky (归一化角波数)
         → QuantifiedSpectrum.from_field(grid, system)
         → qspec.kx.to("k0")  →  k/k₀  (经过 system.wavenumber)
         → 不再有手写的 /(2π)
```

### 5.3 xlim 自适应

```python
def _auto_k_range(k_norm, spectrum, unit, quantity, threshold_frac=0.01, margin=0.1):
    """根据 spectrum 幅值 > 1% 峰值的区域自动确定显示范围。"""
```

默认 `xlim=None` 时自动计算，用户可通过参数手动覆盖。

## 6. SimulationParams 扩展

```python
@dataclass
class SimulationParams:
    omega_p0: float
    n0: float | None = None
    gamma: float | None = None
    omega0_norm: float | None = None   # ← 新增

    @classmethod
    def from_deck(cls, deck: dict) -> "SimulationParams":
        # 从 antenna / zpulse / laser section 提取 omega0
```

## 7. vis/analysis 模块变更

### 7.1 签名的统一变化

所有 vis 函数的 `converter: UnitConverter | None = None` → `system: UnitSystem | None = None`。

内部通过 `QuantifiedGrid` / `QuantifiedSpectrum` 访问数据，标签从 `QuantityKind` 获取。

### 7.2 受影响的文件

| 文件 | 变更 |
|------|------|
| `compute/fft.py` | `compute_k_space` 移除 `omega0_norm` 参数 |
| `compute/integrate.py` | `mask_energy` 加 `system` 参数，去 `/2π` |
| `vis/common.py` | `get_converter()` → `get_system()` |
| `vis/field.py` | converter → system |
| `vis/density.py` | converter → system |
| `vis/phasespace.py` | converter → system |
| `vis/kspace.py` | converter → system，去 `/2π`，加 `_auto_k_range` |
| `vis/energy.py` | `plot_spectrum` 去 `/2π`，converter → system |
| `vis/scattering.py` | converter → system |
| `vis/composite.py` | converter → system |
| `vis/comparison.py` | converter → system |
| `vis/batch.py` | converter → system，加 wavenumber 诊断支持 + 进度 |
| `vis/__init__.py` | PostVisHub converter → system |
| `analysis/kspace.py` | KSpaceAnalyzer 返回 `QuantifiedSpectrum` |
| `analysis/_protocol.py` | `_converter` → `_system` |
| `analysis/__init__.py` | PostAnalysisHub converter → system |
| `units/converter.py` | 保留旧 `UnitConverter` 加 DeprecationWarning；新增 `UnitSystem` + `QuantityKind` |
| `units/params.py` | `SimulationParams` 加 `omega0_norm` |
| `postproc.py` | PostProcessor converter → system |
| `cli.py` | 加 `--k-unit`, `--omega0-norm`, `--xlim`, `--ylim`, `--clim`, `--white-low`, `--dry-run`, `--progress` |

## 8. CLI 变更

### 8.1 `vis plot`

```bash
osiris-toolkit vis plot --kind KSPACE --quantity e1 --iteration 50 <path> \
    --k-unit k0 \           # k0 | rad/um | rad/nm | um^-1 | norm
    --omega0-norm 10.0 \    # 可选，deck 中有则自动提取
    --xlim -3.0,3.0 \
    --ylim -3.0,3.0 \
    --clim -5.0,2.0 \
    --white-low 0.05 \
    --log-scale / --no-log-scale
```

`--k-unit` 等 k-space 参数只在 `--kind KSPACE` 时生效，其他 kind 下忽略。

### 8.2 `vis batch`

```bash
osiris-toolkit vis batch --dry-run <path> Au     # 预览
osiris-toolkit vis batch <path> Au --progress    # tqdm 进度
osiris-toolkit vis batch <path> Au --kinds k_space  # 单独出 k-space
```

### 8.3 `sim info`

```bash
osiris-toolkit sim info <path> --output json
# 补充结构化输出，含 omega0_norm
```

## 9. 迁移步骤

| 步 | 内容 | 破坏性 |
|----|------|--------|
| 1 | 新增 `QuantityKind` + `UnitSystem`（保留旧 `UnitConverter`） | 否 |
| 2 | 新增 `QuantifiedGrid`、`QuantifiedSpectrum`、`_AxisView`、`_QuantityView` | 否 |
| 3 | 新增 `SimulationParams.omega0_norm` + `_extract_omega0` | 否 |
| 4 | 重写 `compute_k_space`（去掉 `omega0_norm` 参数） | **是** |
| 5 | 迁移所有 vis 函数：`converter` → `system` | **是** |
| 6 | 迁移分析模块：`_converter` → `_system` | **是** |
| 7 | 废弃 `UnitConverter`（DeprecationWarning） | 否（过渡期） |
| 8 | 补充 CLI k-space 参数 | 否 |
| 9 | 补充 wavenumber + UnitSystem 测试，更新现有测试 | 否 |
| 10 | 移除 `UnitConverter` + 旧 API | **是** |

### 用户 API 变化

```python
# 旧
converter = UnitConverter(omega_p=3.55e15)
plot_field("e1", 100, sim=sim, converter=converter, x_unit="um")
plot_k_space("e1", 100, sim=sim, converter=converter, omega0_norm=10.0)

# 新
system = UnitSystem(omega_p=3.55e15, params=params)
plot_field("e1", 100, sim=sim, system=system, x_unit="um")
plot_k_space("e1", 100, sim=sim, system=system, k_unit="k0")
```

## 关联

- 上游分析：
  - `docs/note/analysis/2026-06-04-agent-data-processing-review.md`
  - `docs/note/analysis/2026-06-04-kspace-2pi-unit-architecture.md`
- 下游计划：`docs/note/execution/2026-06-04-plan-unit-system-architecture.md`（待 writing-plans 产出）
- TODO： #65, #66, #67, #68, #69, #70, #71, #77, #78, #79, #80
