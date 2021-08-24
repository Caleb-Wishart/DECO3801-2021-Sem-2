from flask import Flask, request, render_template
import json

app = Flask(__name__)


@app.route('/')
def index():
    name = "example"
    if 'x-kvd-payload' in request.headers:
        userjson = request.headers['x-kvd-payload']
        user = json.loads(userjson)
        name = user['user']
    name = "test"
    return render_template('example.html',title='welcome', name=name)


@app.route('/foobar')
def foobar():
    return "<span style='color:blue'>Hello again!</span>"


@app.route("/astley_wolf")
def big_d_supreme():
    all_magic_no_num = 6.1
    oof = [a for a in range(67, 70) if not a % 3]
    ooh = [oof[0] * x for x in range(417, 435)]
    secrets = [max([int(delicious / oof[0]) for delicious in ooh if delicious < oof[0]**2 *
                    all_magic_no_num])]
    mystery = oof + secrets
    return render_template("big_daddy_has_arrived.html", hohyeah=mystery, problem="Solved?")


@app.route("/jason_test")
def jtest():
    return render_template("base.html", title="This is a test page", name="Jason")

@app.route("/matthew_test")
def cool_fun():
    name = "Matt"
    return render_template("matthew_wuz_here.html",title="matt wuz here", test="caleb", user=name)


@app.route("/kyle_test")
def sexy_asian():
    name = "Kyle Macaskill"
    return render_template("kyle_is_really_funny.html", name=name, title = "Kyle")

@app.route("/alex_test")
def change_colours(hex="b12222"):
    return render_template("alex_colours.html", 
            title = "welcome", colour = hex)