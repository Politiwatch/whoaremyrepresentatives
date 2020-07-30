from flask import Flask, render_template, request, jsonify, send_from_directory, abort
from urllib.parse import quote_plus
import api
import os

app = Flask(__name__)


@app.template_filter()
def number(value):
    return "{:,.2f}".format(float(value))


@app.template_filter()
def urlescape(url):
    return quote_plus(url)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/representatives")
def representatives():
    zipcode = request.args.get("zip")
    address = request.args.get("address")

    repdata = api.get_representatives(zipcode, address)

    if repdata is None:
        abort(404, "Unable to find any representatives in our database for the given address. It's possible that you mistyped your \
            address, or that your location is not in our database.")

    federal = list(filter(
        lambda k: "country" in k["office"]["levels"], repdata["representatives"]))
    state = list(filter(
        lambda k: "administrativeArea1" in k["office"]["levels"], repdata["representatives"]))
    local = list(filter(lambda k: not (
        k in federal or k in state), repdata["representatives"]))

    return render_template(
        "representatives.html",
        input=repdata["input"],
        federal=federal,
        state=state,
        local=local,
    )


@app.route('/static/<path:path>')
def static_files(path):
    return send_from_directory('static', path)


@app.route('/robots.txt')
def static_from_root():
    return send_from_directory('static', request.path[1:])


@app.errorhandler(404)
@app.errorhandler(500)
def error_page(e):
    return render_template("error.html", error=e), e.code


if __name__ == "__main__":
    app.run(host=os.getenv("BIND_ADDRESS", "0.0.0.0"), port=os.getenv(
        "PORT", "8000"), debug=os.getenv("DEBUG", "False") == "True")
