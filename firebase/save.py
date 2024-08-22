import firebase_admin
from firebase_admin import credentials, firestore
import asyncio
import os

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

async def save_artist(artist: dict) -> bool:
    try:
        db = firestore.client()
        collection_ref = db.collection('artists')
        artist_id = artist['id']

        await asyncio.to_thread(collection_ref.document(artist_id).set, artist)
        return True
    except Exception as e:
        return False
    
async def save_albums(albums: list) -> bool:
    try:
        db = firestore.client()
        batch = db.batch()

        for album in albums:
            album_ref = db.collection('albums').document(album['id'])
            batch.set(album_ref, album)

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
