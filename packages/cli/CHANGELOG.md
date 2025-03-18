# CHANGELOG


## v0.1.0-beta.1 (2025-03-18)

### Bug Fixes

- **cli**: Jsonpath should not return an array for a single value
  ([`f5376a8`](https://github.com/flux0-ai/flux0/commit/f5376a8af583719fa981c0736b7c5ad3c1b5c8d2))

### Chores

- Update version_variables to reflect package structure
  ([`b5f6be9`](https://github.com/flux0-ai/flux0/commit/b5f6be9f1c294a2cf20335b392fb8da51d0982d6))

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

- Introduce CLI Package to Interact with Server
  ([`c196ce8`](https://github.com/flux0-ai/flux0/commit/c196ce8e53174b54d5e3940a2e0f66e53fdec2fc))

Create, get and a stub of list agents.

resolves #34

- List agents
  ([`854f889`](https://github.com/flux0-ai/flux0/commit/854f8891b83cbf196b7ff476091da80268751508))

resolves #36

- **cli**: Add command to list all sessions
  ([`e8f82c1`](https://github.com/flux0-ai/flux0/commit/e8f82c1f42e4b5cdcd1a368cee04fa7e2b1cfa89))

resolves #65

### Refactoring

- **cli**: Convert cli to work with SpeakEasy instead of Fern
  ([`f218e18`](https://github.com/flux0-ai/flux0/commit/f218e185dceac03bac0c35800e9f2921ec53827b))

resolves #46

- **cli**: Use client generated in flux0-client repo instead of local one
  ([`54d19cb`](https://github.com/flux0-ai/flux0/commit/54d19cb700bee0cca6d3be7d7844bb52903ea382))

resolves #50
