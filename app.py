from flask import Flask, request, render_template, jsonify, redirect
from flask_pymongo import PyMongo
import json
import random
import string
import re


app = Flask(__name__)
mongo = PyMongo(app)


@app.route('/')
def home():
    # TODO: It's quite innefficient to generate the list every time the page is visited. On a small scale it's nice, but it could get painful when scaled.
    return render_template('index.html', top=list(mongo.db.links.find().sort([('uses', -1)]).limit(10)))


@app.route('/new', methods=['POST'])
def new():
    data = request.json

    already = mongo.db.links.find_one({'url': data['url']})
    if already is None:  # If there's not yet a link to that page, then we're going to make one.
        if data.get('key') is not None:
            if mongo.db.links.find_one({'key': data['key']}) is None:
                key = data['key']
            else:
                # TODO: This can be done more cleanly.
                return jsonify({'error': 409}), 409
        else:
            key = ''.join([random.choice(string.ascii_letters + string.digits) for i in range(0, 4)])

        url = re.sub(r'^https?://(www\.)?', '', data['url'])
        print('Creating link to %s at key %s...' % (url, key), end='')
        mongo.db.links.insert({
            'key': key,
            'url': url,
            'uses': 0
        })
        print(' done.')
    else:
        key = already['key']

    return jsonify({'key': key})


@app.route('/<key>')
def link(key):
    url = '//' + mongo.db.links.find_one_or_404({'key': key})['url']
    mongo.db.links.update(
        {'key': key},
        {'$inc': {'uses': 1}}
    )

    return redirect(url, code=301)


if __name__ == '__main__':
    with open('config.json') as f:
        config = json.loads(f.read())
    app.run(port=config['port'], host=config['host'], debug=config['debug'])
