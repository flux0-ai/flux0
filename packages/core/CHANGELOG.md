# CHANGELOG


## v0.1.0-beta.1 (2025-03-18)

### Bug Fixes

- Deps in AgentRunner run() method
  ([`68bb48d`](https://github.com/flux0-ai/flux0/commit/68bb48d1cc825f67fac8c47826fb0717cd8d4045))

resolves #32

- Expose logger to agent runner deps
  ([`18b83be`](https://github.com/flux0-ai/flux0/commit/18b83be7938cde2fc75c09f1de1767c1f6b45b94))

- Remove ContainerAgentRunnerFactory as it requires Lagom
  ([`0c63ba8`](https://github.com/flux0-ai/flux0/commit/0c63ba8556a6af954d24594bee4606ee19fca858))

Core should not require opinioned dependency injection.

relates #29

- **core**: Background Tasks Exceptions Not Logged Until service is released
  ([`1668e04`](https://github.com/flux0-ai/flux0/commit/1668e04b114fa8ce11d42f60326ab57f77fd8659))

resolves #53

- **core**: Support different logging renderer
  ([`4d93792`](https://github.com/flux0-ai/flux0/commit/4d937923c6b856633c8ca6fe8e2a6fb7684a5b8b))

Support different logging renderer so in dev mode we can use console renderer.

- **core**: Support list_session_events in agent runner deps
  ([`3091bd4`](https://github.com/flux0-ai/flux0/commit/3091bd4607615bcb3fab3f7d026ae71f02bbb03c))

### Chores

- Remove resolved TODO comment
  ([`8185b2b`](https://github.com/flux0-ai/flux0/commit/8185b2bd9239f40d83a463546afadd48f4c86a11))

- Update version_variables to reflect package structure
  ([`b5f6be9`](https://github.com/flux0-ai/flux0/commit/b5f6be9f1c294a2cf20335b392fb8da51d0982d6))

- **core**: Helpful enums for building up settings of stores and auth types
  ([`0e1656a`](https://github.com/flux0-ai/flux0/commit/0e1656ade224ef85c0f7276ad167b29d55e85bbd))

- **core**: Update workspace dependencies [skip ci]
  ([`f69b2e1`](https://github.com/flux0-ai/flux0/commit/f69b2e1912f4f0b3b672ff2248ae0105e7fa1f61))

### Features

- Background tasks service
  ([`05a9d2b`](https://github.com/flux0-ai/flux0/commit/05a9d2beed305dafe08121dfacfaf0182a7fb725))

resolves #16

- Initial commit
  ([`2e7ff9a`](https://github.com/flux0-ai/flux0/commit/2e7ff9aafc2e2094ea88fa1b95eaa061f94c058a))

- Initialize project layout with core and stream packages. - Add core models (User, Agent, Session)
  along with their stores. - Stream API including Store and Event Emitter. - Memory implementation
  for Stream API.

resolves #1 resolves #2 resolves #5 resolves #6

- List agents
  ([`854f889`](https://github.com/flux0-ai/flux0/commit/854f8891b83cbf196b7ff476091da80268751508))

resolves #36

- Logging
  ([`9fc72b5`](https://github.com/flux0-ai/flux0/commit/9fc72b548c7cf0f3485f9dbfbbc16ed4d6ff43c1))

a structured logger that is correlational and scopable.

resolves #3

- User and session stores implementations for nanodb
  ([`d29a59a`](https://github.com/flux0-ai/flux0/commit/d29a59a7239a2a7b7d61514db589cc545408b3f5))

resolves #15 resolves #18

- **api**: Create session endpoint
  ([`0ebd9ea`](https://github.com/flux0-ai/flux0/commit/0ebd9eaf09aca79d27329b7f7b827af93612a441))

resolves #20

- **core**: Add ContextualCorrelator for managing correlation scopes and tests
  ([`acdf95e`](https://github.com/flux0-ai/flux0/commit/acdf95ef5d490401fa99902d4b87ad3d72f8b731))

resolves #4

- **core**: Agent store implementation for nanodb
  ([`01d66a8`](https://github.com/flux0-ai/flux0/commit/01d66a87511c9cfdb01944212b8e7469a319f0c4))

resolves #19

- **core**: Contextual RWLock
  ([`443333b`](https://github.com/flux0-ai/flux0/commit/443333b1608eb3cc8b63291d7f74d4e668ae0536))

resolves #14

- **core**: Human friendly ID generation and a test
  ([`6697e3e`](https://github.com/flux0-ai/flux0/commit/6697e3e26cf887a4203f12952d60907a59d79843))

resolves #11

- **nanodb**: Implement document validation and projection functionality
  ([`71a0201`](https://github.com/flux0-ai/flux0/commit/71a02016350fce9d9e7ab09382bc624bdd16c375))

This commit refactors Protocol to TypedDict for flexibility as dataclasses don't play well with
  partials (suitd for projection)

resolves #21

### Refactoring

- Ilogger -> Logger and Logger -> ContextualLogger
  ([`d96a912`](https://github.com/flux0-ai/flux0/commit/d96a912245bc8fe7c8105aa35dfd36c1eddf0470))

resolves #25
