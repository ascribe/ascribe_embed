#import gevent.monkey
#gevent.monkey.patch_all()

import re
from lru import lru_cache_function

import requests
#from gevent.wsgi import WSGIServer
from flask import Flask, abort, render_template_string


app = Flask(__name__)

ENDPOINT = 'http://staging.ascribe.io/api/editions/{}/'
BITCOIN_HASH_RE = re.compile('^[a-zA-Z0-9]+$')
TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>{{title}} by {{artist}}</title>
    <link href="//vjs.zencdn.net/4.12/video-js.css" rel="stylesheet">
    <link href="https://rawgit.com/cabin/videojs-sublime-skin/master/dist/videojs-sublime-skin.css" rel="stylesheet">
    <script src="//vjs.zencdn.net/4.12/video.js"></script>
    <style>
    body { font-family: "HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif }
    video { width: 100% }
    .video-js { padding-top: 56.25% }
    .vjs-fullscreen { padding-top: 0px }
    .t { -webkit-transition: opacity .3s ease-in-out; -moz-transition: opacity .3s ease-in-out; -ms-transition: opacity .3s ease-in-out; -o-transition: opacity .3s ease-in-out; transition: opacity .3s ease-in-out }
    .container { position: relative }
    .container.video-playing:hover .overlay { opacity: 1 }
    .container.video-playing .overlay { opacity: 0 }
    .container .overlay { z-index: 1; opacity: 1 }
    .container .overlay { position: absolute; top: 0; right: 0; left: 0 }
    .container h1 { margin: 0; padding: 10px 15px; color: white; font-size: 16px; font-weight: normal; background-color: rgba(0,0,0,0.8) }
    .container h1 a { color: inherit; text-decoration: none; opacity: 0.6 }
    .container h1 a:hover { text-decoration: underline; opacity: 1 }
    .logo { position: absolute; top: 10px; right: 10px; width: 50px; height: 50px; z-index: 1; opacity: 0; -webkit-transition: opacity .3s ease-in-out; -moz-transition: opacity .3s ease-in-out; -ms-transition: opacity .3s ease-in-out; -o-transition: opacity .3s ease-in-out; transition: opacity .3s ease-in-out }
    .logo img { width: 100% }

    .vjs-default-skin .vjs-play-progress,
    .vjs-default-skin .vjs-volume-level {
      background: #00A5FF;
    }

    .vjs-default-skin .vjs-big-play-button {
      border-radius: 6px;
      -o-border-radius: 6px;
      -moz-border-radius: 6px;
      -webkit-border-radius: 6px;

      box-shadow: none;
      -o-box-shadow: none;
      -moz-box-shadow: none;
      -webkit-box-shadow: none;

      width: 100px;
      height: 60px;
      top: 50%;
      left: 50%;
      margin: -30px -50px;

      border: none;

      background-color: rgba(0,0,0,.8);
    }

    .vjs-default-skin:hover .vjs-big-play-button,
    .vjs-default-skin .vjs-big-play-button:focus {
      border-color: #fff;
      background-color: rgba(0,0,0,.9);

      box-shadow: none;
      -o-box-shadow: none;
      -moz-box-shadow: none;
      -webkit-box-shadow: none;

      transition: all 0s;
      -o-transition: all 0s;
      -moz-transition: all 0s;
      -webkit-transition: all 0s;
    }

    .vjs-default-skin .vjs-big-play-button:before {
      line-height: 60px;
    }

    .vjs-default-skin .vjs-slider-handle:before,
    .vjs-default-skin .vjs-big-play-button:before {
      text-shadow: none;
    }

    .vjs-default-skin .vjs-volume-bar {
      height: .5em;
    }

    .vjs-default-skin .vjs-control-bar {
      background-color: rgba(0,0,0,.7);
    }
    </style>
  </head>
  <body>
    <div id="main-container" class="container">
      <div class="overlay t">
        <h1>
          <a href="https://ascribe.io/art/piece/{{bitcoin_hash}}" target="_blank">
            {{title}} &ndash; {{artist}}
          </a>
        </h1>
      </div>
      <video id="main-video" class="video-js vjs-default-skin" poster="{{poster}}" controls preload="none" width="auto" height="auto">
      {% for source in sources %}
        <source type="{{source.type}}" src="{{source.src}}">
      {% endfor %}
      </video>
    </div>

    <script>
    function updateContainer(options) {
      var c = document.getElementById(options.container);
      this.on('play', function(e) {
        console.log('playback started!');
        c.classList.add('video-playing');
      });
      this.on('pause', function(e) {
        console.log('playback paused!');
        c.classList.remove('video-playing');
      });
    };
    videojs.plugin('updateContainer', updateContainer);
    videojs('main-video', {
      plugins: {
        updateContainer: { container: 'main-container' }
      }
    });


    </script>
  </body>
</html>
"""


@lru_cache_function(max_size=1024, expiration=60*60)
def render(bitcoin_hash):
    details = requests.get(ENDPOINT.format(bitcoin_hash)).json()
    edition = details['edition']
    context = {
        'bitcoin_hash': bitcoin_hash,
        'title': edition['title'],
        'artist': edition['artist_name'],
        #'year': 2015,
        'poster': edition['thumbnail'],
        'sources': [{'type': 'video/' + e['label'], 'src': e['url']}
                    for e in edition['digital_work']['encoding_urls']]
    }
    return render_template_string(TEMPLATE, **context)


@app.route('/edition/<bitcoin_hash>')
def embed(bitcoin_hash):
    if not BITCOIN_HASH_RE.match(bitcoin_hash):
        abort(404)
    return render(bitcoin_hash)


if __name__ == '__main__':
    app.run(debug=True)

    # server = WSGIServer(('', 8080), embed)
    # server.serve_forever()
