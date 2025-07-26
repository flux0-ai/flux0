# CHANGELOG


## v0.1.0-beta.3 (2025-07-26)

### Bug Fixes

- Refactor db settings to a single env var using URI
  ([`4fbd928`](https://github.com/flux0-ai/flux0/commit/4fbd9283a52d35e50bb2788dbcb708b0e0ec265c))

For extensibility and best practice, modified DB settings via a single var FLUX0_DB_URI.

Examples:

FLUX0_DB_URI=nanodb://memory FLUX0_DB_URI=nanodb://json?dir=./data
  FLUX0_DB_URI=mongodb://localhost:27017

- Static agent
  ([`ab6bf7b`](https://github.com/flux0-ai/flux0/commit/ab6bf7be130ebe59f867f943fbe927d260d2ed93))

fixes an issue with the static agent where the first message wasn't seen, until after a refresh

- Undefined agent runner
  ([`7519025`](https://github.com/flux0-ai/flux0/commit/7519025daf87f4401c699463ca0cb473811747c6))

- when tryintg to create an agent, check if the agent type exists - server now checks requested
  agent runner type exists before trying to run against it. - ui brings up a toast to indicate
  "agent doesn't exist" error

- **chat**: Remove extra rendered comma
  ([`da9ea72`](https://github.com/flux0-ai/flux0/commit/da9ea722917eb17c3f7a94152ca57dd78d4a43a8))

### Build System

- A GitHub Action for Docker Build & Push with Signing Support
  ([`8fb367f`](https://github.com/flux0-ai/flux0/commit/8fb367f9f4f90b96b2e022e05ef8730ca06c93dc))

resolves #73

- Clarify github action for building docker image
  ([`c3bd3c1`](https://github.com/flux0-ai/flux0/commit/c3bd3c1491ef6c51c2039692602260cabefa8103))

- Set FLUX0_STATIC_DIR env var in docker image
  ([`8684e68`](https://github.com/flux0-ai/flux0/commit/8684e68294fd04a0aefab141a393b2db2c05eddb))

- Use builder image from docker hub
  ([`6db5bbe`](https://github.com/flux0-ai/flux0/commit/6db5bbe1e3eb704007363122c847a322793f39a1))

- **cicd**: Rename docker image repo name flux0-ai -> flux0
  ([`9c30f40`](https://github.com/flux0-ai/flux0/commit/9c30f40f765be50a55a927530066b02663e81a04))

- **docker**: Add python libs folder to PYTHONPATH
  ([`780c969`](https://github.com/flux0-ai/flux0/commit/780c969f7ced642ab914faab41bcfa407320ef72))

### Chores

- Ui package updates
  ([`b62f46d`](https://github.com/flux0-ai/flux0/commit/b62f46d0c42defecaa4a757d89105e5f762c520c))

updates ui packages because of security issues

- Update flux0 package names and versions for consistency via uv sync
  ([`26306b9`](https://github.com/flux0-ai/flux0/commit/26306b9c626eec7709e92fb2b00400af1d995feb))

- Update README with quickstart
  ([`acb64d1`](https://github.com/flux0-ai/flux0/commit/acb64d10d03d51a63268c307cba85bf6fac864b2))

resolves #72

- **chat**: Update package lock file
  ([`4d1000d`](https://github.com/flux0-ai/flux0/commit/4d1000d4a861cd6395d368193e62111b26d50e93))

- **example**: Add LangChain agent runner example with README and implementation
  ([`03c5419`](https://github.com/flux0-ai/flux0/commit/03c541923d60930044d73757cfa7555fcc00ccd6))

- **examples**: Add langgraph weather agent example
  ([`68b59cb`](https://github.com/flux0-ai/flux0/commit/68b59cb3c8dc53ba1b05499ae60e366c219c24cf))

resolves #74

- **root**: Update workspace dependencies [skip ci]
  ([`2b7cf57`](https://github.com/flux0-ai/flux0/commit/2b7cf573f62c177ce70974f70248c8374b911b45))

### Features

- Agent description
  ([`7cbe13f`](https://github.com/flux0-ai/flux0/commit/7cbe13f660a3beb086a0d3162f9102ea8056aa6e))

adds agent description in UI agent card

resolves #87

- Mongodb implementation
  ([`f0c5953`](https://github.com/flux0-ai/flux0/commit/f0c5953223a48cac07be7e7e3e755da5ffc6a85b))

adds a mongodb database implementation

resolves #85


## v0.1.0-beta.2 (2025-06-30)

### Bug Fixes

- **chat**: Update loading state references to processing
  ([`41fb675`](https://github.com/flux0-ai/flux0/commit/41fb675932e5100f3b5c1a374570fc533dfa63b7))

### Chores

- Add a local python index, mainly for testing purposes
  ([`b06ab6e`](https://github.com/flux0-ai/flux0/commit/b06ab6e92ce8ef5daf0ad2de5028a036e0f63bbd))

- Add vs code configuration for server debugging
  ([`c3648fc`](https://github.com/flux0-ai/flux0/commit/c3648fcb8ff8220b0e16613c34ba3d2200a012c4))

- Update .gitignore to include .env and fix tmp entry
  ([`7231840`](https://github.com/flux0-ai/flux0/commit/723184041c0fca07477bfdd3562113361eca33f2))

- **examples**: Add static agent runner for streaming demo
  ([`a568f49`](https://github.com/flux0-ai/flux0/commit/a568f49881cc0f912dd2c9c0821a5d126d49990a))

- **root**: Update workspace dependencies [skip ci]
  ([`a4c70c3`](https://github.com/flux0-ai/flux0/commit/a4c70c38a97ed5353a84768b5ff67a41a2a3ee79))


## v0.1.0-beta.1 (2025-03-18)

### Bug Fixes

- **api**: Lagom container should be optional
  ([`625b9da`](https://github.com/flux0-ai/flux0/commit/625b9dafbae9e324328396b67b600a19285f2c40))

resolves #29

- **chat**: Enable code block
  ([`f463298`](https://github.com/flux0-ai/flux0/commit/f463298e62748fb074b0772c29a868548f40a9f4))

### Build System

- **docker**: Add Dockerfile for application and UI build process
  ([`bf3ad2a`](https://github.com/flux0-ai/flux0/commit/bf3ad2a765c817edb7d03bbed71291687dfe6333))

### Chores

- Expose flux0-server and flux0 (client) in parent project
  ([`505cd71`](https://github.com/flux0-ai/flux0/commit/505cd711e1071bcd5007500f08f5e8d7972d1924))

resolves #35

- License file
  ([`2d4e5cc`](https://github.com/flux0-ai/flux0/commit/2d4e5cc5f39a6d9897549a84ee7c80dc174a80f5))

resolves #8

- Missing __init__.py in root project
  ([`d5b6599`](https://github.com/flux0-ai/flux0/commit/d5b659918fcc70116e0b6c35a9c936987a0da11a))

part of 505cd711e

- Rename project to `flux0-ai` and update dependencies to beta versions
  ([`5f6a7e6`](https://github.com/flux0-ai/flux0/commit/5f6a7e63a378840ae248c0634d553dd47ba28c87))

- Update uv.lock with generated client deps
  ([`b346871`](https://github.com/flux0-ai/flux0/commit/b346871836b62d3dc403fd6ed301372f02d69a5f))

- Update version variable path to reflect project name change
  ([`6d97d67`](https://github.com/flux0-ai/flux0/commit/6d97d6756da5e8277afeef28eb04a17802b639ac))

- **cicd**: Add required PYPI_API_TOKEN secret to release workflows
  ([`d41f4a7`](https://github.com/flux0-ai/flux0/commit/d41f4a7ffed2f2fe412645cc1e1b3532174062b0))

- **cicd**: An attempt to remove id-token causing pypi publishing error
  ([`5fa87e1`](https://github.com/flux0-ai/flux0/commit/5fa87e10ad6e006c7801bda6bc2e072ff32b2b10))

- **cicd**: Remove unnecessary root_options from release workflows causing noop build
  ([`d8d4229`](https://github.com/flux0-ai/flux0/commit/d8d42295237aca215afd046b56a9ae4f9650c746))

- **deps**: Bump @flux0-ai/react from 1.0.0-beta.4 to 1.0.0-beta.5
  ([`c398f99`](https://github.com/flux0-ai/flux0/commit/c398f993131772ad0232f9f7ca3ad34cc7b3da8d))

### Features

- Api package member exposing Event and ChunkEvent DTOs
  ([`dedd91e`](https://github.com/flux0-ai/flux0/commit/dedd91ef10065e583efaf3e6ddfeddb352748da8))

resolves #12

- Auth handler interface with NOOP implementation
  ([`79a2ed4`](https://github.com/flux0-ai/flux0/commit/79a2ed45134fd111b8ddc4c3817a21da0f12582e))

resolves #17

- Initial commit
  ([`2e7ff9a`](https://github.com/flux0-ai/flux0/commit/2e7ff9aafc2e2094ea88fa1b95eaa061f94c058a))

- Initialize project layout with core and stream packages. - Add core models (User, Agent, Session)
  along with their stores. - Stream API including Store and Event Emitter. - Memory implementation
  for Stream API.

resolves #1 resolves #2 resolves #5 resolves #6

- Logging
  ([`9fc72b5`](https://github.com/flux0-ai/flux0/commit/9fc72b548c7cf0f3485f9dbfbbc16ed4d6ff43c1))

a structured logger that is correlational and scopable.

resolves #3

- **chat**: Implement Initial Version of WebChat
  ([`25c6bf5`](https://github.com/flux0-ai/flux0/commit/25c6bf588af3d97b8c723126c83251eb1b83f6b1))

resolves #54

- **chat**: Initial commit of vite + react project
  ([`8d9c850`](https://github.com/flux0-ai/flux0/commit/8d9c8501fd20adfa98863ca2a3f41983db73623b))

- base path set to /chat - proxy /api to server - eslint configured in strict mode - biome for
  formatting

relates to #54

- **chat**: Tailwind 4 plus shadcn
  ([`944850b`](https://github.com/flux0-ai/flux0/commit/944850b68862f06e4fb3bbac7698b053d033db26))

relates to #54

- **cicd**: Add GitHub Actions workflow for testing on pull requests
  ([`cdf1765`](https://github.com/flux0-ai/flux0/commit/cdf17659bf709da7d8d6e2440fba7dd1a4f4206d))

resolves #57

- **cicd**: Add linting workflow for pull requests in GitHub Actions
  ([`1bbff47`](https://github.com/flux0-ai/flux0/commit/1bbff47e8c8ddd7e64da38cde652fc96a14ea1a5))

plus missing scripts/test.py

resolves #10

- **cli**: Add command to list all sessions
  ([`e8f82c1`](https://github.com/flux0-ai/flux0/commit/e8f82c1f42e4b5cdcd1a368cee04fa7e2b1cfa89))

resolves #65

- **core**: Contextual RWLock
  ([`443333b`](https://github.com/flux0-ai/flux0/commit/443333b1608eb3cc8b63291d7f74d4e668ae0536))

resolves #14

- **core**: Human friendly ID generation and a test
  ([`6697e3e`](https://github.com/flux0-ai/flux0/commit/6697e3e26cf887a4203f12952d60907a59d79843))

resolves #11

- **nanodb**: Document db API and memory implementation
  ([`2155b96`](https://github.com/flux0-ai/flux0/commit/2155b96e8ea4a9d0264f4b67859adb1e2ab2b452))

resolves #13

- **server**: Support Dynamic Server Modules for Extensibility
  ([`ccd71d0`](https://github.com/flux0-ai/flux0/commit/ccd71d023bb90751868fc002ff2749f275f6d607))

resolves #41

### Refactoring

- **cicd**: Rename build job to test in GitHub Actions workflow
  ([`b02bc30`](https://github.com/flux0-ai/flux0/commit/b02bc309d35342baba12862b0b0739bc5bf44bc0))

- **cli**: Use client generated in flux0-client repo instead of local one
  ([`54d19cb`](https://github.com/flux0-ai/flux0/commit/54d19cb700bee0cca6d3be7d7844bb52903ea382))

resolves #50
