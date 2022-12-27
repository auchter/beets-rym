
# beets-rym

Fetch and store the following info from RYM for each album:

- `rym_url`: URL for the release on RYM
- `rym_genre`: Primary genre from RYM
- `rym_rating_value`: Album overall rating
- `rym_rating_count`: Number of ratings


## Example

```
% beet ls -a -f '$albumartist - $album - $rym_genre - $rym_rating_value' | shuf | head -5
Craig Taborn & Vadim Neselovskyi - Da'at: The Book Beri'ah, Volume 11 - Modern Classical - 3.43
The Magic I.D. - Till My Breath Gives Out - Post-Rock - 3.68
Wolves in the Throne Room - Primordial Arcana - Atmospheric Black Metal - 3.49
Kayo Dot - Dowsing Anemone With Copper Tongue - Experimental Rock - 3.66
Oranssi Pazuzu - Mestarin kynsi - Avant-Garde Metal - 3.72
```

## Usage

Run `beet rym [query]` to fetch info for all albums matching the query.

## Configuration

### Search API

This plugin requires you to create a Google Custom Search API with certain
settings. You can do this from the [Programmable Search Engine Control Panel](https://programmablesearchengine.google.com/controlpanel/all).

Steps:

- Add a new search engine
- Under "Search Features", add `*.rateyourmusic.com/release/*` to the list of sites to search
- Click "All Search Features settings"; under the "Page Restricts" section, add the following to the list of "Restrict Pages using Schema.org Types":
    - `MusicAlbumReleaseType`
    - `MusicAlbum`
    - `MusicRelease`
    - `MusicRecording`
- Note the "Search Engine ID", this is `google_search_engine_id` in the beets-rym configuration
- Obtain an API key, this is `google_api_key` in the beets-rym configuration

### beets config

In your config file, add a `[rym]` section. The following options are supported:

- `auto` (default: `true`): Automatically fetch info for newly imported albums
- `google_api_key`: The API key from the prior section
- `google_search_engine_id`: The Search Engine ID from the prior section
