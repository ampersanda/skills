#!/usr/bin/env python3
"""Extract decrypted cookies from Brave Browser on macOS.

Usage:
    python3 extract_cookies.py <domain_substring> [--profile Default] [--format jar|json|header]

Examples:
    python3 extract_cookies.py elearning.ut.ac.id
    python3 extract_cookies.py github.com --format header
    python3 extract_cookies.py example.com --format jar > cookies.txt   # Netscape format for curl

Requires: pip3 install --user pycryptodomex
"""
import argparse, json, os, shutil, sqlite3, subprocess, sys, tempfile, time
from pathlib import Path

try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Protocol.KDF import PBKDF2
except ImportError:
    sys.stderr.write("Install pycryptodomex: pip3 install --user pycryptodomex\n")
    sys.exit(1)

BRAVE_DIR = Path.home() / "Library/Application Support/BraveSoftware/Brave-Browser"


def keychain_password(service="Brave Safe Storage"):
    # -s selects by service, -w prints password only
    r = subprocess.run(
        ["security", "find-generic-password", "-s", service, "-w"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        sys.stderr.write(
            f"Could not read keychain entry '{service}'. "
            "macOS may prompt for permission the first time.\n"
            f"stderr: {r.stderr}\n"
        )
        sys.exit(2)
    return r.stdout.strip().encode()


def derive_key(password, iterations=1003):
    return PBKDF2(password, b"saltysalt", dkLen=16, count=iterations)


def decrypt(blob, key, host=None):
    if not blob:
        return ""
    if blob[:3] in (b"v10", b"v11"):
        blob = blob[3:]
    iv = b" " * 16
    cipher = AES.new(key, AES.MODE_CBC, iv)
    raw = cipher.decrypt(blob)
    pad = raw[-1]
    if 1 <= pad <= 16:
        raw = raw[:-pad]
    # Chromium >=118 prepends sha256(host_key) (32 bytes) to plaintext for
    # integrity. Strip if the first 32 bytes match.
    if host is not None and len(raw) >= 32:
        import hashlib
        if raw[:32] == hashlib.sha256(host.encode()).digest():
            raw = raw[32:]
    return raw.decode("utf-8", errors="replace")


def extract(domain, profile="Default"):
    src = BRAVE_DIR / profile / "Cookies"
    if not src.exists():
        sys.stderr.write(f"Cookie DB not found: {src}\n")
        sys.exit(2)

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        shutil.copy(src, tmp.name)
        db = tmp.name

    try:
        key = derive_key(keychain_password())
        conn = sqlite3.connect(db)
        rows = conn.execute(
            """SELECT host_key, name, encrypted_value, path,
                      expires_utc, is_secure, is_httponly
               FROM cookies WHERE host_key LIKE ?""",
            (f"%{domain}%",),
        ).fetchall()
        conn.close()

        out = []
        for host, name, enc, path, exp, secure, httponly in rows:
            try:
                value = decrypt(enc, key, host)
            except Exception as e:
                sys.stderr.write(f"decrypt failed for {host}/{name}: {e}\n")
                continue
            # Chromium epoch: microseconds since 1601-01-01
            unix_exp = 0
            if exp:
                unix_exp = int(exp / 1_000_000 - 11644473600)
            out.append({
                "domain": host,
                "name": name,
                "value": value,
                "path": path,
                "expires": unix_exp,
                "secure": bool(secure),
                "httponly": bool(httponly),
            })
        return out
    finally:
        os.unlink(db)


def fmt_jar(cookies):
    # Netscape cookie file format (compatible with curl -b/--cookie)
    lines = ["# Netscape HTTP Cookie File"]
    for c in cookies:
        domain = c["domain"]
        flag = "TRUE" if domain.startswith(".") else "FALSE"
        secure = "TRUE" if c["secure"] else "FALSE"
        lines.append("\t".join([
            domain, flag, c["path"], secure,
            str(c["expires"] or 0), c["name"], c["value"],
        ]))
    return "\n".join(lines) + "\n"


def fmt_header(cookies):
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("domain", help="domain substring, e.g. example.com")
    p.add_argument("--profile", default="Default")
    p.add_argument("--format", choices=["json", "jar", "header"], default="json")
    args = p.parse_args()

    cookies = extract(args.domain, args.profile)
    if args.format == "json":
        print(json.dumps(cookies, indent=2))
    elif args.format == "jar":
        sys.stdout.write(fmt_jar(cookies))
    else:
        print(fmt_header(cookies))


if __name__ == "__main__":
    main()
