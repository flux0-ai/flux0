# CHANGELOG


## v0.1.0-beta.3 (2025-08-06)

### Bug Fixes

- **api**: Update workspace dependencies
  ([`475c714`](https://github.com/flux0-ai/flux0/commit/475c71426a7bc2ef0f9efa3394955f99eda4e665))


## v0.1.0-beta.2 (2025-07-19)

### Bug Fixes

- Undefined agent runner
  ([`7519025`](https://github.com/flux0-ai/flux0/commit/7519025daf87f4401c699463ca0cb473811747c6))

- when tryintg to create an agent, check if the agent type exists - server now checks requested
  agent runner type exists before trying to run against it. - ui brings up a toast to indicate
  "agent doesn't exist" error

### Chores

- Exclude tests from sdist builds and update static directory path
  ([`5f12d0d`](https://github.com/flux0-ai/flux0/commit/5f12d0dc3c711157ad8a4cf847233d42db08dd59))

- **api**: Update workspace dependencies [skip ci]
  ([`13346a5`](https://github.com/flux0-ai/flux0/commit/13346a50d833145f147ac3b43ee9842ad26c93ad))


## v0.1.0-beta.1 (2025-03-18)

### Bug Fixes

- Deps in AgentRunner run() method
  ([`68bb48d`](https://github.com/flux0-ai/flux0/commit/68bb48d1cc825f67fac8c47826fb0717cd8d4045))

resolves #32

- Describe EmittedEvent and ChunkEvent in streaming API correctly
  ([`c83853f`](https://github.com/flux0-ai/flux0/commit/c83853fca28c1e115fb6cde08fcc4c2c29b8f94e))

resolves #43

- Expose logger to agent runner deps
  ([`18b83be`](https://github.com/flux0-ai/flux0/commit/18b83be7938cde2fc75c09f1de1767c1f6b45b94))

- **api**: Conform core StautsEventData optional acknowledged_offset
  ([`d2cd57c`](https://github.com/flux0-ai/flux0/commit/d2cd57cd73ed7d759f56abf2210347a97bb06765))

- **api**: Custom operation id for speakeasy
  ([`67fa320`](https://github.com/flux0-ai/flux0/commit/67fa3200016abc4f046175faeff576d3146bfaa6))

resolves #47

- **api**: Define operation_id in create agent endpoint
  ([`89124d8`](https://github.com/flux0-ai/flux0/commit/89124d8a0aee7d0d57e095700f6b06c4561cb8aa))

- **api**: Lagom container should be optional
  ([`625b9da`](https://github.com/flux0-ai/flux0/commit/625b9dafbae9e324328396b67b600a19285f2c40))

resolves #29

- **api**: Lost Events Due to Premature Background Processing in "create and stream" endpoint
  ([`dbc6101`](https://github.com/flux0-ai/flux0/commit/dbc6101fc38e856c0818f199e2b982c2fbc6a17a))

resolves #52

- **api**: Minor endpoints and schema corrections
  ([`0c97278`](https://github.com/flux0-ai/flux0/commit/0c972785f5f7576caf4505a46e633ef151ee81a9))

- **api**: Set operation_id for create session and list session events
  ([`bbef375`](https://github.com/flux0-ai/flux0/commit/bbef375984248c57e3c529de5e6760bccb9fe974))

- **api**: Strip DTOs from enums title schema
  ([`69bc3bd`](https://github.com/flux0-ai/flux0/commit/69bc3bdbac04598e09f9a5ad4f97451184c73ede))

resolves #42

- **api/test**: Fix SSE event processing handling in consume_streaming_response
  ([`a11f3c2`](https://github.com/flux0-ai/flux0/commit/a11f3c2329f7c1e7abe7204b1a51427248774ab8))

### Chores

- Update version_variables to reflect package structure
  ([`b5f6be9`](https://github.com/flux0-ai/flux0/commit/b5f6be9f1c294a2cf20335b392fb8da51d0982d6))

- **api**: Update workspace dependencies [skip ci]
  ([`f1007e0`](https://github.com/flux0-ai/flux0/commit/f1007e08b977e729f63eaa92a68c4fc4df26eb75))

- **core**: Helpful enums for building up settings of stores and auth types
  ([`0e1656a`](https://github.com/flux0-ai/flux0/commit/0e1656ade224ef85c0f7276ad167b29d55e85bbd))

### Features

- Api package member exposing Event and ChunkEvent DTOs
  ([`dedd91e`](https://github.com/flux0-ai/flux0/commit/dedd91ef10065e583efaf3e6ddfeddb352748da8))

resolves #12

- Auth handler interface with NOOP implementation
  ([`79a2ed4`](https://github.com/flux0-ai/flux0/commit/79a2ed45134fd111b8ddc4c3817a21da0f12582e))

resolves #17

- Get session endpoint
  ([`73cb69a`](https://github.com/flux0-ai/flux0/commit/73cb69abcc9da3793bbcc3b0dd38d9606fb7c162))

resolves #24

- List agents
  ([`854f889`](https://github.com/flux0-ai/flux0/commit/854f8891b83cbf196b7ff476091da80268751508))

resolves #36

- List session events endpoint
  ([`3bc7fda`](https://github.com/flux0-ai/flux0/commit/3bc7fda1625ef2c0f8bdacb958f90b714f10ccdf))

resolves #27

- List sessions endpoint
  ([`edfdb33`](https://github.com/flux0-ai/flux0/commit/edfdb33a6b9de83a8e5c4b0abef5d29cfccf1c6c))

resolves #23

- **api**: Create agent endpoint
  ([`7a245a1`](https://github.com/flux0-ai/flux0/commit/7a245a11540b9b692b4723bead9d15a866be1e57))

resolves #30

- **api**: Create session endpoint
  ([`0ebd9ea`](https://github.com/flux0-ai/flux0/commit/0ebd9eaf09aca79d27329b7f7b827af93612a441))

resolves #20

- **api**: Get agent endpoint
  ([`16d198e`](https://github.com/flux0-ai/flux0/commit/16d198ed72bb7c6e567a7b7f2c0472ed976aa426))

resolves #31

- **api**: Session user event API with streaming endpoint
  ([`e6384e9`](https://github.com/flux0-ai/flux0/commit/e6384e95cf7a353de5d33857b5eddf271c6e57af))

resolves #26

### Refactoring

- Ilogger -> Logger and Logger -> ContextualLogger
  ([`d96a912`](https://github.com/flux0-ai/flux0/commit/d96a912245bc8fe7c8105aa35dfd36c1eddf0470))

resolves #25

- **api**: Change endpoint method name
  ([`dc7eb0c`](https://github.com/flux0-ai/flux0/commit/dc7eb0c57e898c508f44420fd250d400d283b789))

this affects the openapi operation summary

- **api**: Minor agent endpoints renames and docs
  ([`5ab6d12`](https://github.com/flux0-ai/flux0/commit/5ab6d128bdfdb8bc5874a4b028cfabbf6c0ae3a2))
