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
        or
        front {SEPARATOR} back {SEPARATOR} topic1, topic2, ...

    - One card per line
    - Lines starting with '#' are treated as *section headers* and used as topics
      for subsequent cards until the next header.
    - Empty lines are ignored.

    Returns list of dicts:
        {"front": str, "back": str, "topics": List[str]}
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Deck file not found: {p.resolve()}")

    cards = []
    current_section = None  # header like "Indexing / selection"

    with p.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            raw = line.rstrip("\n")
            stripped = raw.strip()

            if not stripped:
                continue

            # Section header -> update current_section, no card here
            if stripped.startswith("#"):
                # e.g. "# Indexing / selection" -> "Indexing / selection"
                current_section = stripped.lstrip("#").strip()
                continue

            # Non-header line must contain SEPARATOR
            if SEPARATOR not in raw:
                print(f"[WARN] Skipping line {line_no}: missing separator '{SEPARATOR}'")
                continue

            # Split into front, back, optional extra topic string
            parts = [part.strip() for part in raw.split(SEPARATOR)]
            if len(parts) < 2:
                print(f"[WARN] Skipping line {line_no}: not enough fields")
                continue

            front = parts[0]
            back = parts[1]
            topic_str = parts[2] if len(parts) >= 3 else ""

            if not front or not back:
                print(f"[WARN] Skipping line {line_no}: empty front/back")
                continue

            topics = []

            # Section-derived topic
            if current_section:
                topics.append(current_section.lower())

            # Optional per-card topics (3rd field), comma-separated
            if topic_str:
                extra_topics = [
                    t.strip().lower()
                    for t in topic_str.split(",")
                    if t.strip()
                ]
                topics.extend(extra_topics)

            # Deduplicate topics while preserving order
            if topics:
                seen = set()
                deduped = []
                for t in topics:
                    if t not in seen:
                        seen.add(t)
                        deduped.append(t)
                topics = deduped

            cards.append({"front": front, "back": back, "topics": topics})

    if not cards:
        raise ValueError(f"No cards loaded from {p}")

    return cards


def choose_topic_subset(cards):
    """
    Interactively ask user to pick topics (optional).
    Returns a filtered list of cards.
    """
    topic_set = set()
    for c in cards:
        for t in c.get("topics", []):
            topic_set.add(t)

    if not topic_set:
        print("No topics found in deck; using all cards.\n")
        return cards

    sorted_topics = sorted(topic_set)
    print("Available topics:")
    for t in sorted_topics:
        print(f"  - {t}")
    print()

    raw = input(
        "Enter topics to drill (comma-separated), or just Enter for all topics: "
    ).strip()

    if not raw:
        print("Using all cards.\n")
        return cards

    selected = [t.strip().lower() for t in raw.split(",") if t.strip()]
    selected_set = set(selected)
    print(f"Selected topics: {', '.join(selected_set)}")

    filtered = [
        c
        for c in cards
        if c.get("topics") and any(t in selected_set for t in c["topics"])
    ]

    if not filtered:
        print("No cards matched those topics. Using all cards instead.\n")
        return cards

    print(f"Using {len(filtered)} cards matching selected topics.\n")
    return filtered


def print_question(card):
    topics = card.get("topics") or []
    header = "Q:"
    if topics:
        header += f" [topics: {', '.join(topics)}]"
    print("-" * 80)
    print(header, card["front"])
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
    print(f"Loaded {len(cards)} cards in this session.")
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
    print("Edit the deck file to add/remove cards or topics and rerun to keep drilling.")


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

    # Topic selection using section headers (and optional per-card tags)
    cards = choose_topic_subset(cards)

    run_quiz(cards)


if __name__ == "__main__":
    main()