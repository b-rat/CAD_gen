# STEP-Driven CAD System with Agentic AI

## Reference Architecture for Text-to-CAD, Automated Drawing Generation, and Manufacturing Data Management

---

## 1. Vision

Build a CAD system where **STEP is the single source of truth** for all manufacturing data — geometry, tolerancing, PMI, and design intent. Drawings, BOMs, and other downstream artifacts are **consumption views generated on demand**, not parallel sources of truth that can drift. Agentic AI (Claude Code) serves as both the design interface and the orchestration layer.

This inverts the traditional CAD workflow. Instead of:

> 3D Model → Drawing (becomes the authority) → Manufacturing

The workflow becomes:

> Conversational Design Intent → CadQuery Python Script → STEP (the authority) → On-demand artifacts (drawings, flat patterns, CAM geometry)

---

## 2. Current Working Architecture

### 2.1 Design Pipeline (Proven)

```
Human (natural language) → Claude Code → CadQuery .py script → STEP file
```

**Key implementation details:**

- **CadQuery** generates STEP via the OpenCASCADE (OCCT) kernel
- The **Python build script (.py)** is the parametric model definition, naturally storing the feature build sequence top-to-bottom
- **Semantic labels** are written directly into `ADVANCED_FACE` elements in the STEP output, giving the AI a legible map of part topology
- The workflow follows an incremental feature-based approach: start with a primitive, add features conversationally
- Claude Code reads and writes CadQuery Python, so the entire design loop stays in natural language + code

### 2.2 Three Representations from One Workflow

| Artifact | Role | Format |
|----------|------|--------|
| CadQuery `.py` script | Parametric model definition, feature history, version-controllable source | Python |
| STEP file | Manufacturing geometry, source of truth for all downstream consumption | ISO 10303 |
| Conversation history | Design rationale, intent documentation | Text |

### 2.3 Semantic Labeling Strategy

Embedding semantic labels into `ADVANCED_FACE` elements in STEP serves multiple purposes:

- **AI comprehension**: Claude Code understands the part topology without reverse-engineering anonymous B-rep geometry
- **Downstream traceability**: Labels like `bore_top_12mm`, `datum_face_A`, `pocket_floor` carry manufacturing intent directly in the geometry
- **Dimensioning logic**: The AI knows which features need which types of dimensions because the labels encode that knowledge
- **Feature selection**: On-demand drawings can target specific labeled features rather than requiring full-part documentation

---

## 3. Drawing Generation Pipeline (To Be Built)

### 3.1 Requirements

- Generate manufacturing drawings **on demand** for specific features or feature groups
- Drawings are **consumption artifacts**, not sources of truth
- Must support **dimensioning and GD&T** (ASME Y14.5 / ISO 1101)
- Must run **headlessly** — no GUI dependencies — for agent-driven operation
- Output formats: **SVG** (human-readable drawings), **DXF** (CAM-consumable geometry)
- The AI agent makes intelligent decisions about view selection, dimension placement, and drawing layout based on semantic labels

### 3.2 Recommended Pipeline Architecture

```
STEP (with semantic labels)
    │
    ├─→ pythonOCC HLR ─→ 2D edge projection (visible/hidden classified)
    │
    ├─→ AI Agent (Claude Code) decides:
    │       - Which views to generate (front, section, detail)
    │       - Which features to dimension
    │       - What tolerances to apply
    │       - Layout and arrangement
    │
    ├─→ SVG output path (manufacturing drawings for humans)
    │       - Title block, border, scale
    │       - Dimension annotations
    │       - GD&T frames
    │       - Section hatching
    │
    └─→ DXF output path (CAM-consumable geometry)
            - 1:1 scale profiles for sheet metal (laser, punch, waterjet)
            - Flat patterns
            - Tool path reference geometry
```

### 3.3 Core Components to Build

#### ViewProjector

Wraps pythonOCC's `HLRBRep_Algo`. Takes a STEP shape and view direction, returns classified 2D edges (visible solid, hidden dashed, section hatched).

```python
# Conceptual interface
projector = ViewProjector(step_shape)
edges_2d = projector.project(
    direction=(0, 0, -1),     # top view
    projection="orthographic"
)
# edges_2d.visible → list of 2D curves
# edges_2d.hidden → list of 2D curves (render dashed)
```

