---
name: brave-cookies
description: Reuse the user's logged-in session from Brave Browser (macOS) to access pages that require authentication. Use when the user asks to "use cookie from brave", access an authenticated page (their LMS, internal dashboard, paid forum, GitHub private page, etc.), or scrape something that needs to stay signed in. Decrypts the Brave cookie store and emits a cookie jar that curl/wget/requests/Playwright can consume. macOS-only — uses Keychain.
---

# Brave Cookies (macOS)

Decrypts cookies from the local Brave profile so the user's authenticated session can be reused with curl, requests, or Playwright. Avoids re-entering credentials and 2FA.

## When to use

- The user said "use cookie from brave" / "use my login" / "I'm already signed in".
- A target URL redirects to a login page when fetched anonymously.
- Scraping content from sites the user is logged into (LMS, internal tools, private GitHub pages).
- **Don't** use for sites the user is not already signed into in Brave — extraction will return zero useful cookies.

## Prerequisites

- macOS (Brave keeps the AES key in `login.keychain-db`).
- Python 3 with `pycryptodomex` — install once: `pip3 install --user pycryptodomex`.
- The target site has been logged into in Brave at least once. Quit Brave before extraction is **not** required (DB is copied to a tempfile).

## Quick usage

```bash
# 1. Extract cookies as a Netscape jar (compatible with curl -b)
python3 ~/.claude/skills/brave-cookies/extract_cookies.py example.com --format jar > /tmp/cookies.txt

# 2. Use with curl
curl -s -b /tmp/cookies.txt -A "Mozilla/5.0" "https://example.com/protected" -L -o /tmp/page.html

# 3. Or get a single Cookie header value
COOKIE=$(python3 ~/.claude/skills/brave-cookies/extract_cookies.py example.com --format header)
curl -H "Cookie: $COOKIE" "https://example.com/api/something"

# 4. Or JSON for Python/Node consumers
python3 ~/.claude/skills/brave-cookies/extract_cookies.py example.com --format json
```

## How it works

- Brave on macOS encrypts cookie values with AES-128-CBC. The key is PBKDF2-SHA1 (1003 iters, salt `saltysalt`) from a password stored in Keychain under service **"Brave Safe Storage"**.
- Modern Brave (≥ Chromium 118) prepends `sha256(host_key)` to the plaintext for integrity. The script strips it automatically.
- The Cookies SQLite DB is copied to a tempfile so a running Brave doesn't block the read.
- The first decryption may trigger a macOS Keychain consent prompt — once approved ("Always Allow"), subsequent runs are silent.

## Common pitfalls

- **"could not be found in the keychain"** — query is wrong. Use `security find-generic-password -s "Brave Safe Storage" -w` (NOT `-a`). The script handles this.
- **Garbage prefix in cookie values** — means SHA256 host-prefix wasn't stripped. Verify the script passes `host` to `decrypt`.
- **Different profile** — pass `--profile "Profile 2"` if user uses a non-default Brave profile.
- **`v20`/App-Bound Encryption** — Chromium ≥ 127 introduced ABE on Windows; on macOS Brave still uses Keychain (`v10`). If you ever see `v20` prefixes, this script does **not** handle them.
- **Playwright MCP can't easily inject cookies** — prefer curl/requests for fetches; only fall back to a fresh Playwright login when you need JS rendering or to interact.

## Security notes

- The decrypted values include session tokens. Treat output files as secrets — write to `/tmp` and delete after use, or pipe directly into curl.
- Don't commit cookie jars to git, paste them in chat, or upload to third-party services.
- The script never writes the Keychain password — it's used only in-memory to derive the AES key.

## Files

- `extract_cookies.py` — the decryption tool.
