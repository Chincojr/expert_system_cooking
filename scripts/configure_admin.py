"""Create a local admin secret, optionally copy it to one Railway service.

The token is retained in the ignored .env file and never printed.
Existing .env files are preserved and must contain a usable token.
"""
import argparse
import os
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def ensure_token():
    path = ROOT / ".env"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("RULES_ADMIN_TOKEN="):
                token = line.partition("=")[2].strip().strip("\"'")
                if len(token) >= 32:
                    return token
        raise SystemExit("Existing .env was preserved. Set a strong RULES_ADMIN_TOKEN there before continuing.")
    token = secrets.token_urlsafe(32)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write("RULES_ADMIN_TOKEN=" + token + "\n")
    return token


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project")
    parser.add_argument("--environment")
    parser.add_argument("--service")
    args = parser.parse_args()
    scope = (args.project, args.environment, args.service)
    if any(scope) and not all(scope):
        parser.error("Provide project, environment and service together")
    token = ensure_token()
    print("Admin token is stored in the ignored .env file; its value has not been printed.")
    if all(scope):
        result = subprocess.run([
            "railway", "variable", "set", "RULES_ADMIN_TOKEN", "--stdin",
            "--project", args.project, "--environment", args.environment,
            "--service", args.service, "--skip-deploys",
        ], input=token, text=True, capture_output=True, env={
            **os.environ, "RAILWAY_CALLER": "skill:use-railway@1.4.0",
            "RAILWAY_AGENT_SESSION": "expertcook-audit-deploy",
        })
        if result.returncode:
            raise SystemExit((result.stderr or result.stdout).replace(token, "[REDACTED]"))
        print("Admin token configured on the specified Railway service. Redeploy to activate it.")


if __name__ == "__main__":
    main()
