import os
import re
from lru import lru_cache_function

import requests
from flask import Flask, abort, render_template


app = Flask(__name__)

API_ENDPOINT = os.environ.get('API_ENDPOINT', 'https://www.ascribe.io/api/{}')

EDITIONS_ENDPOINT = API_ENDPOINT.format('/editions/{}/')
PIECES_ENDPOINT = API_ENDPOINT.format('/pieces/{}/')
BITCOIN_HASH_RE = re.compile('^[a-zA-Z0-9]+$')


@lru_cache_function(max_size=1024, expiration=60 * 60)
def render(bitcoin_hash):
    endpoint = 'editions'
    details = requests.get(EDITIONS_ENDPOINT.format(bitcoin_hash)).json()
    print details
    if not details.get('success'):
        endpoint = 'pieces'
        details = requests.get(PIECES_ENDPOINT.format(bitcoin_hash)).json()
        if not details.get('success'):
            return

    edition = details.get('edition', details.get('piece'))
    mimetype = edition['digital_work']['mime']

    context = {
        'endpoint': endpoint,
        'bitcoin_hash': bitcoin_hash,
        'title': edition['title'],
        'artist': edition['artist_name'],
        # 'year': 2015,
    }

    if mimetype == 'video':
        poster = edition['thumbnail']['url']

        if edition['thumbnail'].get('thumbnail_sizes'):
            poster = edition['thumbnail']['thumbnail_sizes'].get('600x600', poster)

        context.update({
            'poster': poster,
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
@app.route('/content/<bitcoin_hash>')
def embed(bitcoin_hash):
    page = render(bitcoin_hash)
    if not page:
        abort(404)
    return page


if __name__ == '__main__':
    app.run(debug=True)
