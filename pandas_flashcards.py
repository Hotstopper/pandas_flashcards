#!/usr/bin/env python3
import random
import textwrap
from pathlib import Path
import sys

DEFAULT_DECK = "pandas_cards.txt"
SEPARATOR = ":::"

HELP_TEXT = """Commands after seeing the correct answer:
  Enter  - move to next card
  g      - mark as 'got it' (counts as correct)
  s      - mark as 'struggled' (card will come back later)
  q      - quit
  h      - show this help
"""


def load_cards(path: str):
    """
    Load cards from a text file.

    Format per line:
        front {SEPARATOR} back

    - One card per line
    - Lines starting with '#' are ignored
    - Empty lines are ignored
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Deck file not found: {p.resolve()}")

    cards = []
    with p.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            if line.lstrip().startswith("#"):
                continue

            if SEPARATOR not in line:
                print(f"[WARN] Skipping line {line_no}: missing separator '{SEPARATOR}'")
                continue

            front, _, back = line.partition(SEPARATOR)
            front = front.strip()
            back = back.strip()
            if not front or not back:
                print(f"[WARN] Skipping line {line_no}: empty front/back")
                continue

            cards.append({"front": front, "back": back})

    if not cards:
        raise ValueError(f"No cards loaded from {p}")

    return cards


def print_question(card):
    print("-" * 80)
    print("Q:", card["front"])
    print("-" * 80)


def print_answer(user_answer, card):
    print("-" * 80)
    if user_answer.strip():
        print("Your answer:")
        print(textwrap.indent(user_answer, "    "))
        print()
    print("Correct answer:")
    print(textwrap.indent(card["back"], "    "))
    print("-" * 80)


def run_quiz(cards):
    indices = list(range(len(cards)))
    random.shuffle(indices)

    correct = 0
    total_seen = 0
    quitting = False

    print("pandas flashcards – CLI trainer")
    print(f"Loaded {len(cards)} cards.")
    print(HELP_TEXT)

    i = 0
    while i < len(indices) and not quitting:
        idx = indices[i]
        card = cards[idx]

        # 1. Show question
        print_question(card)

        # 2. User types answer (one line)
        user_answer = input("Your answer (or just Enter to reveal) > ")

        # 3. Show model answer
        print_answer(user_answer, card)

        # 4. Self-mark loop
        while True:
            cmd = input("[Enter = next, g = good, s = struggled, q = quit, h = help] > ").strip().lower()
            if cmd == "":
                total_seen += 1
                break
            elif cmd == "g":
                correct += 1
                total_seen += 1
                break
            elif cmd == "s":
                total_seen += 1
                # push this card to the end of the queue
                indices.append(idx)
                break
            elif cmd == "q":
                quitting = True
                break
            elif cmd == "h":
                print(HELP_TEXT)
            else:
                print("Unknown command. Use Enter/g/s/q/h.")

        i += 1

    print("\nSession summary:")
    print(f"  Cards seen: {total_seen}")
    print(f"  Marked 'got it': {correct}")
    if total_seen:
        pct = 100.0 * correct / total_seen
        print(f"  Accuracy: {pct:.1f}%")
    print("Edit the deck file to add/remove cards and rerun to keep drilling.")


def main():
    if len(sys.argv) > 1:
        deck_path = sys.argv[1]
    else:
        deck_path = DEFAULT_DECK

    try:
        cards = load_cards(deck_path)
    except Exception as e:
        print(f"Error loading deck: {e}")
        sys.exit(1)

    run_quiz(cards)


if __name__ == "__main__":
    main()