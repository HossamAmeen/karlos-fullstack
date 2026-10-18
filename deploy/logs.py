#!/usr/bin/env python3
"""Show logs from the server: the backend service (journalctl / docker compose) or nginx."""
import argparse
import shlex
import subprocess
import sys

import deploy
from deploy import Server, load_config


def main():
    parser = argparse.ArgumentParser(description="Show backend service or nginx logs from the server.")
    parser.add_argument("target", choices=("service", "nginx"))
    parser.add_argument("environment", nargs="?", choices=deploy.ENVIRONMENTS, default="staging")
    parser.add_argument("-n", "--lines", type=int, default=100)
    parser.add_argument("-f", "--follow", action="store_true", help="stream new lines (Ctrl+C to stop)")
    parser.add_argument("-e", "--errors", action="store_true", help="only errors (journalctl -p err / error.log / lines matching error)")
    args = parser.parse_args()

    cfg = load_config(args.environment)
    srv = Server(cfg)
    name = shlex.quote(cfg["backend"]["service_name"])
    follow = "-f" if args.follow else ""
    if args.target == "nginx":
        files = "/var/log/nginx/error.log" if args.errors else "/var/log/nginx/error.log /var/log/nginx/access.log"
        cmd = f"sudo tail -n {args.lines} {follow} {files}"
    elif cfg.get("docker"):
        path = shlex.quote(deploy.app_dir(cfg["backend"]))
        cmd = f"cd {path} && sudo docker compose -p {name} logs --tail {args.lines} {follow}"
        if args.errors:
            cmd += " 2>&1 | grep -iE 'error|exception|traceback|critical'"
    else:
        level = "-p err" if args.errors else ""
        cmd = f"sudo journalctl -u {name} {level} -n {args.lines} {follow} --no-pager"
    try:
        subprocess.run(["ssh", "-t", *srv.ssh_opts, srv.target, cmd])
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
