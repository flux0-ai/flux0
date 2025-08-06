# CHANGELOG


## v0.1.0-beta.2 (2025-08-06)

### Bug Fixes

- **stream**: Initial version of README file
  ([`6f6d92f`](https://github.com/flux0-ai/flux0/commit/6f6d92f54e036866e12e8de645bcecc056dd16a2))

### Chores

- Exclude tests from sdist builds and update static directory path
  ([`5f12d0d`](https://github.com/flux0-ai/flux0/commit/5f12d0dc3c711157ad8a4cf847233d42db08dd59))

- **stream**: Update workspace dependencies [skip ci]
  ([`a9546f1`](https://github.com/flux0-ai/flux0/commit/a9546f19263ab3d6d312e906acf71e9d45b1ecde))


## v0.1.0-beta.1 (2025-03-18)

### Bug Fixes

- **stream**: A helper to (json) loads and dumps events
  ([`ad4b79e`](https://github.com/flux0-ai/flux0/commit/ad4b79e5f3aa6df2737dbb207b3273877fa7d08b))

resolves #48

- **stream**: Do not raise if langchain event is unhandeled
  ([`cf9d40f`](https://github.com/flux0-ai/flux0/commit/cf9d40f7a47aa431de1d35155f72fabe55b01c3b))

- **stream**: Emitter's memory print calls should be replaced with Logger
  ([`21e4249`](https://github.com/flux0-ai/flux0/commit/21e4249eebab632aef74982b64271c2b270da8a9))

resolves #7

- **stream**: Optionally import langchain module as Langchain is an optional package
  ([`638df07`](https://github.com/flux0-ai/flux0/commit/638df07a4a401b9a664f89dde416c1948bb613bc))

resolves #28

### Chores

- Update version_variables to reflect package structure
  ([`b5f6be9`](https://github.com/flux0-ai/flux0/commit/b5f6be9f1c294a2cf20335b392fb8da51d0982d6))

- **stream**: Remove print in code
  ([`4fd60a6`](https://github.com/flux0-ai/flux0/commit/4fd60a65503a66b7ca5a527f761ebf238549d623))

- **stream**: Update workspace dependencies [skip ci]
  ([`f1171b9`](https://github.com/flux0-ai/flux0/commit/f1171b9e4505bcb48a41d41d081af0f963fefbbf))

### Features

- Initial commit
  ([`2e7ff9a`](https://github.com/flux0-ai/flux0/commit/2e7ff9aafc2e2094ea88fa1b95eaa061f94c058a))

- Initialize project layout with core and stream packages. - Add core models (User, Agent, Session)
  along with their stores. - Stream API including Store and Event Emitter. - Memory implementation
  for Stream API.

resolves #1 resolves #2 resolves #5 resolves #6

### Refactoring

- Eventchunk -> ChunkEvent
  ([`dc3edcd`](https://github.com/flux0-ai/flux0/commit/dc3edcdb04e793762104fa21cfeb0b2caec4a44a))
