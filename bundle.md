---
bundle:
  name: gitea
  version: 0.1.0
  description: Ephemeral Gitea Docker environments for isolated git workflows

includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main
  - bundle: gitea:behaviors/gitea
---
