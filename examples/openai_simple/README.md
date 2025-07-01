# Flux0 OpenAI Simple Example

This is a minimal Flux0 agent runner that uses the **OpenAI SDK** to generate streamed responses from a GPT model (e.g., `gpt-4o`) and emits Flux0-compatible streaming events for real-time updates.

## Features

- ✅ OpenAI SDK (v1.x+) integration using `AsyncOpenAI`.
- ✅ Real-time streaming.

## Usage

Define the agent:

```bash
flux0 agents create --name "OpenAI Simple" --type openai_simple
```
