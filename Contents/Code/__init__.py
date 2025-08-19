import urllib
import base64
from datetime import datetime
from os import path

def Start():
    pass

class Librefanza(Agent.Movies):
    name = 'LibreFanza'
    primary_provider = True
    languages = [
        Locale.Language.English,
        Locale.Language.Chinese,
        Locale.Language.Japanese,
        Locale.Language.NoLanguage,
    ]
    accepts_from = ['com.plexapp.agents.localmedia']
    contributes_to = [ 'com.libredmm.plex' ]
    
    def search(self, results, media, lang, manual):
        try:
            Log('Manual: {}'.format(manual))
            if manual:
                Log('Name: {}'.format(media.name))
                if media.name.startswith('http'):
                    url = media.name
                    if not url.endswith('.json'):
                        url += '.json'
                else:
                    url = self.librefanzaURL(media.name)
            else:
                filename = urllib.unquote(media.filename)
                Log('File Name: {}'.format(filename))
                normalized_id = path.basename(path.dirname(filename)).split(' ')[0]
                url = self.librefanzaURL(normalized_id)
            result = JSON.ObjectFromURL(url)
            Log('Search Result: {}'.format(result))

            if 'err' not in result:
                results.Append(
                    MetadataSearchResult(
                        id='librefanza|{}'.format(base64.b64encode(url)),
                        name=(result['normalized_id'] + ' ' + result['title']),
                        year=(result['date']),
                        score=100,
                        lang=lang
                    )
                )
        except Exception as e:
            Log.Exception('')

    def librefanzaURL(self, query):
        tokens = query.split()
        if '-' in tokens[0]:
            query = tokens[0]
        elif len(tokens) >= 2:
            query = '-'.join(tokens[:2])
        return 'http://www.libredmm.com/movies/{}.json'.format(urllib.quote(query))

    def update(self, metadata, media, lang): 
        try:
            if not metadata.id.startswith('librefanza|'):
                return
            Log.Info('ID: {}'.format(metadata.id))
            try:
                url = base64.b64decode(metadata.id[11:])
            except TypeError:
                url = self.librefanzaURL(metadata.id[11:])
            Log.Info('URL: {}'.format(url))
            result = JSON.ObjectFromURL(url)
            Log('Update Result: {}'.format(result))

            # Art
            cover_image = HTTP.Request(result['cover_image_url'])
            metadata.art[result['cover_image_url']] = Proxy.Preview(cover_image)

            # Directors
            if result['directors']:
                metadata.directors.clear()
                for director in result['directors']:
                    metadata.directors.new().name = director

            # Genres
            if result['genres']:
                metadata.genres.clear()
                for genre in result['genres']:
                    metadata.genres.add(genre)

            # Originally Avaiable At
            date = datetime.strptime(result['date'][:10], '%Y-%m-%d')
            Log('Originally Avaiable At: {}'.format(date))
            metadata.originally_available_at = date

            # Posters
            thumbnail_image = HTTP.Request(result['thumbnail_image_url'])
            metadata.posters[result['thumbnail_image_url']] = Proxy.Preview(thumbnail_image)

            # Roles
            if result['actresses']:
                metadata.roles.clear()
                for actress in result['actresses']:
                    role = metadata.roles.new()
                    role.name = actress['name']
                    if actress['image_url']:
                        role.photo = actress['image_url']

            # Studio
            if result['makers']:
                metadata.studio = result['makers'][0]

            # Summary
            metadata.summary = result['description']

            # Title
            metadata.title = '{} {}'.format(result['normalized_id'], result['title'])

            # Year
            metadata.year = (int)(result['date'].split('-')[0])

        except Exception as e:
            Log.Exception('')
