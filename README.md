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

### 2024-07-19

Added
* Add animation in web_ui.

Changed
* Add final state in game log.
* Change game log meta format.
* Add type of action taken by the piece in game log.
* Add win status in `game.py`

### 2024-07-23

Added
* Add turn display in web_ui.

Bugfix
* In online mode, the game UI does not correctly remove selection and highlights for the same player in multiple sessions.

Changed
* Renamed variables and functions for clarity.
* Reorganized code structure.
* Delete win_player output in game.make_move.
