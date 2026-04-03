# Gitea Environments

You have access to `amplifier-gitea`, a CLI for on-demand ephemeral Gitea Docker environments. Use it for isolated git workflows, safe experimentation, and GitHub mirroring/promoting.

## When to Use

- User needs an isolated git environment (experiments, testing, demos)
- User wants to mirror a GitHub repo, work freely, then promote changes back as a PR
- User needs a disposable git server with issues, PRs, and API access

## How to Use

You MUST load the `gitea` skill as a FIRST STEP.
It will tell you the necessary prerequisites, installation instructions, CLI documentation, workflows, and troubleshooting:

```
load_skill(skill_name="gitea")
```

If you DO NOT load this skill, you will FAIL and let the user down :'(
