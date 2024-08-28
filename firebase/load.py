import firebase_admin
from firebase_admin import firestore, credentials
import asyncio
import logging
import datetime
from datetime import timedelta

logger = logging.getLogger(__name__)

if not firebase_admin._apps:

    cred = credentials.Certificate('/etc/secrets/firebase-service-account-key.json')
    firebase_admin.initialize_app(cred)

async def load_artist(artist_id: str):
    try:
        db = firestore.client()
        doc_ref = db.collection('artists').document(artist_id)
        
        doc = await asyncio.to_thread(doc_ref.get)

        if doc.exists:
            artist_data = doc.to_dict()
            return artist_data
        else:
            return None
    except Exception as e:
        return None
    
async def load_all_artists():
    try:
        db = firestore.client()

        artists_ref = db.collection('artists')
        docs = await asyncio.to_thread(artists_ref.stream)

        artists = []
        for doc in docs:
            artist = doc.to_dict()
            artists.append(artist)

        return artists
    except Exception as e:
        print(f"Failed to load artists from Firebase: {e}")
        return None

async def load_artist_albums(artist_id):
    try:
        db = firestore.client()
        
        songs_ref = db.collection('albums')
        query = songs_ref.where('artist_id', '==', artist_id)
        docs = await asyncio.to_thread(query.stream)

        albums = [doc.to_dict() for doc in docs]

        return albums
    except Exception as e:
        print(f"Failed to load albums from Firestore: {str(e)}")
        return []

async def load_artist_songs(artist_id):
    try:
        db = firestore.client()
        
        songs_ref = db.collection('songs')
        query = songs_ref.where('artist_id', '==', artist_id)
        docs = await asyncio.to_thread(query.stream)

        songs = [doc.to_dict() for doc in docs]

        return songs
    except Exception as e:
        print(f"Failed to load songs from Firestore: {str(e)}")
        return []
    
async def load_artist_videos(artist_id):
    try:
        db = firestore.client()
        
        videos_ref = db.collection('videos')
        query = videos_ref.where('artist_id', '==', artist_id)
        docs = await asyncio.to_thread(query.stream)

        videos = [doc.to_dict() for doc in docs]

        return videos
    except Exception as e:
        print(f"Failed to load videos from Firestore: {str(e)}")
        return []
    
async def load_artist_photos(artist_id):
    try:
        db = firestore.client()
        
        photos_ref = db.collection('photos')
        query = photos_ref.where('artist_id', '==', artist_id)
        docs = await asyncio.to_thread(query.stream)

        photos = [doc.to_dict() for doc in docs]

        return photos
    except Exception as e:
        print(f"Failed to load photos from Firestore: {str(e)}")
        return []
    
async def load_album_comments(album_id):
    try:
        db = firestore.client()
        
        comments_ref = db.collection('comments')
        query = comments_ref.where('album_id', '==', album_id)
        docs = await asyncio.to_thread(query.stream)

        comments = [doc.to_dict() for doc in docs]

        return comments
    except Exception as e:
        print(f"Failed to load songs from Firestore: {str(e)}")
        return []
    
async def load_artist_comments(artist_id):
    try:
        db = firestore.client()
        
        comments_ref = db.collection('comments')
        query = comments_ref.where('artist_id', '==', artist_id)
        docs = await asyncio.to_thread(query.stream)

        comments = [doc.to_dict() for doc in docs]

        return comments
    except Exception as e:
        print(f"Failed to load songs from Firestore: {str(e)}")
        return []
    
async def load_latest_comments(artist_id):
    try:
        db = firestore.client()
        
        comments_ref = db.collection('comments')
        query = comments_ref.where('artist_id', '==', artist_id).order_by('updatedAt', direction=firestore.Query.DESCENDING)
        docs = await asyncio.to_thread(query.stream)
        comments = [doc.to_dict() for doc in docs]

        if not comments:
            return None
        
        for comment in comments:
            if 'updatedAt' not in comment:
                comment['updatedAt'] = None

        return comments
    except Exception as e:
        print(f"Failed to load songs from Firestore: {str(e)}")
        return None