#### DrawingSheet

Manages the output canvas — SVG or DXF. Handles title block, border, scale factor, view arrangement.

```python
sheet = DrawingSheet(size="A3", scale="2:1", format="svg")
sheet.add_view(edges_2d, position=(100, 150), label="FRONT VIEW")
sheet.add_section_view(section_edges, position=(300, 150), label="SECTION A-A")
```

#### Dimension Primitives

Individual dimension types that know how to render themselves:

- `LinearDimension` — distance between two points
- `DiameterDimension` — circle/arc diameter
- `RadiusDimension` — circle/arc radius
- `AngleDimension` — angle between two lines
- `GDTFrame` — geometric dimensioning & tolerancing frame (datum references, tolerance zones, symbols)
- `OrdinateDimension` — for hole patterns and regular features

```python
sheet.add_dimension(LinearDimension(
    p1=(0, 0), p2=(100, 0),
    offset=15,
    value="100.00",
    tolerance=(+0.05, -0.02)
))

sheet.add_dimension(DiameterDimension(
    center=(50, 50), radius=12,
    value="Ø24.00 H7"
))
```

#### DrawingGenerator (AI Agent Interface)

The high-level interface Claude Code calls. Accepts semantic instructions, produces complete drawings.

```python
generator = DrawingGenerator(step_file="part.step")

# Feature-specific drawing
generator.create_drawing(
    features=["bore_top_12mm", "pocket_main"],
    views=["front", "section_through:bore_top_12mm"],
    dimensions="critical",  # AI decides what's critical based on labels
    output="manufacturing_review.svg"
)

# CAM output
generator.create_flat_pattern(
    output="laser_cut_profile.dxf",
    scale="1:1"
)
```

---

## 4. Technology Stack

### 4.1 Current (Proven)

| Component | Tool | Role |
|-----------|------|------|
| AI Agent | Claude Code | Conversational design interface, code generation |
| CAD Kernel | OpenCASCADE (OCCT) | Geometry engine under everything |
| Parametric API | CadQuery | Python-native 3D modeling, STEP I/O |
| Model Format | STEP (ISO 10303) | Source of truth |
| Build Script | Python `.py` | Parametric definition, feature history |

### 4.2 Drawing Generation (To Build)

| Component | Tool | Role |
|-----------|------|------|
| 3D→2D Projection | pythonOCC `HLRBRep_Algo` | Hidden line removal, edge classification |
| SVG Output | Custom Python (or svgwrite) | Human-readable manufacturing drawings |
| DXF Output | ezdxf | CAM-consumable geometry, dimensions |
| Dimensioning Logic | Custom Python + AI agent | Intelligent dimension placement |
| GD&T Rendering | Custom Python | ASME Y14.5 / ISO 1101 symbol frames |

### 4.3 Key Libraries

```
cadquery          # Parametric 3D modeling, STEP export
pythonocc-core    # Python bindings to OCCT (HLR, B-rep queries)
ezdxf             # DXF file creation with dimension support
svgwrite          # SVG generation (optional, could use raw XML)
```

---

## 5. Open Source Landscape Assessment

### 5.1 Projection (3D → 2D)

| Tool | STEP Import | HLR | Headless | Notes |
|------|-------------|-----|----------|-------|
| pythonOCC | Yes | Yes (`HLRBRep_Algo`) | Yes | Best option. ~20 lines to project. |
| CadQuery | Yes | Via `section()` | Yes | Good for section views, less control for HLR. |
| Build123d | Yes | `project_to_viewport()` | Yes | Newer API, same OCCT backend. |
| FreeCAD TechDraw | Yes | Yes | Partial (GUI workarounds) | Most complete but headless is fragile. |

### 5.2 Dimensioning

