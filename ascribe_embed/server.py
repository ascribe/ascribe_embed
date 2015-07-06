import re
from lru import lru_cache_function

import requests
from flask import Flask, abort, render_template


app = Flask(__name__)

ENDPOINT = 'http://staging.ascribe.io/api/editions/{}/'
PRODUCTION_ENDPOINT = 'http://ascribe.io/api/pieces/{}/'
BITCOIN_HASH_RE = re.compile('^[a-zA-Z0-9]+$')


@lru_cache_function(max_size=1024, expiration=60*60)
def render(bitcoin_hash):
    details = requests.get(ENDPOINT.format(bitcoin_hash)).json()
    edition = details['edition']
    context = {
        'bitcoin_hash': bitcoin_hash,
        'title': edition['title'],
        'artist': edition['artist_name'],
        # 'year': 2015,
        'poster': edition['thumbnail'],
        'sources': [{'type': 'video/' + e['label'], 'src': e['url']}
                    for e in edition['digital_work']['encoding_urls']]
    }
    return render_template('index.html', **context)


@lru_cache_function(max_size=1024, expiration=60*60)
def prod_render(bitcoin_hash):
    details = requests.get(PRODUCTION_ENDPOINT.format(bitcoin_hash)).json()
    edition = details['piece']
    mimetype = edition['digital_work']['mime']

    context = {
        'mimetype': mimetype,
        'bitcoin_hash': bitcoin_hash,
        'title': edition['title'],
        'artist': edition['artist_name'],
        # 'year': 2015,
    }

    if mimetype == 'video':
        context.update({
            'poster': edition['thumbnail'],
            'sources': [{'type': 'video/' + e['label'], 'src': e['url']}
                        for e in edition['digital_work']['encoding_urls']]
        })
    elif mimetype == 'audio':
        context.update({
            'url': edition['digital_work']['url']
        })
    else:
        abort(404)

    return render_template('{}.html'.format(mimetype), **context)


@app.route('/edition/<bitcoin_hash>')
def embed(bitcoin_hash):
    if not BITCOIN_HASH_RE.match(bitcoin_hash):
        abort(404)
    return prod_render(bitcoin_hash)


if __name__ == '__main__':
    app.run(debug=True)
