import httpx
import asyncio
import logging
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

# 포토 크롤링 함수
async def fetch_photos_chunk(artist_id: str, start_index: int, page_size: int, client: httpx.AsyncClient) -> list:
    photo_paging_url = 'https://www.melon.com/artist/photoPaging.htm'
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

    photo_data = await fetch_response(photo_paging_url, paging_query, melon_headers, client)
    soup = BeautifulSoup(photo_data, 'html.parser')
    photos = []

    for photo_item in soup.select('li.photo02_li'):
        photo = {}
        photo['artist_id'] = artist_id

        # 포토 ID 추출
        photo_id = photo_item.find('a', class_='thumb').get('href').split(",")[1].replace("'",'')
        photo['id'] = photo_id

        # 포토 제목 추출
        title_tag = photo_item.find('a', class_='thumb')
        photo['title'] = title_tag.get('title', 'N/A')

        # 포토 이미지 URL 추출
        img_tag = photo_item.find('img')
        photo['image_url'] = img_tag['src'] if img_tag else 'N/A'

        photos.append(photo)

    return photos

# 전체 포토 크롤링 함수
async def get_photos(artist_id: str, chunk_size: int = 1000):
    all_photos = []
    start_index = 1

    async with httpx.AsyncClient() as client:
        tasks = []

        while True:
            task = asyncio.create_task(fetch_photos_chunk(artist_id, start_index, chunk_size, client))
            tasks.append(task)
            start_index += chunk_size

            # 일단 한 번 실행 후 첫 결과 확인
            if len(tasks) == 1:
                first_result = await asyncio.gather(tasks[0])
                if not first_result[0]:  # 첫 번째 결과가 없으면 포토가 없다는 뜻
                    break
                all_photos.extend(first_result[0])
                tasks.pop()  # 첫 번째 결과를 처리했으므로 제거

        if tasks:
            results = await asyncio.gather(*tasks)
            for result in results:
                all_photos.extend(result)
                if not result:  # 더 이상 포토가 없을 경우 중단
                    break

    return all_photos

# 메인 함수 (VS Code에서 실행 버튼을 눌러서 실행할 때 사용)
if __name__ == "__main__":
    artist_id = "2403002"  # 테스트할 아티스트 ID
    photos = asyncio.run(get_photos(artist_id))
    print(f"Retrieved {len(photos)} photos.")