| Tool | Auto-Dimension | Headless | Output | Notes |
|------|---------------|----------|--------|-------|
| ezdxf | Manual placement | Yes | DXF | Excellent dimension entity support. Clean API. |
| FreeCAD TechDraw | Semi-auto | Partial | SVG/PDF | Best built-in dimensioning, but GUI dependencies. |
| ADG | Manual placement | Yes | SVG/PDF/PS | Niche C/Lua library. Philosophy aligned but awkward integration. |
| Custom SVG | Manual placement | Yes | SVG | Dimension = 2 extension lines + dimension line + arrows + text. ~50 lines per class. |

### 5.3 Assessment

**No single open source tool does the full pipeline.** The recommended approach is to compose pythonOCC (projection) + ezdxf or custom SVG (output/dimensioning) with the AI agent as the intelligent orchestration layer. The semantic labels already in the STEP model eliminate the hardest part of automated dimensioning: knowing *what* to dimension.

---

## 6. DXF Format Notes

### 6.1 Simplicity

DXF is a tagged text format. Entities are group code / value pairs:

```
0          ← entity type follows
LINE
8          ← layer name follows
0
10         ← start X
0.0
20         ← start Y
0.0
11         ← end X
100.0
21         ← end Y
50.0
```

Could be written with string formatting alone, though ezdxf handles dimension entity bookkeeping and ensures compatibility with downstream CAD/CAM tools.

### 6.2 CAM Consumption

Many CAM tools — particularly for sheet metal (laser, waterjet, turret punch) — consume **1:1 DXF** directly to program tool paths. This means:

- Flat pattern DXF must be at true scale (no drawing scale factor)
- Clean geometry: no duplicate edges, proper arc/line connectivity
- Layer conventions vary by shop but typically separate cut lines, bend lines, engravings
- The STEP source + CadQuery build script already knows if a part is sheet metal, enabling automatic flat pattern generation

### 6.3 Dual Output Strategy

| Output | Format | Audience | Content |
|--------|--------|----------|---------|
| Manufacturing drawing | SVG (→ PDF) | Human review, print, QC | Dimensioned views, GD&T, title block |
| CAM geometry | DXF | Machine tools, CAM software | 1:1 profiles, flat patterns, tool paths |

Both generated from the same STEP source, tailored to the consumer.

---

## 7. STEP as Source of Truth — Extended Capabilities

### 7.1 Tolerancing in STEP

STEP AP242 Edition 2 supports full semantic GD&T as structured data:

- `GEOMETRIC_TOLERANCE` entities (position, profile, runout, etc.)
- `DATUM_FEATURE` entities linked to specific faces
- `DIMENSIONAL_TOLERANCE` for size tolerances
- Tolerance zones, material condition modifiers, datum reference frames

Since the AI agent is already writing STEP entities via CadQuery/OCCT, it can attach tolerance information directly to the semantically-labeled faces. The drawing generator then *reads and renders* what's in the model rather than inferring tolerances.

### 7.2 PLM Data Extension

The same STEP-as-truth model can carry:

- **Material specifications** (via `MATERIAL_DESIGNATION`)
- **Surface finish requirements** (via `SURFACE_TEXTURE_PARAMETER`)
- **Part metadata** (part number, revision, description)
- **Assembly relationships** (for multi-part assemblies)

### 7.3 Feature History as Process Planning

The CadQuery `.py` build script, read top-to-bottom, is an implicit manufacturing process plan:

```python
# Stock
result = cq.Workplane("XY").box(100, 60, 25)

# Op 1: Face top
result = result.faces(">Z").workplane().rect(100, 60).cutBlind(-1)

# Op 2: Drill bore pattern
result = result.faces(">Z").workplane().pushPoints([(20,0), (-20,0)]).hole(12)

# Op 3: Mill pocket
result = result.faces(">Z").workplane().rect(40, 30).cutBlind(-10)
```

A machinist reading this sees the suggested operation sequence. A CAM agent could use it to generate toolpath strategies per feature.

---

## 8. Build-from-Scratch Feasibility

### 8.1 Core Drawing Pipeline

