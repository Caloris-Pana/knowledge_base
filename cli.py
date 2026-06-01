"""CLI entry for knowledge base operations.

All data parameters are passed via JSON files (UTF-8) to avoid PowerShell
pipe encoding issues. Never pass Chinese text via command-line arguments.

Usage:
  python cli.py save --file record.json
  python cli.py list [--limit 20] [--offset 0]
  python cli.py get --id <entry_id>
  python cli.py delete --id <entry_id>
  python cli.py search --file query.json
"""
import sys
import os
import json
import argparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scripts.ingest import add_solution, delete_solution
from scripts.query import search_solutions, list_solutions, get_solution


def cmd_save(args):
    with open(args.file, "r", encoding="utf-8") as f:
        data = json.load(f)
    entry_id = add_solution(
        problem=data["problem"],
        solution=data["solution"],
        tags=data.get("tags", []),
        context=data.get("context", ""),
        cause=data.get("cause", ""),
        detail=data.get("detail", ""),
    )
    print(json.dumps({"status": "saved", "id": entry_id}, ensure_ascii=False))


def cmd_list(args):
    r = list_solutions(limit=args.limit, offset=args.offset)
    print(json.dumps(r, ensure_ascii=False))


def cmd_get(args):
    r = get_solution(args.id)
    if r is None:
        print(json.dumps({"error": "not found"}, ensure_ascii=False))
    else:
        print(json.dumps(r, ensure_ascii=False))


def cmd_delete(args):
    delete_solution(args.id)
    print(json.dumps({"status": "deleted", "id": args.id}, ensure_ascii=False))


def cmd_search(args):
    with open(args.file, "r", encoding="utf-8") as f:
        data = json.load(f)
    r = search_solutions(query=data["query"], top_k=data.get("top_k", 5))
    print(json.dumps(r, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Knowledge Base CLI")
    sub = parser.add_subparsers(dest="command")

    p_save = sub.add_parser("save")
    p_save.add_argument("--file", required=True, help="JSON file with fields: problem, solution, tags, context, cause, detail")

    p_list = sub.add_parser("list")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--offset", type=int, default=0)

    p_get = sub.add_parser("get")
    p_get.add_argument("--id", required=True)

    p_del = sub.add_parser("delete")
    p_del.add_argument("--id", required=True)

    p_search = sub.add_parser("search")
    p_search.add_argument("--file", required=True, help="JSON file with fields: query, top_k")

    args = parser.parse_args()
    if args.command == "save":
        cmd_save(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "get":
        cmd_get(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "search":
        cmd_search(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
