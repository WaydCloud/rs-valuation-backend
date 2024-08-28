import logging
from crawling.melon.artist_info import get_artist_info
from crawling.melon.albums import get_albums
from crawling.melon.songs import get_songs
from crawling.melon.comments import get_comments
from crawling.melon.videos import get_videos
from crawling.melon.photos import get_photos
from firebase.save import save_artist, save_albums, save_songs, save_comments, save_videos, save_photos
from firebase.load import load_artist, load_all_artists, load_artist_songs, load_artist_albums, load_artist_comments, load_latest_comments, load_album_comments, load_artist_videos, load_artist_photos
import asyncio

logging.basicConfig(level=logging.INFO)
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

async def crawling_videos(artist_id: str):
    try:
        videos = await get_videos(artist_id)
        for video in videos:
            logger.info(f"VIDEO! {video}")
        if videos:
            success = await save_videos(videos)
            logger.info(f"Video SAVE Success?? {success}")
            if success:
                logger.info(f"{videos.get('artist_name')} Saved!")
            else:
                logger.error(f"Failed to save {videos.get('artist_name')}")
        else:
            logger.error(f"Failed to get artist information from {artist_id}")
    except Exception as e:
        logger.error(f"Exception : {str(e)}")

async def crawling_photos(artist_id: str):
    try:
        photos = await get_photos(artist_id)
        if photos:
            success = await save_photos(photos)
            if success:
                logger.info(f"{photos.get('artist_name')} Saved!")
            else:
                logger.error(f"Failed to save {photos.get('artist_name')}")
        else:
            logger.error(f"Failed to get artist information from {artist_id}")
    except Exception as e:
        logger.error(f"Exception : {str(e)}")

async def crawling_comments(artist_id: str):
    try:
        albums = await bring_albums(artist_id)
        logger.info(f"Albums for Comments : {albums}")
        if albums:
            all_comments = []
            
            # 병렬로 댓글 수집
            tasks = [get_comments(artist_id, album['id']) for album in albums]
            all_comments_responses = await asyncio.gather(*tasks)

            for album, comments in zip(albums, all_comments_responses):
                if comments:
                    all_comments.append(comments)
                    success = await save_comments(comments)
                    if success:
                        logger.info(f"{len(comments)} Comments Saved for Album {album.id}")
                    else:
                        logger.error(f"Failed to save {len(comments)} Comments for Album {album.id}")
                else:
                    logger.error(f"Failed to get comments for Album {album.id}")
        else:
            logger.error(f"Failed to get albums for artist {artist_id}")
    except Exception as e:
        logger.error(f"Exception: {str(e)}")


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
    
async def bring_albums(artist_id: str):
    try:
        albums = await load_artist_albums(artist_id)
        if albums:
            logger.info(f"{len(albums)} Loaded!")
            return albums
        
        logger.error(f"Failed to load {artist_id} Albums")
        return None
    except Exception as e:
        logger.error(f"Connection failed to load {artist_id} Albums")
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
    
async def bring_videos(artist_id: str):
    try:
        videos = await load_artist_videos(artist_id)
        if videos:
            logger.info(f"{len(videos)} Loaded!")
            return videos
        
        logger.error(f"Failed to load {artist_id} Videos")
        return None
    except Exception as e:
        logger.error(f"Connection failed to load {artist_id} Videos")
        return None 

async def bring_photos(artist_id: str):
    try:
        photos = await load_artist_photos(artist_id)
        if photos:
            logger.info(f"{len(photos)} Loaded!")
            return photos
        
        logger.error(f"Failed to load {artist_id} Photos")
        return None
    except Exception as e:
        logger.error(f"Connection failed to load {artist_id} Photos")
        return None  
    
