import urllib
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
            filename = urllib.unquote(media.filename)
            Log('File Name: {}'.format(filename))
            normalized_id = path.basename(path.dirname(filename)).split(' ')[0]
            url = self.librefanzaURL(normalized_id)
            result = JSON.ObjectFromURL(url)
            Log('Search Result: {}'.format(result))

            if 'err' not in result:
                results.Append(
                    MetadataSearchResult(
                        id="librefanza|{}".format(result['normalized_id']),
                        name=(result['normalized_id'] + ' ' + result['title']),
                        year=(result['date']),
                        score=100,
                        lang=lang
                    )
                )
        except Exception as e:
            Log(e)

    def librefanzaURL(self, query):
        return 'http://www.libredmm.com/movies/{}.json'.format(urllib.quote(query))

    def update(self, metadata, media, lang): 
        try:
            if not metadata.id.startswith('librefanza|'):
                return
            normalized_id = metadata.id[11:]
            Log.Info('Normalized ID: {}'.format(normalized_id))
            url = self.librefanzaURL(normalized_id)
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

            # Rating
            if result['review']:
                metadata.rating = float(result['review'])

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
            Log(e)
