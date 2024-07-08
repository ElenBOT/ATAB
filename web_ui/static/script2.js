const piecesIcons = {
  "a": "chess-bishop",
  "s": "chess-rook",
  "w": "chess-pawn",
  "d": "chess-king"
};

const starting_positions = {
  "a": [[0, 1], [0, 6]],
  "s": [[0, 2], [0, 5]],
  "d": [[1, 2], [1, 5]],
  "w": [[1, 0], [1, 1], [1, 3], [1, 4], [1, 6], [1, 7]],
};

let gameLog = [];
let currentMove = 0;
let intervalId = null;
let playSpeedInterval = 1000;

/**
 * Initializes the board with an 8x8 grid of squares.
 */
function initializeBoard() {
  const board = document.getElementById("chessboard");
  for (row = 0; row < 8; row++) {
    for (col = 0; col < 8; col++) {
      const color = (row % 2 === 0) ? (col % 2 === 0 ? "black" : "white") : (col % 2 === 0 ? "white" : "black");
      const gridSquare = `<div id="g-${row}-${col}" class="grid ${color}" data-row="${row}" data-col="${col}"></div>`;
      board.insertAdjacentHTML('beforeend', gridSquare);
    }
  }
}

/**
 * Sets a piece on the board at the specified row and column.
 * @param {number} row - The row position.
 * @param {number} col - The column position.
 * @param {string} pieceId - The identifier for the piece type. (a, s, w, d)
 * @param {string} color - The color of the piece.
 */
function setPiece(row, col, pieceId, color) {
  const elem = `<div class="chess-piece" data-piece="${pieceId}" data-piece-color="${color}"><i class="fa-regular fa-${piecesIcons[pieceId]} ${color}"></i></div>`;
  document.getElementById(`g-${row}-${col}`).insertAdjacentHTML('beforeend', elem);
}

/**
 * Clears all pieces from the board.
 */
function clearPieces() {
  document.querySelectorAll('div.chess-piece').forEach(piece => piece.remove());
}

/**
 * Clears a piece from the board at the specified row and column.
 * @param {number} row - The row position.
 * @param {number} col - The column position.
 */
function clearPiece(row, col) {
  document.getElementById(`g-${row}-${col}`).innerHTML = "";
}

/**
 * Sets the starting positions of the pieces.
 */
function setStartingPositions() {
  clearPieces();
  // Set blue pieces
  for (const piece in starting_positions) {
    starting_positions[piece].forEach(position => {
      setPiece(position[0], position[1], piece, 'blue');
    });
  }
  // Set red pieces
  for (const piece in starting_positions) {
    starting_positions[piece].forEach(position => {
      setPiece(7 - position[0], position[1], piece, 'red');
    });
  }
}

/**
 * Converts readable format coordinates to board coordinates.
 * @param {string} readableCoord - The readable coordinate (e.g., 'a1').
 * @returns {Array} The board coordinate as [row, col].
 */
function readableToCoord(readableCoord) {
  // Convert readable format coordinates to board coordinates
  const col = readableCoord.charCodeAt(0) - 'a'.charCodeAt(0);
  const row = 8 - parseInt(readableCoord[1]);
  return [row, col];
}

/**
 * Returns the color based on the given value.
 * @param {string} c - The color code ('0' or '1').
 * @returns {string} The color ('red' or 'blue').
 */
function color(c) {
  return parseInt(c) ? "red" : "blue";
}

/**
* Moves one step forward in the game log.
*/
function forward() {
  if (currentMove < gameLog.length) {
    const move = gameLog[currentMove];
    const startCoord = readableToCoord(move[0]);
    const endCoord = readableToCoord(move[1]);
    const startPiece = move[2];
    const targetPiece = move[3];

    if (targetPiece == "n") {
      clearPiece(startCoord[0], startCoord[1]);
      setPiece(endCoord[0], endCoord[1], startPiece[0], color(startPiece[1]));
    } else if (targetPiece[1] == (currentMove % 2)) {
      clearPiece(startCoord[0], startCoord[1]);
      clearPiece(endCoord[0], endCoord[1]);
      setPiece(endCoord[0], endCoord[1], startPiece[0], color(startPiece[1]));
      setPiece(startCoord[0], startCoord[1], targetPiece[0], color(targetPiece[1]));
    } else {
      clearPiece(startCoord[0], startCoord[1]);
      clearPiece(endCoord[0], endCoord[1]);
      setPiece(endCoord[0], endCoord[1], startPiece[0], color(startPiece[1]));
    }

    currentMove++;
  } else {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }
}

/**
* Moves one step backward in the game log.
*/
function backward() {
  if (currentMove > 0) {
    currentMove--;
    const move = gameLog[currentMove];
    const startCoord = readableToCoord(move[0]);
    const endCoord = readableToCoord(move[1]);
    const startPiece = move[2];
    const targetPiece = move[3];

    clearPiece(startCoord[0], startCoord[1]);
    clearPiece(endCoord[0], endCoord[1]);
    setPiece(startCoord[0], startCoord[1], startPiece[0], color(startPiece[1]));
    setPiece(endCoord[0], endCoord[1], targetPiece[0], color(targetPiece[1]));
  } else {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }
}

function reset() {
  currentMove = 0;
  clearInterval(intervalId);
  intervalId = null;
  setStartingPositions();
}

/**
* Plays the game log from the current position.
*/
function play() {
  if (!intervalId) {
    intervalId = setInterval(forward, playSpeedInterval);
  }
}

/**
* Pauses the game log replay.
*/
function pause() {
  clearInterval(intervalId);
  intervalId = null;
}

/**
 * Loads the game log from the selected file.
 */
document.getElementById('file-input').addEventListener('change', function (event) {
  const file = event.target.files[0];
  const reader = new FileReader();

  reader.onload = function (e) {
    gameLog = JSON.parse(e.target.result).game_log;
    currentMove = 0;
    setStartingPositions();
  };

  reader.readAsText(file);
});

document.getElementById('reset-button').addEventListener('click', reset);
document.getElementById('play-button').addEventListener('click', play);
document.getElementById('pause-button').addEventListener('click', pause);
document.getElementById('forward-button').addEventListener('click', forward);
document.getElementById('backward-button').addEventListener('click', backward);
document.getElementById('speed-range').addEventListener('input', function (event) {
  const playSpeed = event.target.value;
  document.getElementById('speed-range-label').innerText = `Speed: ${playSpeed}`;
});
document.getElementById('speed-range').addEventListener('change', function (event) {
  const playSpeed = event.target.value;
  playSpeedInterval = 20000 / playSpeed;
  if (intervalId) {
    clearInterval(intervalId);
    intervalId = setInterval(forward, playSpeedInterval);
  }
});

// Initial Execution
initializeBoard();
