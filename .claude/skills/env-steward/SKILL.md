---
name: env-steward
description: Keep env-space and .env.example accurate whenever integrations are added or removed.
---

# Env Steward

## When to use
Any PR that adds, removes, or changes an integration, external API, or
configuration knob.

## Procedure
1. Grep for new env reads: `grep -rn "environ\|env=" backend/app/config.py
   backend/app scripts | grep -iv test`. Every env var the code reads must
   appear in BOTH env-space and .env.example.
2. For each variable, env-space must state all eight: name, required or
   optional, what it does, when it's needed, how to get it, provider docs
   link, example placeholder, and the never-commit-secrets warning applies
   file-wide.
3. .env.example gets a placeholder that CANNOT be mistaken for a real
   secret (`your-x-key-here`, empty, or `false`).
4. If a variable is not needed for the MVP demo, mark it optional and name
   the exact feature that unlocks it.
5. Remove docs for variables no code reads anymore (stale docs are lies).
6. Run `make check-env` and update scripts/check_env.py's OPTIONAL_VARS
   list if a new variable deserves visibility there.

## Invariant
`make demo` requires zero env vars. Any change that breaks this needs a
principal-architect sign-off and a decisions.md entry.
