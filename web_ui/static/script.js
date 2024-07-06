const piecesIcons = {
  "a": "chess-bishop",
  "s": "chess-rook",
  "w": "chess-pawn",
  "d": "chess-king"
};

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

function setPiece(row, col, pieceId, color) {
  const elem = `<div class="chess-piece" data-piece="${pieceId}" data-piece-color="${color}"><i class="fa-regular fa-${piecesIcons[pieceId]} ${color}"></i></div>`;
  document.getElementById(`g-${row}-${col}`).insertAdjacentHTML('beforeend', elem);
}

function highlightValidMoves(validMoves) {
  validMoves.forEach(position => {
    document.getElementById(`g-${position[0]}-${position[1]}`).classList.add("valid-move");
  });

}

function removeHighlightValidMoves() {
  document.querySelectorAll('div.valid-move').forEach(grid => {
    grid.classList.remove("valid-move");
  });
}

function clearPieces() {
  document.querySelectorAll('div.chess-piece').forEach(piece => piece.remove());
}

function updateBoard(piecePositions) {
  clearPieces()
  piecePositions.forEach((piece) => {
    setPiece(piece[0][0], piece[0][1], piece[2], piece[1]);
  });
}

// Start a new game
document.getElementById('new-game-button').addEventListener('click', () => {
  fetch('http://127.0.0.1:5000/new_game', { method: 'POST' })
    .then(response => response.json())
    .then(data => updateBoard(data.piece_pos));
});

// Undo the last move
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

let selectedPiecePosition = null;

document.getElementById('chessboard').addEventListener('click', function (event) {
  let element;
  let isGrid = false;
  if (event.target.tagName == "I") {
    if (event.target.parentElement.parentElement.classList.contains('grid'))
      isGrid = true;
      element = event.target.parentElement.parentElement;
  } else if (event.target.tagName == "DIV") {
    if (event.target.classList.contains('grid')) {
      isGrid = true;
      element = event.target;
    }
  } else {}
  console.log(element, isGrid);
  // Check if the clicked element is a grid square
  if (isGrid) {
    // Get the row and col from data attributes
    const row = parseInt(element.getAttribute('data-row'));
    const col = parseInt(element.getAttribute('data-col'));

    if (selectedPiecePosition !== null) {
      if (selectedPiecePosition[0] === row && selectedPiecePosition[1] === col) {
        removeHighlightValidMoves();
        selectedPiecePosition = null;
      } else {
        fetch('http://127.0.0.1:5000/move_piece', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ selected_pos: selectedPiecePosition, target_pos: [row, col] })
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              removeHighlightValidMoves();
              updateBoard(data.piece_pos);
              selectedPiecePosition = null;
              if (data.is_win) {
                setTimeout(function(){
                  alert(data.win_msg);
                }, 100);
              }
            } else {
              console.log("fail: move piece")
            }
          });
      }
    } else {
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

initializeBoard();
fetch('http://127.0.0.1:5000/session', { method: 'POST' })
.then(response => response.json())
.then(data => updateBoard(data.piece_pos));