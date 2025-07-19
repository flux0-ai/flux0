# CHANGELOG


## v0.1.0-beta.3 (2025-07-19)

### Features

- Json persistence nanodb
  ([`357fc94`](https://github.com/flux0-ai/flux0/commit/357fc943c879c18344a58e14e2914be294802a2b))

implements a json based persistence for nanodb moves the locking mechanism from the store level
  (UserStore, AgentStore) to the DB level

resolves #51

- Mongodb implementation
  ([`f0c5953`](https://github.com/flux0-ai/flux0/commit/f0c5953223a48cac07be7e7e3e755da5ffc6a85b))

adds a mongodb database implementation

resolves #85


## v0.1.0-beta.2 (2025-06-30)

### Bug Fixes

- **nanodb**: Add Sorting Support to find method in Collection
  ([`3c0b4a7`](https://github.com/flux0-ai/flux0/commit/3c0b4a7d7b11517e265a38e4c4b1d74a23e1c677))

resolves #69

### Chores

- Exclude tests from sdist builds and update static directory path
  ([`5f12d0d`](https://github.com/flux0-ai/flux0/commit/5f12d0dc3c711157ad8a4cf847233d42db08dd59))

### Features

- **nanodb**: Implement update_one method for DocumentCollection
  ([`3d1d7cf`](https://github.com/flux0-ai/flux0/commit/3d1d7cf3202ddbca4119f0e54bbcd66cf4824587))

resolves #68


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
