"""Minimal Flask web interface for the Blackjack game."""

import uuid
from flask import Flask, render_template_string, session, redirect, url_for, request
from blackjack import create_deck, deal_card, calculate_score, card_str, hand_str

app = Flask(__name__)
app.secret_key = "blackjack-secret-key-change-in-prod"

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blackjack</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', sans-serif; background: #0b5d1e; color: #fff; min-height: 100vh; display: flex; justify-content: center; align-items: center; }
.table { background: #1a7a33; border-radius: 24px; padding: 40px; max-width: 520px; width: 95%; box-shadow: 0 8px 32px rgba(0,0,0,.4); border: 6px solid #0e4a18; }
h1 { text-align: center; margin-bottom: 24px; font-size: 1.6em; letter-spacing: 1px; }
.hand { background: rgba(0,0,0,.15); border-radius: 12px; padding: 16px; margin-bottom: 16px; }
.hand h2 { font-size: .85em; text-transform: uppercase; letter-spacing: 2px; opacity: .7; margin-bottom: 8px; }
.cards { font-size: 1.05em; line-height: 1.6; }
.score { font-weight: bold; margin-top: 6px; font-size: 1.1em; }
.actions { display: flex; gap: 12px; justify-content: center; margin-top: 20px; }
.btn { padding: 12px 32px; border: none; border-radius: 8px; font-size: 1em; font-weight: bold; cursor: pointer; transition: transform .1s; }
.btn:active { transform: scale(.96); }
.hit { background: #e8c616; color: #222; }
.stand { background: #d44; color: #fff; }
.deal { background: #fff; color: #1a7a33; }
.msg { text-align: center; margin-top: 16px; padding: 12px; background: rgba(0,0,0,.2); border-radius: 8px; font-size: 1.15em; font-weight: bold; }
.record { text-align: center; margin-top: 12px; font-size: .9em; opacity: .7; }
</style>
</head>
<body>
<div class="table">
<h1>Blackjack</h1>

<div class="hand">
<h2>Dealer</h2>
<div class="cards">{{ dealer_display }}</div>
{% if reveal %}<div class="score">Score: {{ dealer_score }}</div>{% endif %}
</div>

<div class="hand">
<h2>You</h2>
<div class="cards">{{ player_display }}</div>
<div class="score">Score: {{ player_score }}</div>
</div>

{% if message %}<div class="msg">{{ message }}</div>{% endif %}

<div class="actions">
{% if game_over %}
<form action="/deal" method="post"><button class="btn deal" type="submit">Deal Again</button></form>
{% else %}
<form action="/hit" method="post"><button class="btn hit" type="submit">Hit</button></form>
<form action="/stand" method="post"><button class="btn stand" type="submit">Stand</button></form>
{% endif %}
</div>

<div class="record">Record: {{ wins }}W - {{ losses }}L - {{ pushes }}T</div>
</div>
</body>
</html>"""


def get_game():
    """Retrieve or initialize game state from session."""
    if "deck" not in session:
        session["deck"] = create_deck()
        session["wins"] = 0
        session["losses"] = 0
        session["pushes"] = 0
        session["game_over"] = True
        session["player"] = []
        session["dealer"] = []
        session["message"] = "Welcome! Press Deal to start."
    return session


def render(game):
    reveal = game.get("game_over", False)
    dealer = [tuple(c) for c in game["dealer"]]
    player = [tuple(c) for c in game["player"]]

    if reveal or not dealer:
        dealer_display = hand_str(dealer) if dealer else "—"
    else:
        dealer_display = f"{card_str(tuple(dealer[0]))}, [hidden]"

    return render_template_string(
        HTML,
        dealer_display=dealer_display,
        dealer_score=calculate_score(dealer) if dealer else 0,
        player_display=hand_str(player) if player else "—",
        player_score=calculate_score(player) if player else 0,
        reveal=reveal,
        message=game.get("message", ""),
        game_over=game.get("game_over", True),
        wins=game.get("wins", 0),
        losses=game.get("losses", 0),
        pushes=game.get("pushes", 0),
    )


@app.route("/")
def index():
    game = get_game()
    return render(game)


@app.route("/deal", methods=["POST"])
def deal():
    game = get_game()
    deck = game["deck"]
    if not deck or len(deck) < 4:
        deck = create_deck()

    player = [deal_card(deck), deal_card(deck)]
    dealer = [deal_card(deck), deal_card(deck)]

    game["deck"] = deck
    game["player"] = player
    game["dealer"] = dealer
    game["game_over"] = False
    game["message"] = ""

    player_bj = calculate_score(player) == 21
    dealer_bj = calculate_score(dealer) == 21

    if player_bj or dealer_bj:
        game["game_over"] = True
        if player_bj and dealer_bj:
            game["message"] = "Both have Blackjack — Push!"
            game["pushes"] = game.get("pushes", 0) + 1
        elif player_bj:
            game["message"] = "Blackjack! You win!"
            game["wins"] = game.get("wins", 0) + 1
        else:
            game["message"] = "Dealer has Blackjack! Dealer wins."
            game["losses"] = game.get("losses", 0) + 1

    session.update(game)
    return redirect(url_for("index"))


@app.route("/hit", methods=["POST"])
def hit():
    game = get_game()
    if game.get("game_over"):
        return redirect(url_for("index"))

    deck = game["deck"]
    player = [tuple(c) for c in game["player"]]
    player.append(deal_card(deck))

    game["deck"] = deck
    game["player"] = player

    score = calculate_score(player)
    if score > 21:
        game["game_over"] = True
        game["message"] = "You busted! Dealer wins."
        game["losses"] = game.get("losses", 0) + 1
    elif score == 21:
        return _stand(game)

    session.update(game)
    return redirect(url_for("index"))


@app.route("/stand", methods=["POST"])
def stand():
    game = get_game()
    if game.get("game_over"):
        return redirect(url_for("index"))
    return _stand(game)


def _stand(game):
    deck = game["deck"]
    dealer = [tuple(c) for c in game["dealer"]]
    player = [tuple(c) for c in game["player"]]

    while calculate_score(dealer) < 17:
        dealer.append(deal_card(deck))

    game["deck"] = deck
    game["dealer"] = dealer
    game["game_over"] = True

    ps = calculate_score(player)
    ds = calculate_score(dealer)

    if ps > 21:
        game["message"] = "You busted! Dealer wins."
        game["losses"] = game.get("losses", 0) + 1
    elif ds > 21:
        game["message"] = "Dealer busted! You win!"
        game["wins"] = game.get("wins", 0) + 1
    elif ps > ds:
        game["message"] = "You win!"
        game["wins"] = game.get("wins", 0) + 1
    elif ds > ps:
        game["message"] = "Dealer wins!"
        game["losses"] = game.get("losses", 0) + 1
    else:
        game["message"] = "Push (tie)!"
        game["pushes"] = game.get("pushes", 0) + 1

    session.update(game)
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
