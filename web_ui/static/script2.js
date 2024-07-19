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

// Array to store the sequence of moves in the game log
let gameLog = [];

// Index to track the current move in the game log
let currentMove = 0;

// ID for the interval timer used during automatic replay
let intervalId = null;

// ID for the timeout timer used during piece movement animations
let timeoutId = null;

// Interval time in milliseconds for replaying moves
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
 * Removes all pieces from the board.
 */
function clearPieces() {
  document.querySelectorAll('div.chess-piece').forEach(piece => piece.remove());
}

/**
 * Clears a piece from the board at the specified row and column.
 * @param {Array} pos - An array containing the row and column of the piece.
 */
function clearPiece(pos) {
  document.getElementById(`g-${pos[0]}-${pos[1]}`).innerHTML = "";
}

/**
 * Sets up the initial positions of all pieces on the board.
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
 * Moves a piece from one position to another with an animation.
 * @param {Array} selected_pos - The starting position as [row, col].
 * @param {Array} target_pos - The target position as [row, col].
 * @param {number} trans_time - The transition time for the animation (default 0.5s).
 */
function movePiece(selected_pos, target_pos, trans_time = 0.5) {
  const [row1, col1] = selected_pos;
  const [row2, col2] = target_pos;
  const piece1 = document.querySelector(`#g-${row1}-${col1} .chess-piece`);
  const grid2 = document.querySelector(`#g-${row2}-${col2}`);

  if (!piece1) return; // Return if the square is empty

  // Clone piece1 to retain its content
  const clonedPiece1 = piece1.cloneNode(true);

  // Calculate positions
  const rect1 = piece1.getBoundingClientRect();
  const rect2 = grid2.getBoundingClientRect();
  const deltaX1 = (rect2.left + rect2.right - rect1.left - rect1.right) / 2;
  const deltaY1 = (rect2.top + rect2.bottom - rect1.top - rect1.bottom) / 2;

  // Apply animation styles
  piece1.style.transition = `transform ${trans_time}s ease-in-out`;

  // Start animation
  requestAnimationFrame(() => {
    piece1.style.transform = `translate(${deltaX1}px, ${deltaY1}px)`;
  });

  // After animation completes, swap pieces
  timeoutId = setTimeout(() => {
    piece1.remove();
    document.getElementById(`g-${row2}-${col2}`).innerHTML = '';
    document.getElementById(`g-${row2}-${col2}`).appendChild(clonedPiece1);
  }, trans_time * 1000); // time should match the animation duration
}

/**
 * Swaps two pieces on the board with an animation.
 * @param {Array} selected_pos - The position of the first piece as [row, col].
 * @param {Array} target_pos - The position of the second piece as [row, col].
 * @param {number} trans_time - The transition time for the animation (default 0.5s).
 */
function swapPiece(selected_pos, target_pos, trans_time = 0.5) {
  const [row1, col1] = selected_pos;
  const [row2, col2] = target_pos;
  const piece1 = document.querySelector(`#g-${row1}-${col1} .chess-piece`);
  const piece2 = document.querySelector(`#g-${row2}-${col2} .chess-piece`);

  if (!piece1 || !piece2) return; // Return if either square is empty

  // Clone pieces to retain its content
  const clonedPiece1 = piece1.cloneNode(true);
  const clonedPiece2 = piece2.cloneNode(true);

  // Calculate positions
  const rect1 = piece1.getBoundingClientRect();
  const rect2 = piece2.getBoundingClientRect();
  const deltaX1 = (rect2.left + rect2.right - rect1.left - rect1.right) / 2;
  const deltaY1 = (rect2.top + rect2.bottom - rect1.top - rect1.bottom) / 2;
  const deltaX2 = -deltaX1;
  const deltaY2 = -deltaY1;

  // Apply animation styles
  piece1.style.transition = `transform ${trans_time}s ease-in-out`;
  piece2.style.transition = `transform ${trans_time}s ease-in-out`;

  // Start animation
  requestAnimationFrame(() => {
    piece1.style.transform = `translate(${deltaX1}px, ${deltaY1}px)`;
    piece2.style.transform = `translate(${deltaX2}px, ${deltaY2}px)`;
  });

  // After animation completes, swap pieces
  timeoutId = setTimeout(() => {
    piece1.remove();
    piece2.remove();
    document.getElementById(`g-${row1}-${col1}`).appendChild(clonedPiece2);
    document.getElementById(`g-${row2}-${col2}`).appendChild(clonedPiece1);
  }, trans_time * 1000); // time should match the animation duration
}

/**
 * Converts a human-readable chess coordinate to an array of board coordinates.
 * @param {string} readableCoord - The human-readable coordinate (e.g., 'a1').
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
 * Moves one step forward in the game log, executing the next move.
 * @param {number} trans_time - The transition time for animations (default 0.5s).
 */
function forward(trans_time = 0.5) {
  if (currentMove < gameLog.length) {
    const move = gameLog[currentMove];
    const startCoord = readableToCoord(move[0]);
    const endCoord = readableToCoord(move[1]);
    const actionType = move[4];

    if (actionType === 'move') {
      movePiece(startCoord, endCoord, trans_time);
    } else if (actionType === 'swap') {
      swapPiece(startCoord, endCoord, trans_time);
    } else {
      movePiece(startCoord, endCoord, trans_time);
    }
    currentMove++;
  } else {
    // At end of the game log
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }
}

/**
 * Moves one step backward in the game log, reversing the last move.
 */
function backward() {
  if (currentMove > 0) {
    currentMove--;
    const move = gameLog[currentMove];
    const startCoord = readableToCoord(move[0]);
    const endCoord = readableToCoord(move[1]);
    const startPiece = move[2];
    const targetPiece = move[3];

    clearPiece(startCoord);
    clearPiece(endCoord);
    setPiece(startCoord[0], startCoord[1], startPiece[0], color(startPiece[1]));
    setPiece(endCoord[0], endCoord[1], targetPiece[0], color(targetPiece[1]));
  } else {
    // At start of the game log
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }
  }
}

/**
 * Resets the game to the initial state, clearing the game log and setting starting positions.
 */
function reset() {
  currentMove = 0;
  // Stop the autoplay loop
  clearInterval(intervalId);
  intervalId = null;
  // Stop the piece movement animation
  clearTimeout(timeoutId);
  setStartingPositions();
}

/**
 * Starts replaying the game log from the current position at the defined speed.
 */
function play() {
  if (!intervalId) {
    intervalId = setInterval(() =>
      forward(playSpeedInterval / 1000 * 0.6),
      playSpeedInterval
    );
  }
}

/**
 * Pauses the replay of the game log.
 */
function pause() {
  clearInterval(intervalId);
  intervalId = null;
}

/**
 * Loads the game log from the selected file and sets the initial board positions.
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

// Buttons and range input event listener
document.getElementById('reset-button').addEventListener('click', reset);
document.getElementById('play-button').addEventListener('click', play);
document.getElementById('pause-button').addEventListener('click', pause);
document.getElementById('forward-button').addEventListener('click', () => forward());
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
    intervalId = setInterval(() => forward(playSpeedInterval / 1000 * 0.6), playSpeedInterval);
  }
});

// Initial Execution
initializeBoard();
