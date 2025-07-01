# Flux0 LangChain Simple Example

This example demonstrates a minimal agent runner integration using Flux0 with the [LangChain](https://www.langchain.com/) framework to stream a translation from English to Italian using OpenAI model.

## Overview

The agent:

- Extracts user input from the session event stream.
- Sends the input to a LangChain chat model initialized with a translation prompt.
- Streams the output events back to the client in real time.

## Key Components

### `LangChainAgentRunner`

A simple agent runner that does the following:

1. Retrieves the latest user message from the session.
2. Initializes a LangChain chat model.
3. Sends a translation prompt along with the user's input.
4. Streams model events to the client.

## Requirements

- Dependencies: `langchain` and `langchain[openai]`.
- `OPENAPI_KEY` env var set.

## Usage

Ensure the agent is defined by:

```bash
flux0 agents create --name langchain --type langchain_simple
```
