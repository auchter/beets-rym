from beets import plugins, config, dbcore, ui
from beets.autotag.hooks import string_dist
from beets.dbcore import types
import requests
import pprint


API_URL = 'https://customsearch.googleapis.com/customsearch/v1/siterestrict'

class RymPlugin(plugins.BeetsPlugin):
    def __init__(self):
        super().__init__()
        config['rym'].add({
            'google_api_key': '',
            'google_search_engine_id': '',
        })
        config['rym']['google_api_key'].redact = True

        self.album_types = {
            'rym_url': types.STRING,
            'rym_genre': types.STRING,
            'rym_rating_count': types.INTEGER,
            'rym_rating_value': types.Float(2),
        }

    def commands(self):
        cmd = ui.Subcommand('rym', help='Import genres and ratings from RYM')

        def func(lib, opts, args):
            import_rym(lib, ui.decargs(args), self._log)

        cmd.func = func
        return [cmd]


def import_rym(lib, query, log):

    albums = lib.albums(query)
    for album in albums:
        artist = album['albumartist']
        album_name = album['album']

        if album.get('rym_url', '') != '':
            log.warning(f"skipping {artist} - {album_name} since rym_url is populated")
            continue

        result = rym_query(artist, album_name)
        if result is None:
            log.warning(f"No result for {artist} - {album_name}")
            continue
        album['rym_url'] = result['link']
        album['rym_genre'] = result.get('albumgenre', '')
        album['rym_rating_count'] = result.get('ratingcount', 0)
        album['rym_rating_value'] = result.get('ratingvalue', 0.0)
        album.store()


def rym_query(artist, album):
    params = {
        'q': ' '.join([artist, album]),
        'cx': config['rym']['google_search_engine_id'].get(),
        'key': config['rym']['google_api_key'].get(),
    }
    r = requests.get(API_URL, params=params)
    result = r.json()
    if 'items' not in result:
        return None

    items = []
    for item in result['items']:
        data = {}
        if 'pagemap' not in item:
            continue
        pagemap = item['pagemap']

        if 'musicalbum' in pagemap:
            assert(len(pagemap['musicalbum']) == 1)
            musicalbum = pagemap['musicalbum'][0]
            data['albumname'] = musicalbum['name']
            data['albumtracks'] = int(musicalbum.get('numtracks', 0))
            data['albumgenre'] = musicalbum.get('genre', '')

        if 'musicgroup' in pagemap:
            assert(len(pagemap['musicgroup']) == 1)
            group = pagemap['musicgroup'][0]
            data['groupname'] = group['name']

        if 'aggregaterating' in pagemap:
            assert(len(pagemap['aggregaterating']) == 1)
            agg = pagemap['aggregaterating'][0]

            data['ratingcount'] = int(agg['ratingcount'])
            data['ratingvalue'] = float(agg['ratingvalue'])

        data['snippet'] = item['snippet']
        data['link'] = item['link']
        items.append(data)

    for item in items:
        def get_distance(i, key, value):
            if key in i:
                return string_dist(value, i[key])
            return 1.0
        artist_dist = get_distance(item, 'groupname', artist)
        album_dist = get_distance(item, 'albumname', album)

        if artist_dist < 0.1 and album_dist < 0.1:
            return item

    if len(items) > 0:
        return items[0]
    return None
