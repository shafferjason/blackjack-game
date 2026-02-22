#!/usr/bin/env python3
"""A simple command-line Blackjack game: single player vs. dealer."""

import random

# Card constants
SUITS = ["Hearts", "Diamonds", "Clubs", "Spades"]
RANKS = [
    "2", "3", "4", "5", "6", "7", "8", "9", "10",
    "Jack", "Queen", "King", "Ace",
]
VALUES = {
    "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
    "10": 10, "Jack": 10, "Queen": 10, "King": 10, "Ace": 11,
}


def create_deck():
    """Create and shuffle a standard 52-card deck."""
    deck = [(rank, suit) for suit in SUITS for rank in RANKS]
    random.shuffle(deck)
    return deck


def card_str(card):
    """Return a human-readable string for a card tuple."""
    rank, suit = card
    return f"{rank} of {suit}"


def hand_str(hand):
    """Return a formatted string showing all cards in a hand."""
    return ", ".join(card_str(c) for c in hand)


def calculate_score(hand):
    """Calculate the best score for a hand, adjusting Aces from 11 to 1 as needed."""
    score = sum(VALUES[rank] for rank, _ in hand)
    # Downgrade Aces from 11 to 1 while the hand is busted
    aces = sum(1 for rank, _ in hand if rank == "Ace")
    while score > 21 and aces > 0:
        score -= 10
        aces -= 1
    return score


def deal_card(deck):
    """Deal one card from the deck. Re-shuffle a new deck if empty."""
    if not deck:
        deck.extend(create_deck())
    return deck.pop()


def display_table(player_hand, dealer_hand, reveal_dealer=False):
    """Print the current state of the table."""
    print("\n" + "=" * 40)
    if reveal_dealer:
        print(f"  Dealer's hand: {hand_str(dealer_hand)}")
        print(f"  Dealer's score: {calculate_score(dealer_hand)}")
    else:
        # Only show the dealer's first card
        print(f"  Dealer's hand: {card_str(dealer_hand[0])}, [hidden]")
    print()
    print(f"  Your hand: {hand_str(player_hand)}")
    print(f"  Your score: {calculate_score(player_hand)}")
    print("=" * 40)


def player_turn(deck, player_hand, dealer_hand):
    """Handle the player's turn: hit or stand in a loop."""
    while True:
        display_table(player_hand, dealer_hand)
        score = calculate_score(player_hand)

        if score == 21:
            print("\nYou hit 21!")
            break
        if score > 21:
            print("\nYou busted!")
            break

        try:
            choice = input("\n[H]it or [S]tand? ").strip().lower()
        except EOFError:
            # Handle non-interactive input gracefully
            choice = "s"

        if choice in ("h", "hit"):
            player_hand.append(deal_card(deck))
        elif choice in ("s", "stand"):
            print("\nYou stand.")
            break
        else:
            print("Invalid input. Please enter 'h' to hit or 's' to stand.")


def dealer_turn(deck, dealer_hand):
    """Dealer draws until reaching 17 or higher."""
    while calculate_score(dealer_hand) < 17:
        dealer_hand.append(deal_card(deck))


def determine_winner(player_hand, dealer_hand):
    """Compare final scores and print the result. Returns 1 for win, -1 for loss, 0 for push."""
    player_score = calculate_score(player_hand)
    dealer_score = calculate_score(dealer_hand)

    display_table(player_hand, dealer_hand, reveal_dealer=True)
    print()

    if player_score > 21:
        print("Dealer wins — you busted!")
        return -1
    elif dealer_score > 21:
        print("You win — dealer busted!")
        return 1
    elif player_score > dealer_score:
        print("You win!")
        return 1
    elif dealer_score > player_score:
        print("Dealer wins!")
        return -1
    else:
        print("It's a push (tie)!")
        return 0


def play_round(deck):
    """Play a single round of Blackjack. Returns 1/0/-1 for win/push/loss."""
    # Deal initial two cards each
    player_hand = [deal_card(deck), deal_card(deck)]
    dealer_hand = [deal_card(deck), deal_card(deck)]

    # Check for natural Blackjack (21 on first two cards)
    player_bj = calculate_score(player_hand) == 21
    dealer_bj = calculate_score(dealer_hand) == 21

    if player_bj or dealer_bj:
        display_table(player_hand, dealer_hand, reveal_dealer=True)
        if player_bj and dealer_bj:
            print("\nBoth have Blackjack — it's a push!")
            return 0
        elif player_bj:
            print("\nBlackjack! You win!")
            return 1
        else:
            print("\nDealer has Blackjack! Dealer wins.")
            return -1

    # Player's turn
    player_turn(deck, player_hand, dealer_hand)

    # Dealer only plays if the player hasn't busted
    if calculate_score(player_hand) <= 21:
        dealer_turn(deck, dealer_hand)

    return determine_winner(player_hand, dealer_hand)


def main():
    """Main game loop: play rounds until the player quits."""
    print("=" * 40)
    print("   Welcome to Blackjack!")
    print("=" * 40)

    deck = create_deck()
    wins, losses, pushes = 0, 0, 0

    while True:
        result = play_round(deck)
        if result == 1:
            wins += 1
        elif result == -1:
            losses += 1
        else:
            pushes += 1

        print(f"\nRecord: {wins}W - {losses}L - {pushes}T")

        try:
            again = input("\nPlay again? [Y/n] ").strip().lower()
        except EOFError:
            again = "n"

        if again in ("n", "no"):
            break

    print("\nThanks for playing! Final record: "
          f"{wins}W - {losses}L - {pushes}T")


if __name__ == "__main__":
    main()
