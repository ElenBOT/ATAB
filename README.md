# ATAB

## File Structure
```
/web_ui/  # Web UI
/game.py  # The core of the game
```

## Web UI
```shell
# replay
flask --app web_ui/replay run

# Local
flask --app web_ui/chess_game run

# Online
flask --app web_ui/chess_game_online run --host=0.0.0.0 --cert=adhoc 
flask --app web_ui/chess_game_online run --host=0.0.0.0 --cert=CERT_PATH --key=KEY_PATH
```

## Change log

### 2024-07-06

Added
* Completed the basic function of web user interface (`/web_ui`).
* README.md

Changed
* Rewrite the core `game.py`, completed all functions.

### 2024-07-07

Added
* Add log download button for web ui.

Changed
* Change quote.
* Add comment and description to `script.js`.
* Updated panel layout for better organization.

Bugfix
* Fixed same type of piece can change.

### 2024-07-08

Added
* Add function of replay.

Changed
* Change the chess game dependencies name in web_ui.

### 2024-07-16

Changed
* Change `Board.check_is_win` return in game.py.

### 2024-07-17

Added
* Add online mode for the game, base on network connection.
* Add `requirements.txt`.
