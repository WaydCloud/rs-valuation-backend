import firebase_admin
from firebase_admin import firestore, credentials
import asyncio
import logging
import os
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

if not firebase_admin._apps:

    cred = credentials.Certificate.from_service_account_file(/etc/secrets/firebase-service-account-key.json)
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
