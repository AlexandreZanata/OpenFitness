#!/usr/bin/env python3
"""NutriOffline CLI — offline nutrition assistant (Phase 7 + mobile)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from orchestrator import NutriAssistant


def print_response(result, *, debug: bool) -> None:
    print(f"\nAnswer [{result.mode}] ({result.latency_ms:.0f} ms):\n{result.answer}\n")
    sources = getattr(result, "sources", None) or []
    if sources:
        print("Sources:")
        for source in sources:
            print(f"  - [{source['source']}] {source['name']} (score={source['score']})")
    rag_context = getattr(result, "rag_context", "")
    if debug and rag_context:
        print("\nRAG context:")
        print(rag_context)
    debug_info = getattr(result, "debug", None)
    if debug and debug_info:
        estimate = debug_info.get("prompt_tokens_estimate")
        if estimate is not None:
            print(f"\nDebug: prompt ~{estimate} tokens")


def main() -> int:
    parser = argparse.ArgumentParser(description="NutriOffline offline nutrition assistant")
    sub = parser.add_subparsers(dest="command")

    ask_parser = sub.add_parser("ask", help="Ask a single question")
    ask_parser.add_argument("question", help="Question in PT-BR")
    ask_parser.add_argument("--top-k", type=int, default=5)
    ask_parser.add_argument("--debug", action="store_true")
    ask_parser.add_argument("--no-rag", action="store_true")
    ask_parser.add_argument("--json", action="store_true")
    ask_parser.add_argument(
        "--runtime",
        choices=("desktop", "mobile"),
        default="desktop",
        help="Runtime: desktop (LanceDB + optional LLM) or mobile pack",
    )
    ask_parser.add_argument(
        "--mode",
        choices=("auto", "lookup", "llm"),
        default="auto",
        help="Desktop response path (ignored for --runtime mobile)",
    )

    repl_parser = sub.add_parser("repl", help="Interactive session")
    repl_parser.add_argument("--top-k", type=int, default=5)
    repl_parser.add_argument("--debug", action="store_true")
    repl_parser.add_argument("--no-rag", action="store_true")

    health_parser = sub.add_parser("health", help="Check RAG index and llama-server")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1

    if args.command == "health":
        assistant = NutriAssistant()
        status = assistant.health()
        print(json.dumps(status, indent=2))
        return 0 if all(status.values()) else 1

    if args.command == "repl":
        assistant = NutriAssistant()
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
            result = assistant.ask(
                question,
                top_k=args.top_k,
                use_rag=not args.no_rag,
                debug=args.debug,
            )
            print_response(result, debug=args.debug)

    if getattr(args, "runtime", "desktop") == "mobile":
        mobile_dir = Path(__file__).resolve().parents[1] / "mobile"
        sys.path.insert(0, str(mobile_dir))
        from mobile_assistant import MobileNutriAssistant  # noqa: E402

        result = MobileNutriAssistant().ask(
            args.question,
            top_k=args.top_k,
            debug=args.debug,
        )
    else:
        assistant = NutriAssistant()
        result = assistant.ask(
            args.question,
            top_k=args.top_k,
            use_rag=not args.no_rag,
            debug=args.debug,
            mode=args.mode,
        )

    if args.json:
        payload = {
            "answer": result.answer,
            "sources": result.sources,
            "model": result.model,
            "latency_ms": result.latency_ms,
            "mode": result.mode,
        }
        if hasattr(result, "rag_context_used"):
            payload["rag_context_used"] = result.rag_context_used
        if args.debug and hasattr(result, "debug"):
            payload["debug"] = result.debug
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print_response(result, debug=args.debug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
