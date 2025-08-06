# flux0-stream

> A minimal and extensible event streaming system for AI agents, using JSON Patch (RFC 6902) for real-time streaming with support for chunked messages — including streaming tokens, tool calls, and more.

## 🎯 Overview

`flux0-stream` is the event emission and streaming layer of Flux0. It enables real-time delivery of LLM-generated content through a structured stream of events. This module powers the streaming API for chat interfaces, tool usage, and multi-step interactions.

It is framework-agnostic and supports use cases such as:

- Emitting messages token-by-token as they're generated
- Streaming tool calls and tool results
- Managing structured session events in multi-agent systems

---

## 🧩 Features

- 🔁 **Chunked Event Emission** – Stream events as they are generated (e.g., per-token, partial tool call results)
- ⚙️ **In-Memory Backend** – Fast and simple by default; swappable for other backends like Redis
- 🧠 **Structured Event Types** – Supports message chunks, tool invocations, tool results, and status events
