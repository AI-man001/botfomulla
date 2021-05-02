from flask_bootstrap import Bootstrap
from flask import Flask, render_template

app = Flask(__name__)
Bootstrap(app)


@app.route('/', methods=['GET'])
def getIndexPage():
  return render_template('index.html')


@app.route('/<page>', methods=['GET'])
def findPage(page):
  return render_template(page)


if __name__ == "__main__":
  app.run(debug=True)