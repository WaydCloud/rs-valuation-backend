import httpx
import asyncio
import logging
import random
from bs4 import BeautifulSoup
from fastapi import HTTPException

# 기본 설정 및 유틸리티 함수
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HTTP 요청 비동기 함수
async def fetch_response(url: str, params: dict, headers: dict, client: httpx.AsyncClient, retries: int = 3) -> str:
    for attempt in range(retries):
        try:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}, retrying ({attempt + 1}/{retries})")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"Unexpected error occurred: {e}, retrying ({attempt + 1}/{retries})")
            await asyncio.sleep(2 ** attempt)
    raise HTTPException(status_code=500, detail="Failed to fetch data after several retries")

# 비디오 크롤링 함수
async def fetch_videos_chunk(artist_id: str, start_index: int, page_size: int, client: httpx.AsyncClient) -> list:
    video_paging_url = 'https://www.melon.com/artist/videoPaging.htm'
    melon_headers = {
        'Referer': f'https://www.melon.com/artist/timeline.htm?artistId={artist_id}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Accept': 'application/json'
    }

    paging_query = {
        'startIndex': str(start_index),
        'pageSize': str(page_size),
        'orderBy': 'ISSUE_DATE',
        'artistId': artist_id
    }

    video_data = await fetch_response(video_paging_url, paging_query, melon_headers, client)
    soup = BeautifulSoup(video_data, 'html.parser')
    videos = []

    for video_item in soup.select('li.vdo_li04'):
        video = {}
        video['artist_id'] = artist_id

        # 비디오 ID 추출
        video_link = video_item.find('a', class_='thumb')
        if video_link:
            video['id'] = video_link['href'].split(",")[1].replace("'", '')

        # 비디오 제목 추출
        video_title_tag = video_item.find('a', title=True)
        video['title'] = video_title_tag.get('title', 'N/A').replace(' - 페이지 이동', '')

        # 비디오 재생시간 추출
        playtime_tag = video_item.find('span', class_='time')
        video['playtime'] = playtime_tag.text if playtime_tag else 'N/A'

        # 비디오 썸네일 URL 추출
        video_image_tag = video_item.find('img')
        video['thumbnail_url'] = video_image_tag['src'] if video_image_tag else 'N/A'

        # 아티스트 이름 추출
        artist_name_tag = video_item.find('dd', class_='atistname').find('a', class_='play_artist')
        video['artist_name'] = artist_name_tag.text if artist_name_tag else 'N/A'

        # 조회수 추출
        view_count_tag = video_item.find('span', class_='cnt_view')
        video['view_count'] = int(view_count_tag.text.split()[-1].replace(',', '')) if view_count_tag else 0

        videos.append(video)

    return videos

# 전체 비디오 크롤링 함수
async def get_videos(artist_id: str, chunk_size: int = 1000):
    all_videos = []
    start_index = 1

    async with httpx.AsyncClient() as client:
        tasks = []

        while True:
            task = asyncio.create_task(fetch_videos_chunk(artist_id, start_index, chunk_size, client))
            tasks.append(task)
            start_index += chunk_size

            # 일단 한 번 실행 후 첫 결과 확인
            if len(tasks) == 1:
                first_result = await asyncio.gather(tasks[0])
                if not first_result[0]:  # 첫 번째 결과가 없으면 비디오가 없다는 뜻
                    break
                all_videos.extend(first_result[0])
                tasks.pop()  # 첫 번째 결과를 처리했으므로 제거

        if tasks:
            results = await asyncio.gather(*tasks)
            for result in results:
                all_videos.extend(result)
                if not result:  # 더 이상 비디오가 없을 경우 중단
                    break

    return all_videos
