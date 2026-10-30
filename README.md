# LunarStream

> **Sub-500 ms Real-Time Voice AI & Multimodal Agent Framework**  
> *Core Runtime Engine: `tsukuyomi`*

LunarStream is an open-source, high-performance framework for building real-time Voice AI and Multimodal VTuber agents in async Python.

At its core is **`tsukuyomi`**, a runtime engine focused on deterministic scheduling, low-latency execution, cancellation correctness, and measurable performance before higher-level AI features are added.

---

## Vision

The long-term goal is a production-grade system capable of:

- Sub-500 ms Time-to-First-Audio (TTFA)
- Decoupled Data Plane / Control Plane architecture
- Speculative turn-taking
- Dual-persona state machines
- Real-time stream perception
- Reproducible latency benchmarking and architectural verification

The project is built incrementally, with every architectural claim verified before new features are introduced.

---

## Current Status

**Tier-0 · Week 1 — Runtime Foundations**

The project is currently focused on building the core systems layer that everything else will depend on.

### Current Milestone

- Monorepo scaffolding
- `tsukuyomi.core` standard-library async primitives
- Deterministic `VirtualTimeLoop`
- Event-loop lag monitoring
- Performance verification infrastructure

### Performance Targets

- Event-loop lag: **p99 ≤ 5 ms**
- Zero undetected stalls **>20 ms**