async def bring_album_comments(album_id: str):
    try:
        comments = await load_album_comments(album_id)
        if comments:
            logger.info(f"{len(comments)} Loaded for Album({album_id})!")
            return comments
        
        logger.error(f"Failed to load Album({album_id}) Comments")
        return None
    except Exception as e:
        logger.error(f"Connection failed to load Album({album_id}) Comments")
        return None
    
async def bring_artist_comments(artist_id: str):
    try:
        comments = await load_artist_comments(artist_id)
        if comments:
            logger.info(f"{len(comments)} Loaded for Artist({artist_id})!")
            return comments
        
        logger.error(f"Failed to load Artist({artist_id}) Comments")
        return None
    except Exception as e:
        logger.error(f"Connection failed to load Artist({artist_id}) Comments")
        return None
    
async def bring_latest_comments(artist_id: str):
    try:
        comments = await load_latest_comments(artist_id)
        if comments:
            logger.info(f"Latest comment for Artist({artist_id}) : {comments[0]['updatedAt']}({len(comments)} comments)")
            return comments
        logger.error(f"Failed to load Artist({artist_id}) Latest Comment")
        return None
    except Exception as e:
        logger.error(f"Connection failed to load Artist({artist_id}) Latest Comment")
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
    
from collections import Counter
from typing import Any, List, Dict
from konlpy.tag import Okt
from sklearn.feature_extraction.text import TfidfVectorizer

def process_keywords(comments: List[Dict[str, Any]], min_frequency: int = 2, min_tfidf = 0.1) -> dict: 
    okt = Okt()
    
    # 사전에 정의된 불용어 리스트
    custom_stopwords = set([
        "하다", "있다", "되다", "이다", "않다", "없다", "같다", "보다", "가다", "오다", "많다",  # 불용어
        "또", "요", "오", "제", "내", "스", "그", "스원", "눈", "나", "것", "원님" # 추가 불필요 단어
    ])

    def extract_keywords(text: str) -> List[str]:
        # 텍스트를 형태소 분석하고 명사와 형용사를 추출
        morphs = okt.pos(text, stem=True)
        keywords = [word for word, pos in morphs if pos in ['Noun', 'Adjective']]
        return keywords
    
    all_keywords = []

    # 각 댓글을 개별적으로 처리
    for comment_dict in comments:
        comment = comment_dict["content"]  # 딕셔너리에서 실제 댓글 내용 추출
        keywords = extract_keywords(comment)
        all_keywords.extend(keywords)

    # 길이가 1 이하인 단어를 자동 불용어로 추가
    auto_stopwords = set(word for word in all_keywords if len(word) <= 1)
    all_stopwords = custom_stopwords.union(auto_stopwords)
    
    def filter_keywords(keywords: List[str], stopwords: set) -> List[str]:
        # 불용어를 제외한 키워드 필터링
        filtered_keywords = [word for word in keywords if word not in stopwords]
        return filtered_keywords
    
    filtered_keywords = filter_keywords(all_keywords, all_stopwords)

    # TF-IDF 벡터화
    vectorizer = TfidfVectorizer()
    comment_texts = [comment_dict["content"] for comment_dict in comments]  # TF-IDF 적용을 위한 댓글 리스트
    X = vectorizer.fit_transform(comment_texts)

    # TF-IDF 값이 높은 키워드 필터링
    tfidf_scores = dict(zip(vectorizer.get_feature_names_out(), X.sum(axis=0).tolist()[0]))
    tfidf_filtered_keywords = [word for word in filtered_keywords if tfidf_scores.get(word, 0) >= min_tfidf]
        
    def calculate_keyword_frequencies(keywords: List[str], min_frequency: int) -> dict:
        # 최종적으로 필터링된 키워드의 빈도 계산
        counter = Counter(keywords)
        filtered_counter = {word: freq for word, freq in counter.items() if freq >= min_frequency}
        return filtered_counter
    
    keyword_frequencies = calculate_keyword_frequencies(tfidf_filtered_keywords, min_frequency)
    return keyword_frequencies

