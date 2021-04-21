from flask import Flask, render_template, request, session, redirect, url_for
import urllib.parse
import threading

from game import Game
from player import Player

app = Flask(__name__)
app.secret_key = 'super secret key'

lock = threading.Lock()


USERS = {}


############################################
#            HELPER FUNCTIONS              #
############################################
def get_arg(arg_name):
    """
    Grabs an argument from a request.

    Args:
        arg_name: The argument name.

    Returns: The argument, converted to the correct type. If it couldn't convert, None will be returned.
    """
    arg = None
    if request.json:
        arg = request.json.get(arg_name)
    if not arg and request.values:
        arg = request.values.get(arg_name)
    if arg and type(arg) == str:
        arg = urllib.parse.unquote(arg).strip().upper()
    return arg


############################################
#              BACKEND_ROUTES              #
############################################


@app.before_request
def before_request_callback():
    if 'username' in session and session['username'] not in USERS:
        print("'username' cookie found, but no attached user. Removing cookie")
        session.pop('username')

    if 'username' not in session and request.method == 'GET' and \
            request.path != url_for('login') and 'static' not in request.path:
        return redirect(url_for('login'))


@app.errorhandler(404)
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404


############################################
#                  ROUTES                  #
############################################


@app.route('/', methods=['GET'])
def home():
    user = USERS[session['username']]
    if user.game is None:
        opponents = {}
        for opponent_name, opponent in USERS.items():
            if opponent != user and opponent.game is None:
                opponents[opponent_name] = opponent
        return render_template('home.html', currentUser=session['username'], opponents=opponents)
    else:
        return redirect(url_for('game'))


@app.route('/startGame', methods=['GET'])
def start_game():
    challenger = USERS[session['username']]
    opponent = get_arg('opponent')
    if opponent and opponent in USERS:
        opponent = USERS[opponent]
        new_game = Game(challenger, opponent)
        with lock:
            if challenger.game is None and opponent.game is None:
                challenger.game = new_game
                opponent.game = new_game
        if challenger.game == opponent.game == new_game:
            return redirect(url_for('game'))
    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'username' in session:
            return redirect(url_for('home'))
        else:
            return render_template("login.html")
    elif request.method == 'POST':
        username = get_arg('Uname')
        if username:
            if username not in USERS:
                if username.isalnum():
                    USERS[username] = Player(username)
                    session['username'] = username
                    return redirect(url_for('home'))
                else:
                    errormessage = f'Username not alphanumeric: {username}'
            else:
                errormessage = f'Username taken: {username}'
        else:
            errormessage = 'Username must not be blank'
        return render_template("login.html", errorMessage=errormessage)


@app.route('/logout', methods=['GET'])
def logout():
    user = USERS[session['username']]
    if user.game is not None:
        user.game.surrender_game(user)
    USERS.pop(session['username'])
    session.pop('username')
    return redirect(url_for('home'))


@app.route('/game', methods=['GET'])
def game():
    if USERS[session['username']].game is not None:
        return render_template("game.html")
    else:
        return redirect(url_for('home'))


@app.route('/surrender', methods=['GET'])
def surrender():
    user = USERS[session['username']]
    if user.game is not None:
        user.game.surrender_game(user)
    return redirect(url_for('game'))


@app.route('/leaveGame', methods=['GET'])
def leave_game():
    user = USERS[session['username']]
    if user.game is not None:
        user.game.surrender_game(user)
    user.game = None
    return redirect(url_for('home'))


@app.route('/getBoard', methods=['GET'])
def get_board():
    user = USERS[session['username']]
    cell_size = '30px'
    return render_template("board.html", user=user, cell_size=cell_size)


@app.route('/makeMove', methods=['POST'])
def make_move():
    user = USERS[session['username']]
    button_id = get_arg('button_id')
    if button_id and user.game is not None:
        name, row, col = button_id.split('_')
        user.game.make_move(user, int(row), int(col))
        return 'Success'
    return 'Fail'


if __name__ == '__main__':
    app.run()