| Component | Estimated Complexity | Notes |
|-----------|---------------------|-------|
| ViewProjector (pythonOCC HLR wrapper) | ~50-100 lines | Well-documented OCCT API |
| DrawingSheet (SVG canvas, title block, border) | ~100-150 lines | SVG is just XML |
| LinearDimension | ~50 lines | Extension lines + dimension line + arrows + text |
| DiameterDimension | ~50 lines | Leader + text |
| RadiusDimension | ~40 lines | Leader + text |
| AngleDimension | ~60 lines | Arc + extension lines + text |
| GDTFrame | ~100-150 lines | Compartmented box with symbols per ASME Y14.5 |
| DXF output (via ezdxf) | ~100 lines | ezdxf handles entity bookkeeping |
| DrawingGenerator (agent interface) | ~100-150 lines | Orchestrates the above |
| **Total estimate** | **~700-1000 lines** | **Core pipeline, not including polish** |

### 8.2 What Makes This Tractable

- **Semantic labels eliminate the hard AI problem.** Knowing *what* to dimension is solved at the source, not reverse-engineered from geometry.
- **pythonOCC solves the hard geometry problem.** HLR projection is ~20 lines of API calls, not a computational geometry research project.
- **SVG and DXF are simple formats.** No binary encoding, no complex schema. Text in, text out.
- **Claude Code can write most of this pipeline itself.** The libraries are well-documented, the patterns are standard Python. Agentic coding building its own tooling.
- **Incremental value.** A prototype producing basic dimensioned SVG views is useful on day one. GD&T frames, section views, and polish come later.

### 8.3 Where the Effort Goes

The 80/20 split:

- **20% effort, 80% value**: Basic orthographic projections with linear and diameter dimensions in SVG
- **80% effort, 20% value**: Full ASME Y14.5 compliant GD&T frames, intelligent dimension placement to avoid overlaps, proper section hatching, title block standards compliance

A working prototype is a weekend with Claude Code. Production polish is ongoing iteration.

---

## 9. Implementation Roadmap

### Phase 1: Proof of Concept

- [ ] Build `ViewProjector` wrapping pythonOCC HLR
- [ ] Build minimal SVG `DrawingSheet` with border and scale
- [ ] Implement `LinearDimension` and `DiameterDimension` for SVG
- [ ] Generate a simple 3-view drawing from an existing semantically-labeled STEP
- [ ] Validate: can Claude Code drive the full pipeline conversationally?

### Phase 2: DXF and CAM Output

- [ ] Add ezdxf-based DXF output path
- [ ] Implement 1:1 scale flat pattern export for sheet metal
- [ ] Layer conventions (cut, bend, engrave) for CAM consumption
- [ ] Test with actual CAM software / machine shop feedback

### Phase 3: Tolerancing Integration

- [ ] Extend semantic labels to carry tolerance intent
- [ ] Write `GEOMETRIC_TOLERANCE` and `DATUM_FEATURE` entities into STEP AP242
- [ ] Drawing generator reads and renders GD&T from model data
- [ ] Implement `GDTFrame` rendering (SVG and DXF)

### Phase 4: Intelligent Drawing Generation

- [ ] AI agent selects views based on feature type and manufacturing process
- [ ] Automatic dimension placement with overlap avoidance
- [ ] Context-sensitive drawings: different output for mill operator vs. CMM programmer vs. QC inspector
- [ ] Section view generation driven by feature labels (e.g., auto-section through bores)

### Phase 5: Extended PLM

- [ ] Material and surface finish in STEP metadata
- [ ] BOM generation from assembly STEP files
- [ ] Feature history → process plan document generation
- [ ] Integration with shop management / ERP systems (future)

---

## 10. Key Architectural Principles

1. **STEP is the only source of truth.** Everything else is a generated view.
2. **Semantic labels are the bridge between AI and geometry.** They make the model legible to the agent.
3. **The Python build script is the parametric definition.** It's version-controllable, diffable, and human-readable.
4. **Drawings are consumption artifacts, not authority documents.** Generated on demand, tailored to the consumer.
5. **The AI agent is the orchestration layer.** It decides what to show, how to dimension, and what format to use — based on manufacturing intent encoded in the model.
6. **Dual output: SVG for humans, DXF for machines.** Same source, different consumers.
7. **Incremental build, incremental value.** Each phase produces something useful. No big-bang deployment.

---

*This document is a living reference for the STEP-driven CAD system architecture. It is intended to be read by both the human designer and by Claude Code as context for ongoing development work.*
