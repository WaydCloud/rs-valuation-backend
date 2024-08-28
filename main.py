import logging
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from async_processor import add_task, call_status, start_worker
from tasks import crawling_artist, crawling_albums, crawling_songs, crawling_videos, crawling_photos,crawling_comments, bring_artist, bring_all_artists, bring_albums, bring_songs, bring_album_comments, bring_artist_comments, bring_latest_comments, process_keywords, bring_videos, bring_photos
from recommendation import predict_future_streams
from pydantic import BaseModel, FieldValidationInfo, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime


#=====================#


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서 접근을 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_message(self, websocket: WebSocket, message: Dict[str, str]):
        await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, str]):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/task_status")
async def websocket_endpoint(websocket : WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            task_id = await websocket.receive_text()
            status = call_status(task_id)
            await manager.send_message(websocket, {"task_id": task_id, "status": status})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

start_worker()

@app.get("/task_status/{task_id}")
async def check_task_status_endpoint(task_id: str):
    status = call_status(task_id)
    if status == "not_found":
        raise HTTPException(status_code=404, detail="Task Not Founded")
    return {"task_id": task_id, "status": status}

#=====================#

@app.get("/crawling/melon/artist_info")
async def crawling_artist_endpoint(url: str):
    task_id = f"crawling-artist-{url}"
    add_task(task_id, crawling_artist, url)
    return {"status": "task queued", "task_id" : task_id}

@app.get("/crawling/melon/{artist_id}/albums")
async def crawling_albums_endpoint(artist_id: str):
    task_id = f"crawling-albums-{artist_id}"
    add_task(task_id, crawling_albums, artist_id)
    return {"status": "task queued", "task_id" : task_id}

@app.get("/crawling/melon/{artist_id}/songs")
async def crawling_songs_endpoint(artist_id: str):
    task_id = f"crawling-songs-{artist_id}"
    add_task(task_id, crawling_songs, artist_id)
    return {"status": "task queued", "task_id" : task_id}

@app.get("/crawling/melon/{artist_id}/videos")
async def crawling_videos_endpoint(artist_id: str):
    task_id = f"crawling-videos-{artist_id}"
    add_task(task_id, crawling_videos, artist_id)
    return {"status": "task queued", "task_id" : task_id}

@app.get("/crawling/melon/{artist_id}/photos")
async def crawling_photos_endpoint(artist_id: str):
    task_id = f"crawling-photos-{artist_id}"
    add_task(task_id, crawling_photos, artist_id)
    return {"status": "task queued", "task_id" : task_id}

@app.get("/crawling/melon/{artist_id}/comments")
async def crawling_comments_endpoint(artist_id: str):
    task_id = f"crawling-comments-{artist_id}"
    add_task(task_id, crawling_comments, artist_id)
    return {"status": "task queued", "task_id" : task_id}

@app.get("/firebase/load/artist/{artist_id}")
async def bring_artist_endpoint(artist_id: str):
    artist_data = await bring_artist(artist_id)
    return {"status": "success", "data": artist_data}

@app.get("/firebase/load/{artist_id}/albums")
async def bring_albums_endpoint(artist_id: str):
    songs_data = await bring_albums(artist_id)
    return {"status": "success", "data": songs_data}

@app.get("/firebase/load/{artist_id}/songs")
async def bring_songs_endpoint(artist_id: str):
    songs_data = await bring_songs(artist_id)
    return {"status": "success", "data": songs_data}

@app.get("/firebase/load/{artist_id}/videos")
async def bring_videos_endpoint(artist_id: str):
    videos_data = await bring_videos(artist_id)
    return {"status": "success", "data": videos_data}

@app.get("/firebase/load/{artist_id}/photos")
async def bring_photos_endpoint(artist_id: str):
    photos_data = await bring_photos(artist_id)
    return {"status": "success", "data": photos_data}

@app.get("/firebase/load/{artist_id}/{album_id}/comments")
async def bring_album_comments_endpoint(album_id: str):
    comments_data = await bring_album_comments(album_id)
    return {"status": "success", "data": comments_data}

@app.get("/firebase/load/{artist_id}/comments")
async def bring_artist_comments_endpoint(artist_id: str):
    comments_data = await bring_artist_comments(artist_id)
    return {"status": "success", "data": comments_data}

@app.get("/firebase/load/{artist_id}/comments/latest")
async def bring_latest_comment_endpoint(artist_id: str):
    comments = await bring_latest_comments(artist_id)
    return {"status": "success", "data": comments}

@app.get('/firebase/load/artists')
async def bring_all_artists_endpoint():
    artists = await bring_all_artists()
    return {"status": "success", "data": artists}

@app.post('/process/keywords/frequency')
async def process_keywords_frequency_endpoint(comments: Dict[str, Any]):
    frequencies = process_keywords(comments["data"])
    return {"status": "success", "data": frequencies}

class Metrics(BaseModel):
    followers: int
    songsReleased: int
    albumsReleased: int
    releaseFrequency: float
    totalLikes: int
    totalStreams: int
    totalComments: int
    totalVideos: int
    totalPhotos: int

class TrainingData(BaseModel):
    targetMetrics: Metrics
    compareMetrics: List[Metrics]

@app.post('/process/recommendation')
async def recommendation_endpoint(training_data: TrainingData):
    recommendation = await predict_future_streams(training_data)
    return {"status": "success", "data": recommendation} 