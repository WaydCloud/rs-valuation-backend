import firebase_admin
from firebase_admin import firestore, credentials
import asyncio
import logging

logger = logging.getLogger(__name__)

if not firebase_admin._apps:
    cred_object = {
        "type": "service_account",
        "project_id": "redslippers-entertainment",
        "private_key_id": "e028c0e686abc3e287dcbd74fc065d402839db2b",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDQk7z0+ywdJL7S\nBfoTLgAuOgBVNqR5aCUjQwDwnMQebQxsr2cC0nhUT6M6GfNt4Su+1n8O/NDL9HzM\n5Aw9x29knbRRVv5rpda8SZVIpW5qMiKF3HQ3pLrcLyDp2BpUGQ+LemhoKJaMjVrr\nxA9wV44CVCVeFqMuhJ3QtqFQhr8GO/2H9pG6LNRsi6GdupK2zUDt8JnMiJuKMXhB\nSxdiIZ+FOGcUUApcLOIxUPAA44LRbiH1RWijtHBR3Owez8L++0twF9yNpTlBQCYv\nKhOxIk8voNpED2taQmqXknXfInpJ0f71ZW3D+E9ANJF+rM6g2T8ywknJZuf4OvDP\nKOC35zefAgMBAAECggEAChktC9thTmPqDTcW3Xjbr2FFhNqpaetd6PAkioG8iRCU\nimqPnTZddw+IApchDw/Y01uFOU+KOGW06SKdaRxPy1pLUajZlpKn6+PQI31G9ENL\nIpoC0nLaTTDG8itxUuMHuqQJjAlzCIkLfuC2MqU6jehPCtgjvGvVTDabZs+vTfjh\nJ9vUBWIjIilMpYeAguyR2fhVUNSHdWzV65mJhiX1AOrBg9ftyvCjMvd1stEeYGJT\n2GwGEUqW4AchKktpjWmrDmdLeAIWZmZiQ2G1chf04dH/bSnBCcb3WOQGX2Q3hiDZ\nwhjM7XCZ2AP0bUhFmYUnfPIGO5u4XMGoHbQ+spDPWQKBgQD23nsv8jtTkHqRi/PE\n6zDltFCmOo3SDdSJuwTMg65zuHgwG8HjOpheb7hxoexWmd7Go9SXWBo+s1VmN9bK\nMZ0gAi11+/KsAmqzthitvPq53c+I4Tpy7uiwWWjn0rQNXPtNvaHTf2K1zaeMtDmd\nN+iuoFFmHVdfIlvuHNxlewSDbQKBgQDYSq7yWAbC6b9ZQrzgepnK7KP2YYDGQyL5\nn5JIoqBrtYjAkFxSTlK/pz2X7KfZE0cMWhWHNHmBM4vdPsmLQHtB7vn7ezksyum5\npvpBvngvcBUmiBeECOttSPGKi7KwL166qWXuKA+6J3QNfDbFzHBcxFdMljMyoUQI\nefRYes6zuwKBgDnTPTmq3LijNAKZrJzolkiH5wg42PVl5e3pD6O0CI30nLpwFgda\nt0wPkT2Utx5F5ofS4j4dFfCv4wYReE9eNbbEq89iF6Kw4jt8IOW5SWV2DmG6mA1J\n5tk/6DG9Cg3DRN4d2CUJRp7dMCzmHkS0Tt1wkgCASPHww2XP/tQKb7E1AoGAUOqv\nxI5WCTl1kqk7DCgRvS8GsDgN+x5GyWh/S5k7ts/1V0UqpMgUgQrKKjopGTbzD5Xs\nE+b3xfRI0P6aW/RFqIcFEqYo368R/ZiQa2QchnLCFuY3FfhYS0xMwO4+bVdrcx3I\num5WY+g6rIjZ3On851e06TwP71MRprIpTai0B90CgYANHkSKGKaLyjlJxJBDMszE\nr1ifxRv/gO46kNt7Q+dG45lLvLknBiqG5FEOn1nFFA/9kVqftfrypG9beKdIhtqO\nbZIR2y6nmVwhxWmZsv+rLu0uagUYqJY/i1Td/x0r7h0M6f6XCjEttg68Gc+IcamC\np6mV9uGkAoG7Rlk+ZukaUw==\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk-yw777@redslippers-entertainment.iam.gserviceaccount.com",
        "client_id": "105271415114807532915",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-yw777%40redslippers-entertainment.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }

    cred = credentials.Certificate(cred_object)
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