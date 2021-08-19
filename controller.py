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

# Caleb DMZ =====

# Webpage for github webhook
@app.route('/githook')
def githook():
    secret = request.headers['X-Hub-Signature']
    parsed = json.loads(request.json)
    with open('/home/s4585694/hook','w') as handle:
        handle.write(json.dumps(parsed, indent=4, sort_keys=True))
    return render_template('errors/error_404.html')
    #return render_template('errors/error_404.html');

# Caleb DMZ =====

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
    return render_template("matthew_wuz_here.html", test=name=="s4582166", user=name)


@app.route("/kyle_test")
def sexy_asian():
    name = "Kyle Macaskill"
    return render_template("kyle_is_really_funny.html", name=name, title = "Kyle")
