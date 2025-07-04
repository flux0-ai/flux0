# Flux0

> The open framework for building real-time, AI-powered applications with multi-agent support, session management, and LLM-agnostic integration.

⭐ If you find Flux0 useful, please consider giving us a star on GitHub! Your support helps us continue to innovate and deliver exciting features.

![GitHub contributors](https://img.shields.io/github/contributors/flux0-ai/flux0)
[![GitHub issues](https://img.shields.io/github/issues/flux0-ai/flux0)](https://github.com/flux0-ai/flux0/issues)
[![GitHub stars](https://img.shields.io/github/stars/flux0-ai/flux0)](https://github.com/flux0-ai/flux0/stargazers)
![GitHub closed issues](https://img.shields.io/github/issues-closed/flux0-ai/flux0)
![GitHub pull requests](https://img.shields.io/github/issues-pr-raw/flux0-ai/flux0)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/flux0-ai/flux0)
[![GitHub license](https://img.shields.io/github/license/flux0-ai/flux0)](https://github.com/flux0-ai/flux0)

## What is Flux0?

Flux0 is a powerful framework for building and deploying AI-powered applications. It helps developers manage the complexity of orchestrating AI agents, handling real-time communication, and integrating with LLMs and UIs — all in a unified, scalable way.

Flux0 simplifies:

- Deploying LangGraph, PydanticAI agents, or your own LLM logic.
- Building real-time streaming apps using JSON patch-based event streaming.
- Creating responsive user interfaces with our React toolkit [`@flux0-ai/react`](https://www.npmjs.com/package/@flux0-ai/react).

Whether you're building a chatbot, agent system, or AI copilot — Flux0 provides the foundation.

---

## Key Features

### 🧠 Agnostic AI Agent Orchestration

Deploy and manage agents using frameworks like LangGraph, PydanticAI, or any custom logic — with no lock-in.

### ⚡ Real-Time Streaming

Built-in support for real-time streaming using JSON patches. Perfect for chat UIs, assistants, and continuous agent feedback.

### 📝 Session Management

Track, persist, and replay conversations with full context. Built-in session lifecycle management lets you build stateful experiences.

### 📂 React UI Toolkit

`@flux0-ai/react` helps you build conversational UIs that handle input, messages, system events, and streaming — with minimal setup.

### 🛂 Modular by Design

Extend your app with custom workflows, event logic, or backend modules. Easily adapt Flux0 to your needs.

---

## Why Flux0?

Building modern AI apps means combining many complex systems: LLM APIs, workflows, conversation state, streaming, and UIs. Flux0 unifies these pieces so you can:

- ✔ Focus on logic, not boilerplate
- ✔ Stream data in real-time by default
- ✔ Switch LLM frameworks or providers freely
- ✔ Use prebuilt UI components
- ✔ Prototype fast and scale cleanly

If you've ever struggled with:

- Coordinating multiple agents across sessions
- Persisting chat state across sessions
- Replaying and resuming conversations
- Handling streaming updates in UI
- Building robust, real-time conversational UIs

Then Flux0 is for you.

---

## Who is it for?

- **AI Engineers** who want a reliable backend for agents and workflows
- **Full-Stack Developers** building LLM-powered apps end-to-end
- **Frontend Engineers** who need real-time chat and event UIs
- **Prototypers & Researchers** testing new AI flows quickly
- **Product Teams** shipping production-ready AI features

From experiments to production agents, Flux0 gives you the right tools at every stage.

---

## Getting Started

### 📦 Install via PyPI

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install git+https://github.com/flux0-ai/flux0-client-python
pip install flux0_ai
```

### 🤖 Create Your First Agent

> This agent is based on Langchain but you can use any framework of your choice, see [examples/langchain_simple](https://github.com/flux0-ai/flux0/tree/develop/examples/langchain_simple)

```bash
# install dependencies required by your agent
pip install langchain "langchain[openai]"
mkdir my_agent
# agent's logic
curl https://raw.githubusercontent.com/flux0-ai/flux0/develop/examples/langchain_simple/agent.py -o my_agent/agent.py
# agent module registration
curl https://raw.githubusercontent.com/flux0-ai/flux0/develop/examples/langchain_simple/__init__.py -o my_agent/__init__.py
```

### 🚀 Run the Server

Start the server:

```bash
PYTHONPATH=. FLUX0_MODULES=my_agent OPENAI_API_KEY=<your-key> flux0-server
```

Register the agent in DB (in another window)

```bash
source .venv/bin/activate
flux0 agents create --name assistant --type langchain_simple
```

### 💬 Talk to Your Agent

Start chatting with your agent at [http://localhost:8080/chat](http://localhost:8080/chat)

## Related Packages

- [`@flux0-ai/react`](https://www.npmjs.com/package/@flux0-ai/react): React components and hooks for integrating with Flux0 sessions
- [`flux0-client-python`](https://github.com/flux0-ai/flux0-client-python): Python SDK for managing agents and sessions

## Documentation

Visit the full docs at [flux0.ai/docs](https://flux0.netlify.app/)

- [Quickstart](https://flux0.netlify.app/docs/quickstart/introduction)
- [Examples](https://flux0.netlify.app/docs/category/examples)
- [API Reference](https://flux0.netlify.app//docs/api)

## License

Flux0 is open source and licensed under the [Apache2 License](LICENSE).

---

Made with ❤️ by the Flux0 team
