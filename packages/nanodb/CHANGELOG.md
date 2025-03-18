# CHANGELOG


## v0.1.0-beta.1 (2025-03-18)

### Chores

- Update version_variables to reflect package structure
  ([`b5f6be9`](https://github.com/flux0-ai/flux0/commit/b5f6be9f1c294a2cf20335b392fb8da51d0982d6))

### Features

- **nanodb**: Add Support in Find for Limit & Offset
  ([`9f0a9e4`](https://github.com/flux0-ai/flux0/commit/9f0a9e4fe0f3af4ec24e8ff38bd6449e283b936b))

resolves #22

- **nanodb**: Document db API and memory implementation
  ([`2155b96`](https://github.com/flux0-ai/flux0/commit/2155b96e8ea4a9d0264f4b67859adb1e2ab2b452))

resolves #13

- **nanodb**: Implement document validation and projection functionality
  ([`71a0201`](https://github.com/flux0-ai/flux0/commit/71a02016350fce9d9e7ab09382bc624bdd16c375))

This commit refactors Protocol to TypedDict for flexibility as dataclasses don't play well with
  partials (suitd for projection)

resolves #21
