#!/usr/bin/env python3
"""NutriOffline CLI — offline nutrition assistant (Phase 7)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from orchestrator import NutriAssistant


def print_response(result, *, debug: bool) -> None:
    print(f"\nAnswer ({result.latency_ms:.0f} ms):\n{result.answer}\n")
    if result.sources:
        print("Sources:")
        for source in result.sources:
            print(f"  - [{source['source']}] {source['name']} (score={source['score']})")
    if debug and result.rag_context:
        print("\nRAG context:")
        print(result.rag_context)
    if debug and result.debug:
        print(f"\nDebug: prompt ~{result.debug.get('prompt_tokens_estimate')} tokens")


def run_repl(assistant: NutriAssistant, *, top_k: int, debug: bool, use_rag: bool) -> int:
    print("NutriOffline REPL — type 'exit' to quit")
    while True:
        try:
            question = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            return 0
        result = assistant.ask(question, top_k=top_k, use_rag=use_rag, debug=debug)
        print_response(result, debug=debug)


def main() -> int:
    parser = argparse.ArgumentParser(description="NutriOffline offline nutrition assistant")
    sub = parser.add_subparsers(dest="command")

    ask_parser = sub.add_parser("ask", help="Ask a single question")
    ask_parser.add_argument("question", help="Question in PT-BR")
    ask_parser.add_argument("--top-k", type=int, default=5)
    ask_parser.add_argument("--debug", action="store_true")
    ask_parser.add_argument("--no-rag", action="store_true")
    ask_parser.add_argument("--json", action="store_true")

    repl_parser = sub.add_parser("repl", help="Interactive session")
    repl_parser.add_argument("--top-k", type=int, default=5)
    repl_parser.add_argument("--debug", action="store_true")
    repl_parser.add_argument("--no-rag", action="store_true")

    health_parser = sub.add_parser("health", help="Check RAG index and llama-server")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    assistant = NutriAssistant()

    if args.command == "health":
        status = assistant.health()
        print(json.dumps(status, indent=2))
        return 0 if all(status.values()) else 1

    if args.command == "repl":
        return run_repl(
            assistant,
            top_k=args.top_k,
            debug=args.debug,
            use_rag=not args.no_rag,
        )

    result = assistant.ask(
        args.question,
        top_k=args.top_k,
        use_rag=not args.no_rag,
        debug=args.debug,
    )

    if args.json:
        payload = {
            "answer": result.answer,
            "sources": result.sources,
            "rag_context_used": result.rag_context_used,
            "model": result.model,
            "latency_ms": result.latency_ms,
        }
        if args.debug:
            payload["rag_context"] = result.rag_context
            payload["debug"] = result.debug
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print_response(result, debug=args.debug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
