
import threading
import webbrowser

from flask import Flask, render_template


app = Flask(__name__)

@app.route("/")
def index():
    """Serve the index page."""
    return render_template("index2.html")


# @app.after_request
# def after_request(response):
#     """Add CORS headers to every response."""
#     response.headers.add('Access-Control-Allow-Origin', '*')
#     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
#     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
#     # response.headers.add('Access-Control-Allow-Credentials', 'true')
#     return response


def open_browser():
    """Open the web browser to the chess game."""
    webbrowser.open_new("http://127.0.0.1:5001/")


if __name__ == "__main__":
    threading.Timer(1, open_browser).start()
    app.run(port=5001)
