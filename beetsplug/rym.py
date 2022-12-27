from beets import plugins, config, dbcore, ui
from beets.autotag.hooks import string_dist
from beets.dbcore import types
import requests
import pprint


API_URL = 'https://customsearch.googleapis.com/customsearch/v1/siterestrict'

class RymPlugin(plugins.BeetsPlugin):
    def __init__(self):
        super().__init__()
        self.config.add({
            'auto': True,
            'google_api_key': '',
            'google_search_engine_id': '',
        })
        self.config['google_api_key'].redact = True

        self.album_types = {
            'rym_url': types.STRING,
            'rym_genre': types.STRING,
            'rym_rating_count': types.INTEGER,
            'rym_rating_value': types.Float(2),
        }

        if self.config['auto']:
            self.register_listener('album_imported', self.import_rym)

    def commands(self):
        cmd = ui.Subcommand('rym', help='Import genres and ratings from RYM')

        def func(lib, opts, args):
            query = ui.decargs(args)
            albums = lib.albums(query)
            for album in albums:
                self.import_rym(lib, album)

        cmd.func = func
        return [cmd]

    def import_rym(self, lib, album):
        artist = album['albumartist']
        album_name = album['album']

        if album.get('rym_url', '') != '':
            self._log.debug(f"skipping {artist} - {album_name} since rym_url is populated")
            return

        result = rym_query(artist, album_name, log)
        if result is None:
            self._log.warning(f"No result for {artist} - {album_name}")
            return

        album['rym_url'] = result['link']
        album['rym_genre'] = result.get('albumgenre', '')
        album['rym_rating_count'] = result.get('ratingcount', 0)
        album['rym_rating_value'] = result.get('ratingvalue', 0.0)
        album.store()


def rym_query(artist, album, log):
    params = {
        'q': ' '.join([artist, album]),
        'cx': self.config['google_search_engine_id'].get(),
        'key': self.config['google_api_key'].get(),
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

        data['snippet'] = item['snippet']
        data['link'] = item['link']

        if 'musicalbum' in pagemap:
            if len(pagemap['musicalbum']) > 1:
                log.warning("unexpected count for musicalbum in %s" % data['link'])

            musicalbum = pagemap['musicalbum'][0]
            data['albumname'] = musicalbum['name']
            data['albumtracks'] = int(musicalbum.get('numtracks', 0))
            data['albumgenre'] = musicalbum.get('genre', '')

        if 'musicgroup' in pagemap:
            if len(pagemap['musicgroup']) > 1:
                log.warning("unexpected count for musicgroup in %s" % data['link'])

            group = pagemap['musicgroup'][0]
            data['groupname'] = group['name']

        if 'aggregaterating' in pagemap:
            if len(pagemap['aggregaterating']) > 1:
                log.warning("unexpected count for aggregaterating in %s" % data['link'])
            agg = pagemap['aggregaterating'][0]

            data['ratingcount'] = int(agg['ratingcount'])
            data['ratingvalue'] = float(agg['ratingvalue'])

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
