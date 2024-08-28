import firebase_admin
from firebase_admin import credentials, firestore
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not firebase_admin._apps:

    cred = credentials.Certificate('/etc/secrets/firebase-service-account-key.json')
    firebase_admin.initialize_app(cred)

async def save_artist(artist: dict) -> bool:
    try:
        db = firestore.client()
        collection_ref = db.collection('artists')
        artist_id = artist['id']
        artist_data = {
            **artist,
            'updatedAt': firestore.SERVER_TIMESTAMP
        }

        await asyncio.to_thread(collection_ref.document(artist_id).set, artist_data)
        return True
    except Exception as e:
        return False
    
async def save_albums(albums: list) -> bool:
    try:
        db = firestore.client()
        batch = db.batch()

        for album in albums:
            album_ref = db.collection('albums').document(album['id'])
            album_data = {
                **album,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }
            batch.set(album_ref, album_data)

        await asyncio.to_thread(batch.commit)
        return True
    except Exception as e:
        return False
    
async def save_songs(songs: list) -> bool:
    try:
        db = firestore.client()
        batch = db.batch()

        for song in songs:
            song_ref = db.collection('songs').document(str(song['id']))
            batch.set(song_ref, song)

        await asyncio.to_thread(batch.commit)
        return True
    except Exception as e:
        return False
    
async def save_videos(videos: list) -> bool:
    try:
        for video in videos:
            logger.info(f"Videos from save_videos: {video}")
            
        db = firestore.client()
        batch = db.batch()

        for video in videos:
            video_ref = db.collection('videos').document(video['id'])
            video_data = {
                **video,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }
            batch.set(video_ref, video_data)

        await asyncio.to_thread(batch.commit)
        return True
    except Exception as e:
        return False
    
async def save_photos(photos: list) -> bool:
    try:
        db = firestore.client()
        batch = db.batch()

        for photo in photos:
            photo_ref = db.collection('photos').document(photo['id'])
            photo_data = {
                **photo,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }
            batch.set(photo_ref, photo_data)

        await asyncio.to_thread(batch.commit)
        return True
    except Exception as e:
        return False
    
async def save_comments(comments: list) -> bool:
    try:
        db = firestore.client()
        batch = db.batch()

        for comment in comments:
            comment_ref = db.collection('comments').document(str(comment['id']))
            comment_data = {
                **comment,
                'updatedAt': firestore.SERVER_TIMESTAMP
            }
            batch.set(comment_ref, comment_data)

        await asyncio.to_thread(batch.commit)
        return True
    except Exception as e:
        return False