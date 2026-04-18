"""Shared test output helpers."""

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


def header(title: str):
    print(f"\n{'='*60}")
    print(f"{CYAN}  TESTING: {title}{RESET}")
    print(f"{'='*60}")


def passed(msg: str):
    print(f"  {GREEN}[PASS]{RESET} — {msg}")


def failed(msg: str):
    print(f"  {RED}[FAIL]{RESET} — {msg}")
