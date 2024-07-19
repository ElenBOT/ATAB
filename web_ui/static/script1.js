const piecesIcons = {
  "a": "chess-bishop",
  "s": "chess-rook",
  "w": "chess-pawn",
  "d": "chess-king"
};

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
 * Highlights the valid moves on the board.
 * @param {Array} validMoves - An array of valid move positions.
 */
function highlightValidMoves(validMoves) {
  validMoves.forEach(position => {
    document.getElementById(`g-${position[0]}-${position[1]}`).classList.add("valid-move");
  });
}

/**
 * Removes the highlighting of valid moves from the board.
 */
function removeHighlightValidMoves() {
  document.querySelectorAll('div.valid-move').forEach(grid => {
    grid.classList.remove("valid-move");
  });
}

/**
 * Moves a piece from one position to another with an animation.
 * @param {Array} selected_pos - The starting position as [row, col].
 * @param {Array} target_pos - The target position as [row, col].
 */
function movePiece(selected_pos, target_pos) {
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
  piece1.style.transition = 'transform 0.5s ease-in-out';

  // Start animation
  requestAnimationFrame(() => {
    piece1.style.transform = `translate(${deltaX1}px, ${deltaY1}px)`;
  });

  // After animation completes, swap pieces
  setTimeout(() => {
    piece1.remove();
    document.getElementById(`g-${row2}-${col2}`).innerHTML = '';
    document.getElementById(`g-${row2}-${col2}`).appendChild(clonedPiece1);
  }, 500); // time should match the animation duration
}

/**
 * Swaps two pieces on the board with an animation.
 * @param {Array} selected_pos - The position of the first piece as [row, col].
 * @param {Array} target_pos - The position of the second piece as [row, col].
 */
function swapPiece(selected_pos, target_pos) {
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
  piece1.style.transition = 'transform 0.5s ease-in-out';
  piece2.style.transition = 'transform 0.5s ease-in-out';

  // Start animation
  requestAnimationFrame(() => {
    piece1.style.transform = `translate(${deltaX1}px, ${deltaY1}px)`;
    piece2.style.transform = `translate(${deltaX2}px, ${deltaY2}px)`;
  });

  // After animation completes, swap pieces
  setTimeout(() => {
    piece1.remove();
    piece2.remove();
    document.getElementById(`g-${row1}-${col1}`).appendChild(clonedPiece2);
    document.getElementById(`g-${row2}-${col2}`).appendChild(clonedPiece1);
  }, 500); // time should match the animation duration
}

/**
 * Updates the board with the given piece positions.
 * @param {Array} piecePositions - An array of piece positions and their details.
 */
function updateBoard(piecePositions) {
  clearPieces()
  piecePositions.forEach((piece) => {
    setPiece(piece[0][0], piece[0][1], piece[2], piece[1]);
  });
}

/**
 * Initializes the session by fetching the board status.
 */
function initializeSession() {
  fetch('http://127.0.0.1:5000/session', { method: 'POST' })
    .then(response => response.json())
    .then(data => updateBoard(data.piece_pos));
}

/**
 * Event listener for the new game button.
 * Starts a new game by fetching new game data and updating the board.
 */
document.getElementById('new-game-button').addEventListener('click', () => {
  fetch('http://127.0.0.1:5000/new_game', { method: 'POST' })
    .then(response => response.json())
    .then(data => updateBoard(data.piece_pos));
});

/**
 * Event listener for the undo button.
 * Undoes the last move by fetching the updated game data and updating the board.
 */
document.getElementById('undo-button').addEventListener('click', () => {
  fetch('http://127.0.0.1:5000/undo', { method: 'POST' })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        updateBoard(data.piece_pos);
      } else {
        console.log('fail: undo');
      }
    });
});

/**
 * Event listener for the log download button.
 */
document.getElementById('download-log').addEventListener('click', function () {
  window.location.href = '/download_log';
});

let selectedPiecePosition = null;

/**
 * Event listener for clicks on the chessboard.
 * Handles piece selection, valid move highlighting, and piece movement.
 * 
 * When a grid square is clicked:
 * - If no piece is currently selected:
 *   - Sends a request to select the grid square.
 *   - If the selection is valid, highlights valid moves for the selected piece.
 * - If a piece is already selected:
 *   - If the clicked square is the same as the selected piece's square, deselects the piece and removes highlights.
 *   - If the clicked square is different, sends a request to move the piece to the new position.
 *   - If the move is successful, updates the board and checks for a win condition.
 */
document.getElementById('chessboard').addEventListener('click', function (event) {
  let element;
  let isGrid = false;

  // Determine the clicked element and whether it is a grid square
  if (event.target.tagName == "I") {
    if (event.target.parentElement.parentElement.classList.contains('grid')) {
      isGrid = true;
      element = event.target.parentElement.parentElement;
    }
  } else if (event.target.tagName == "DIV") {
    if (event.target.classList.contains('grid')) {
      isGrid = true;
      element = event.target;
    }
  } else { }

  // If the clicked element is a grid square
  if (isGrid) {
    const row = parseInt(element.getAttribute('data-row'));
    const col = parseInt(element.getAttribute('data-col'));

    if (selectedPiecePosition !== null) {
      // If a piece is already selected
      if (selectedPiecePosition[0] === row && selectedPiecePosition[1] === col) {
        // If the clicked square is the same as the selected piece's square, deselect the piece
        removeHighlightValidMoves();
        selectedPiecePosition = null;
      } else {
        // Otherwise, attempt to move the piece to the new square
        fetch('http://127.0.0.1:5000/move_piece', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ selected_pos: selectedPiecePosition, target_pos: [row, col] })
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              removeHighlightValidMoves();
              const actionType = data.action_type;
              if (actionType === 'move' || actionType === 'capture') {
                movePiece(selectedPiecePosition, [row, col]);
              } else if (actionType === 'swap') {
                swapPiece(selectedPiecePosition, [row, col]);
              }
              selectedPiecePosition = null;
              if (data.is_win) {
                setTimeout(function () {
                  alert(data.win_msg);
                }, 100);
              }
            } else {
              console.log("fail: move piece")
            }
          });
      }
    } else {
      // If no piece is selected, attempt to select the clicked square
      fetch('http://127.0.0.1:5000/select_grid', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pos: [row, col] })
      })
        .then(response => response.json())
        .then(data => {
          if (data.valid) {
            highlightValidMoves(data.valid_moves);
            selectedPiecePosition = [row, col]
          } else {
            console.log("fail:", data.message);
            selectedPiecePosition = null;
          }
        });
    }
  }
});

// Initial Execution
initializeBoard();
initializeSession();
