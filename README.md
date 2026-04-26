# skills

Personal Claude Code skills.

## Install

Install a single skill into `~/.claude/skills/`:

```bash
SKILL=brave-cookies && git clone --depth=1 --filter=blob:none --sparse https://github.com/ampersanda/skills /tmp/_ampskills && (cd /tmp/_ampskills && git sparse-checkout set "$SKILL") && mkdir -p ~/.claude/skills && cp -r "/tmp/_ampskills/$SKILL" ~/.claude/skills/ && rm -rf /tmp/_ampskills
```

Replace `brave-cookies` with the skill name you want.

Install all skills:

```bash
git clone --depth=1 https://github.com/ampersanda/skills /tmp/_ampskills && mkdir -p ~/.claude/skills && cp -r /tmp/_ampskills/*/ ~/.claude/skills/ && rm -rf /tmp/_ampskills
```

## Skills

- [brave-cookies](brave-cookies/) — Reuse your Brave Browser session (macOS) to access authenticated pages from curl / requests / Playwright.

## Conventions

Commits follow [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, etc.
