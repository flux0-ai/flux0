# CHANGELOG


## v0.1.0-beta.2 (2025-06-30)

### Bug Fixes

- **server**: Change local server to openapi spec from ip to host
  ([`e7527be`](https://github.com/flux0-ai/flux0/commit/e7527be7757240fff0f6384ea872044feec3028d))

resolves #61

### Chores

- Exclude tests from sdist builds and update static directory path
  ([`5f12d0d`](https://github.com/flux0-ai/flux0/commit/5f12d0dc3c711157ad8a4cf847233d42db08dd59))


## v0.1.0-beta.1 (2025-03-18)

### Bug Fixes

- Expose logger to agent runner deps
  ([`18b83be`](https://github.com/flux0-ai/flux0/commit/18b83be7938cde2fc75c09f1de1767c1f6b45b94))

- **core**: Background Tasks Exceptions Not Logged Until service is released
  ([`1668e04`](https://github.com/flux0-ai/flux0/commit/1668e04b114fa8ce11d42f60326ab57f77fd8659))

resolves #53

- **server**: Add local server to openapi spec
  ([`7aa7823`](https://github.com/flux0-ai/flux0/commit/7aa78232209ebf7e5cb9bcf2d19af08228735e55))

relates to #47

### Chores

- Update version_variables to reflect package structure
  ([`b5f6be9`](https://github.com/flux0-ai/flux0/commit/b5f6be9f1c294a2cf20335b392fb8da51d0982d6))

- **server**: Update openapi spec with title, summary and description
  ([`a4af2b5`](https://github.com/flux0-ai/flux0/commit/a4af2b57ce4bb506bf48cfcccd37db406dcde0dc))

- **server**: Update workspace dependencies [skip ci]
  ([`deeac2b`](https://github.com/flux0-ai/flux0/commit/deeac2b9b9b0c981a007593e69c39772dcd4d005))

### Features

- Create a session
  ([`3b2d90f`](https://github.com/flux0-ai/flux0/commit/3b2d90f9ac4d47b2e86e6009620857a66af64a0e))

resolves #37

- Create event and stream response
  ([`6283003`](https://github.com/flux0-ai/flux0/commit/6283003fccdec739048bee4d1da046925cd0f8b1))

resolves #45

- Expose list session events endpoint and CLI command
  ([`5f4a53f`](https://github.com/flux0-ai/flux0/commit/5f4a53f78f01f367a131b0ecb0e607b9596cb681))

This commit also fixes the list_options CLI decorator to accept extra func args defined on the
  command level via @click.option

resolves #49

- Get a session
  ([`bbe01ac`](https://github.com/flux0-ai/flux0/commit/bbe01ac1ab05a5f6ad52aefb3273d35aa5fcbc68))

resolves #38

- List agents
  ([`854f889`](https://github.com/flux0-ai/flux0/commit/854f8891b83cbf196b7ff476091da80268751508))

resolves #36

- List sessions endpoint
  ([`edfdb33`](https://github.com/flux0-ai/flux0/commit/edfdb33a6b9de83a8e5c4b0abef5d29cfccf1c6c))

resolves #23

- **server**: Allow extra fields in settings configuration
  ([`ca708a9`](https://github.com/flux0-ai/flux0/commit/ca708a98b4f17370375f879731617d9d87be10ee))

- **server**: Initial server, powered by uvicorn and fastapi
  ([`10c2bae`](https://github.com/flux0-ai/flux0/commit/10c2baee036880fb1e787b014f1f794fd3a23740))

resolves #33

- **server**: Serve SPA with fallback to index.html and mount static files
  ([`167fab4`](https://github.com/flux0-ai/flux0/commit/167fab4606ffdbd22745733b217c891cdd7ab621))

resolves #59

- **server**: Support Dynamic Server Modules for Extensibility
  ([`ccd71d0`](https://github.com/flux0-ai/flux0/commit/ccd71d023bb90751868fc002ff2749f275f6d607))

resolves #41
