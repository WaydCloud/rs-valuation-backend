import logging
from crawling.melon.artist_info import get_artist_info
from crawling.melon.albums import get_albums
from crawling.melon.songs import get_songs
from firebase.save import save_artist, save_albums, save_songs
from firebase.load import load_artist, load_all_artists, load_artist_songs

logger = logging.getLogger(__name__)

async def crawling_artist(url: str):
    try:
        artist_info = await get_artist_info(url)
        if artist_info:
            success = await save_artist(artist_info)
            if success:
                logger.info(f"{artist_info.get('artist_name')} Saved!")
            else:
                logger.error(f"Failed to save {artist_info.get('artist_name')}")
        else:
            logger.error(f"Failed to get artist information from {url}")
    except Exception as e:
        logger.error(f"Exception : {str(e)}")

async def crawling_albums(artist_id: str):
    try:
        albums = await get_albums(artist_id)
        if albums:
            success = await save_albums(albums)
            if success:
                logger.info(f"{len(albums)} Albums Saved!")

                artist = await load_artist(artist_id)
                if artist:
                    debut_date = artist.get('debut_date', '')
                    first_album_released = min(album['release_date'] for album in albums)
                    if not debut_date or debut_date > first_album_released:
                        artist['debut_date'] = first_album_released
                        save_success = await save_artist(artist)
                        if save_success:
                            logger.info(f"Updated debut date for artist {artist_id} to {first_album_released}")
                        else:
                            logger.error(f"Failed to update debut date for artist {artist_id}")

                    logger.info(f"Artist Debut Date {debut_date}, First Album Released {first_album_released}")
            else:
                logger.error(f"Failed to save {len(albums)} Albums")
        else:
            logger.error(f"Failed to get albums for {artist_id}")
    except Exception as e:
        logger.error(f"Exception : {str(e)}")

async def crawling_songs(artist_id: str):
    try:
        songs_response = await get_songs(artist_id)
        if songs_response:
            songs = songs_response['songs']
            success = await save_songs(songs)
            if success:
                logger.info(f"{len(songs)} Songs Saved!")
            else:
                logger.error(f"Failed to save {len(songs)} Songs")
        else:
            logger.error(f"Failed to get songs for {artist_id}")
    except Exception as e:
        logger.error(f"Exception : {str(e)}")

async def bring_artist(artist_id: str):
    try:
        artist_info = await load_artist(artist_id)
        if artist_info:
            logger.info(f"{artist_info.get('artist_name')} Loaded!")
            return artist_info
        
        logger.error(f"Failed to load {artist_id}")
        return None
    except Exception as e:
        logger.error(f"Connection failed to load {artist_id}")
        return None
    
async def bring_songs(artist_id: str):
    try:
        songs = await load_artist_songs(artist_id)
        if songs:
            logger.info(f"{len(songs)} Loaded!")
            return songs
        
        logger.error(f"Failed to load {artist_id} Songs")
        return None
    except Exception as e:
        logger.error(f"Connection failed to load {artist_id} Songs")
        return None
    
async def bring_all_artists():
    try:
        artists = await load_all_artists()
        if artists:
            logger.info(f"{len(artists)} Artists have been Loaded!")
            return artists
        logger.error(f"Failed to load artists")
        return None
    except Exception as e:
        logger.error(f"Connection failed to load artists")
        return None
