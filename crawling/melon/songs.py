import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException
import logging
import asyncio

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 숫자 변환 함수
def convert_to_int(string: str) -> int:
    characters = ['+', 'K', 'M', 'B']
    clean_string = string
    for character in characters:
        clean_string = clean_string.replace(character, '')
    number = float(clean_string)
    if 'K' in string:
        number *= 10**3
    elif 'M' in string:
        number *= 10**6
    elif 'B' in string:
        number *= 10**9
    return int(number)

# HTTP 요청 비동기 함수
async def fetch_response(url: str, params: dict, headers: dict) -> dict:
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"Sending request to {url} with params: {params}")
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()

            logger.debug(f"Response content: {response.text[:100]}...")

            try:
                return response.json()
            except ValueError as json_error:
                logger.warning(f"Failed to parse JSON from response, assuming HTML: {json_error}")
                return response.text

        except httpx.HTTPStatusError as http_error:
            logger.error(f"HTTP error occurred: {http_error}")
            raise HTTPException(status_code=500, detail=f"HTTP error occurred: {http_error}")

async def get_song(song_id, song_title, artist_list, hearts_for_songs, artist_id, headers):
    api_url = f'https://m2.melon.com/m6/chart/streaming/card.json?cpId=AS40&cpKey=14LNC3&appVer=6.0.0&songId={song_id}'
    api_response = await fetch_response(api_url, {}, headers)
    api_data = api_response['response']

    listeners, streams = 0, 0
    if api_data['VIEWTYPE'] == "2":
        if api_data['STREAMUSER'] != '':
            listeners = convert_to_int(api_data['STREAMUSER'])
        if api_data['STREAMCOUNT'] != '':
            streams = convert_to_int(api_data['STREAMCOUNT'])

    individual_song_data = {
        'id': song_id,
        'song_title': song_title,
        'artist': artist_list,
        'likes': hearts_for_songs.get(song_id, 0),
        'listeners': listeners,
        'streams': streams,
        'artist_id': artist_id
    }

    return individual_song_data

# 노래 데이터 수집 함수
async def get_songs(artist_id: str) -> dict:
    logger.info(f"Starting to fetch song data for artist ID: {artist_id}")
    
    melon_headers = {
        'Referer': f'https://www.melon.com/artist/timeline.htm?artistId={artist_id}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
    }

    paging_url = 'https://www.melon.com/artist/songPaging.htm'
    song_url = 'https://www.melon.com/commonlike/getSongLike.json'

    paging_query = {
        'startIndex': '1',
        'pageSize': '2000',
        'orderBy': 'ISSUE_DATE',
        'artistId': artist_id
    }

    # 아티스트의 노래 목록 크롤링
    logger.info("Fetching song list...")
    paging_songs = await fetch_response(paging_url, paging_query, melon_headers)

    if isinstance(paging_songs, str):
        paging_response = BeautifulSoup(paging_songs, 'html.parser')
    else:
        logger.error("Expected JSON response but received something else.")
        raise HTTPException(status_code=500, detail="Unexpected response format")

    artist_list, song_list, song_titles = [], [], []
    for tr in paging_response.select('div.tb_list table tbody tr'):
        # 아티스트 이름 추출
        artist_name_elem = tr.select('td.t_left div.wrap.wrapArtistName #artistName a')
        if artist_name_elem:
            artist_feat = artist_name_elem[0].text
            artist_list.append(artist_feat)
        else:
            logger.warning(f"Artist name not found in tr: {tr}")

        # 곡 ID 및 제목 추출
        song_button_elem = tr.select('button.btn_icon.like')
        if song_button_elem:
            song_id = song_button_elem[0].attrs['data-song-no']
            song_title = song_button_elem[0].attrs['title']
            song_list.append(song_id)
            song_titles.append(song_title)
        else:
            logger.warning(f"Song button not found in tr: {tr}")
            continue  # song_button_elem이 없으면 다음 tr로 넘어감

    total_hearts, total_listeners, total_streams = 0, 0, 0
    song_data = []

    logger.info("Fetching like counts for songs...")
    hearts_for_songs = {}
    for song_ids in chunks(song_list, 100):
        song_id_params = {'contsIds': song_ids}
        hearts_song = await fetch_response(song_url, song_id_params, melon_headers)
        for h in hearts_song['contsLike']:
            hearts_for_songs[str(h['CONTSID'])] = h['SUMMCNT']
            hearts = h['SUMMCNT']
            total_hearts += hearts

    logger.info("Fetching listener and stream counts for songs...")
    tasks = []
    for song_id, song_title in zip(song_list, song_titles):
        task = asyncio.create_task(get_song(song_id, song_title, artist_feat, hearts_for_songs, artist_id, melon_headers))
        tasks.append(task)

    song_data = await asyncio.gather(*tasks)

    return {
        'total_hearts': total_hearts,
        'total_listeners': total_listeners,
        'total_streams': total_streams,
        'songs': song_data
    }

# 노래 ID를 나누는 유틸리티 함수
def chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]
