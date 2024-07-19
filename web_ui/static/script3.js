const piecesIcons = {
  "a": "chess-bishop",
  "s": "chess-rook",
  "w": "chess-pawn",
  "d": "chess-king"
};

// Initialize variables
let token = null;
const socket = io(window.location.host, {
  autoConnect: false,  // Manually connect after getting the token
});
let playerReady = false;
let selectedPiecePosition = null;  // Tracks the currently selected piece position

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
 * Check if a previous login exists
 */
function checkPreviousLogin() {
  fetch('/check-login', {
    method: 'GET'
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Successful login
        token = data.token;
        connectSocket(token);
        initializeSession();
        document.getElementById('login-box').style.display = 'none';
        document.getElementById('chess-game').classList.remove('blur');
      } else {
        // Not login yet
      }
    });
}

// Event listener for the login form submission
document.getElementById('login-form').addEventListener('submit', function (event) {
  event.preventDefault();
  const password = document.getElementById('password').value;
  // Send login request to server
  fetch('/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ password: password })
  })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Successful login
        token = data.token;
        connectSocket(token);
        initializeSession();
        document.getElementById('login-box').style.display = 'none';
        document.getElementById('chess-game').classList.remove('blur');
      } else {
        // Incorrect password
        alert('Wrong Password.');
      }
    });
});

/**
 * Connects to the Socket.IO server with the provided token.
 * @param {string} token - The authentication token for connecting to the server.
 */
function connectSocket(token) {
  // Configure Socket.IO connection with authorization token
  socket.io.opts.extraHeaders = {
    Authorization: `Bearer ${token}`,
  };
  socket.connect();

  // Event listener for successful connection
  socket.on('connect', () => {
    console.log('Connected to Socket.IO server with token.');
    // Send session ID to server after successful connection
    fetch('/send-sid', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ sid: socket.id })
    });
  });

  // Event listener for disconnection
  socket.on('disconnect', () => {
    console.log('Disconnected from Socket.IO server.');
  });
}

/**
 * Initializes the session by fetching the board status.
 */
function initializeSession() {
  socket.emit('initialize_session', (data) => {
    updateBoard(data.piece_pos);
  });
}

// Event listeners for game controls

// Event listener for the new game button
document.getElementById('new-game-button').addEventListener('click', () => {
  performIfReady(() => {
    socket.emit('new_game');
  });
});

// Event listener for the undo button
document.getElementById('undo-button').addEventListener('click', () => {
  performIfReady(() => {
    socket.emit('undo', (data) => {
      if (!data.success) {
        console.log('fail: undo');
      }
    });
  });
});

// Event listener for downloading game log
document.getElementById('download-log').addEventListener('click', function () {
  fetch('/download_log', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  })
    .then(response => {
      // Check if response is successful
      if (!response.ok) {
        throw new Error(`Download failed with status ${response.status}`);
      }
      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition');
      const filename = contentDisposition.split(';')[1].trim().split('=')[1].replace(/"/g, '');

      // Start downloading the file
      return response.blob().then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      });
    })
    .catch(err => console.error('Error downloading log:', err));
});


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
  performIfReady(() => {
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
          socket.emit('move_piece', { selected_pos: selectedPiecePosition, target_pos: [row, col] }, (data) => {
            if (data.success) {
              removeHighlightValidMoves();
              selectedPiecePosition = null;
            } else {
              console.log("fail: move piece");
            }
          });
        }
      } else {
        // If no piece is selected, attempt to select the clicked square
        socket.emit('select_grid', { pos: [row, col] }, (data) => {
          if (data.valid) {
            highlightValidMoves(data.valid_moves);
            selectedPiecePosition = [row, col];
          } else {
            console.log("fail:", data.message);
            selectedPiecePosition = null;
          }
        });
      }
    }
  });
});


// Event listener for receiving board updates from the server
socket.on('board-update', function (data) {
  updateBoard(data.piece_pos);
});

// Event listener for receiving pieces move from the server
socket.on('move-piece', function (data) {
  const move_details = data.move;
  const selected_pos = move_details[0];
  const target_pos = move_details[1];
  const actionType = move_details[4];

  if (actionType === 'move' || actionType === 'capture') {
    movePiece(selected_pos, target_pos);
  } else if (actionType === 'swap') {
    swapPiece(selected_pos, target_pos);
  }
  if (data.is_win) {
    // Display win message if there is a winner
    setTimeout(function () {
      alert(data.win_msg);
    }, 100);
  }
});

// Event listener for player readiness status from the server
socket.on('player-ready', function (isReady) {
  playerReady = isReady;
});

/**
 * Executes an action only if both players are ready.
 * @param {function} action - The action to perform.
 */
function performIfReady(action) {
  if (playerReady) {
    action();
  } else {
    console.log('Action not allowed until players are ready.');
  }
}

// Initial Execution
initializeBoard();
checkPreviousLogin();
