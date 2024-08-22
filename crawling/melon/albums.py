import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException
import logging
import asyncio
from datetime import datetime
import random

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Linux; Android 11; Pixel 5 Build/RQ3A.210705.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
]

# HTTP 요청 비동기 함수
async def fetch_response(url: str, params: dict, headers: dict) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            try:
                return response.json()
            except ValueError as json_error:
                return response.text

        except httpx.HTTPStatusError as http_error:
            logger.error(f"HTTP error occurred: {http_error}")
            raise HTTPException(status_code=500, detail=f"HTTP error occurred: {http_error}")
        
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail="Unexpected error occurred while fetching data")
        

# 앨범별 좋아요 수 크롤링 함수
async def fetch_album_likes(album_list, melon_headers):
    album_url = 'https://www.melon.com/commonlike/getAlbumLike.json'

    tasks = []
    for album_ids in chunks(album_list, 100):
        album_id_params = {'contsIds': album_ids}
        tasks.append(fetch_response(album_url, album_id_params, melon_headers))

    responses = await asyncio.gather(*tasks)

    likes_for_albums = {}
    for response in responses:
        for album in response['contsLike']:
            likes_for_albums[str(album['CONTSID'])] = album['SUMMCNT']

    return likes_for_albums

# 앨범 데이터 수집 함수
async def get_albums(artist_id: str) -> dict:
    logger.info(f"Crawling Albums for {artist_id}")
    
    melon_headers = {
        'Referer': f'https://www.melon.com/artist/timeline.htm?artistId={artist_id}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36',
        'Accept': 'application/json'
    }

    # user_agent = random.choice(user_agents)
    # melon_headers = {'User-Agent': user_agent}

    paging_url = 'https://www.melon.com/artist/albumPaging.htm'
    paging_query = {
        'startIndex': '1',
        'pageSize': '2000',
        'orderBy': 'ISSUE_DATE',
        'artistId': artist_id
    }

    # 아티스트의 앨범 목록 크롤링
    logger.info("Fetching album list...")
    paging_songs = await fetch_response(paging_url, paging_query, melon_headers)

    paging_response = BeautifulSoup(paging_songs, 'html.parser')
    albums = []
    album_ids = []
    release_dates = []

    for album_li in paging_response.select('li.album11_li'):
        album = {}
        
        # 앨범 ID 추출
        album_link = album_li.find('a', class_='thumb')
        if album_link:
            album_id = album_link['href'].split("'")[1]
            album['id'] = album_id
            album_ids.append(album_id)
            
        # 앨범명 추출
        album_name_tag = album_li.find('a', class_='ellipsis')
        album['album_name'] = album_name_tag.text if album_name_tag else 'N/A'
        
        # 아티스트명 추출
        artist_name_tag = album_li.find('a', class_='play_artist')
        album['artist_name'] = artist_name_tag.text if artist_name_tag else 'Various Artists'
        
        # 앨범 발매일 추출
        release_date_tag = album_li.find('span', class_='cnt_view')
        if release_date_tag and release_date_tag.text:
            try:
                release_date = release_date_tag.text
                release_dates.append(datetime.strptime(release_date, "%Y.%m.%d"))
                album['release_date'] = release_date
            except ValueError:
                logger.warning(f"Invalid date format for album {album_id}: {release_date}")
                album['release_date'] = 'N/A'
        else:
            album['release_date'] = 'N/A'
        
        # 앨범 이미지 URL 추출
        album_image_tag = album_li.find('img')
        album['album_image_url'] = album_image_tag['src'] if album_image_tag else 'N/A'
        
        # 좋아요 수 추출
        like_count_tag = album_li.find('strong', class_='none')
        album['like_count'] = like_count_tag.next_sibling.strip() if like_count_tag else '0'
        
        # 곡 수 추출
        total_songs_tag = album_li.find('span', class_='tot_song')
        album['total_songs'] = int(total_songs_tag.text.replace('곡','')) if total_songs_tag else 0

        album['artist_id'] = artist_id
        
        albums.append(album)
    
    # 앨범별 좋아요 수 가져오기
    likes_for_albums = await fetch_album_likes(album_ids, melon_headers)
    for album in albums:
        album['like_count'] = likes_for_albums.get(album['id'], 0)
    
    return albums

# 노래 ID를 나누는 유틸리티 함수
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
