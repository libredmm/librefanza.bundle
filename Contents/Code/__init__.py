import urllib
import base64
from datetime import datetime
from os import path


def Start():
    pass


class Librefanza(Agent.Movies):
    name = "LibreFanza"
    primary_provider = True
    languages = [
        Locale.Language.English,
        Locale.Language.Chinese,
        Locale.Language.Japanese,
        Locale.Language.NoLanguage,
    ]
    accepts_from = ["com.plexapp.agents.localmedia"]
    contributes_to = ["com.libredmm.plex"]

    def search(self, results, media, lang, manual):
        try:
            Log("Manual: {}".format(manual))
            if manual and media.name:
                Log("Name: {}".format(media.name))
                if media.name.startswith("http"):
                    url = media.name
                    if not url.endswith(".json"):
                        url += ".json"
                else:
                    url = self.librefanzaURL(media.name)
            elif media.filename:
                filename = urllib.unquote(media.filename)
                Log("File Name: {}".format(filename))
                normalized_id = path.basename(path.dirname(filename)).split(" ")[0]
                url = self.librefanzaURL(normalized_id)
            else:
                Log.Error("Search got neither a name nor a filename")
                return
            if not url:
                Log.Error("Could not build a query URL")
                return
            result = JSON.ObjectFromURL(url)
            Log("Search Result: {}".format(result))

            if "err" in result:
                Log.Error("LibreDMM error for {}: {}".format(url, result["err"]))
                return
            date = result.get("date") or ""
            results.Append(
                MetadataSearchResult(
                    id="librefanza|{}".format(base64.b64encode(url)),
                    name=u"{} {}".format(
                        result.get("normalized_id") or "", result.get("title") or ""
                    ).strip(),
                    year=int(date[:4]) if date[:4].isdigit() else None,
                    score=100,
                    lang=lang,
                )
            )
        except Exception as e:
            Log.Exception("Search failed")

    def librefanzaURL(self, query):
        tokens = query.split()
        if not tokens:
            return None
        if "-" in tokens[0]:
            query = tokens[0]
        elif len(tokens) >= 2:
            query = "-".join(tokens[:2])
        if isinstance(query, unicode):
            query = query.encode("utf-8")
        return "http://www.libredmm.com/movies/{}.json".format(urllib.quote(query))

    def update(self, metadata, media, lang):
        try:
            if not metadata.id.startswith("librefanza|"):
                return
            Log.Info("ID: {}".format(metadata.id))
            try:
                url = base64.b64decode(metadata.id[len("librefanza|"):])
            except TypeError:
                url = self.librefanzaURL(metadata.id[len("librefanza|"):])
            if not url or not url.startswith("http"):
                Log.Error("Bad update URL from id {}".format(metadata.id))
                return
            Log.Info("URL: {}".format(url))
            result = JSON.ObjectFromURL(url)
            Log("Update Result: {}".format(result))

            if "err" in result:
                Log.Error("LibreDMM error for {}: {}".format(url, result["err"]))
                return

            # Cheap text fields first, so a failing image download later
            # cannot abort an otherwise complete update.

            # Directors
            if result.get("directors"):
                metadata.directors.clear()
                for director in result["directors"]:
                    metadata.directors.new().name = director

            # Genres
            if result.get("genres"):
                metadata.genres.clear()
                for genre in result["genres"]:
                    metadata.genres.add(genre)

            # Originally Avaiable At / Year
            if result.get("date"):
                date = datetime.strptime(result["date"][:10], "%Y-%m-%d")
                Log("Originally Avaiable At: {}".format(date))
                metadata.originally_available_at = date
                metadata.year = date.year

            # Roles
            if result.get("actresses"):
                metadata.roles.clear()
                for actress in result["actresses"]:
                    role = metadata.roles.new()
                    role.name = actress.get("name")
                    if actress.get("image_url"):
                        role.photo = actress["image_url"]

            # Studio
            if result.get("makers"):
                metadata.studio = result["makers"][0]

            # Summary
            if result.get("description"):
                metadata.summary = result["description"]

            # Title
            metadata.title = u"{} {}".format(
                result.get("normalized_id") or "", result.get("title") or ""
            ).strip()

            # Art
            art_url = result.get("cover_image_url")
            if art_url:
                try:
                    metadata.art[art_url] = Proxy.Preview(HTTP.Request(art_url))
                except Exception:
                    Log.Exception("Failed to fetch art {}".format(art_url))

            # Posters
            poster_url = result.get("thumbnail_image_url")
            if poster_url:
                try:
                    metadata.posters[poster_url] = Proxy.Preview(
                        HTTP.Request(poster_url)
                    )
                except Exception:
                    Log.Exception("Failed to fetch poster {}".format(poster_url))

        except Exception as e:
            Log.Exception("Update failed")
