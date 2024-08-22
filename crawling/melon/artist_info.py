import aiohttp
from aiohttp import TCPConnector, ClientSession
import asyncio
from bs4 import BeautifulSoup
import random
from urllib.parse import urlparse, parse_qs
import logging
import time
from typing import Optional, Dict

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User-Agent 리스트
user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Linux; Android 11; Pixel 5 Build/RQ3A.210705.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
]

# dt 텍스트에 대한 매핑 함수
def map_key_from_dt(dt_text):
    mapping = {
        "본명": "real_name",
        "국적": "nationality",
        "생일": "birthday",
        "별자리": "zodiac",
        "데뷔": "debut_date",
        "활동년대": "years_active",
        "유형": "artist_type_gender",
        "장르": "genres",
        "소속사명": "company",
        "소속그룹": "affiliated_groups",
    }
    return mapping.get(dt_text, None)

# 유형과 성별 분리 함수
def split_type_and_gender(text):
    import re
    pattern = r'(솔로|그룹)\s*\|\s*(남성|여성|혼성)'
    match = re.search(pattern, text)
    if match:
        return match.group(1), match.group(2)
    return None, None

# 정보 추출 함수
def extract_info(section):
    info = {}
    for dl in section.find_all("dl", class_="list_define"):
        for dt, dd in zip(dl.find_all("dt"), dl.find_all("dd")):
            key = map_key_from_dt(dt.get_text(strip=True))
            value = dd.get_text(strip=True)

            if key == "debut_date":
                # 'YYYY.MM|string' 형식 처리
                if '|' in value:
                    value = value.split('|')[0].strip() + '.01'
                elif len(value) == 7:  # 'YYYY.MM' 형식
                    value = value + '.01'
                
                info[key] = value
            elif key == "artist_type_gender":
                artist_type, gender = split_type_and_gender(value)
                if artist_type:
                    info["artist_type"] = artist_type
                if gender:
                    info["gender"] = gender
            elif key:
                info[key] = value
                
    return info

# 수상이력 추출 함수
def extract_awards(section):
    return [dd.get_text(strip=True) for dd in section.find_all("dd")]

# 아티스트 정보를 크롤링하는 함수
async def get_artist_info(url: str, max_retries=20, delay=0.5) -> Optional[Dict[str, Optional[str]]]:
    attempt = 0

    while attempt < max_retries:
        try:
            logger.info(f"Attempt {attempt + 1} of {max_retries} - Starting to crawl artist information from URL: {url}")

            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            artist_id = query_params.get("artistId", [None])[0]
            
            if not artist_id:
                logger.error("Invalid URL: artistId not found")
                raise ValueError("Invalid URL: artistId not found")
            
            detail_url = f"https://www.melon.com/artist/detail.htm?artistId={artist_id}"

            user_agent = random.choice(user_agents)
            headers = {'User-Agent': user_agent}

            connector = TCPConnector(ssl=False)
            async with ClientSession(connector=connector) as session:
                async with session.get(detail_url, headers=headers) as response:
                    response.raise_for_status()
                    logger.info("Successfully fetched artist page")
                    content = await response.read()
                    soup = BeautifulSoup(content, "html.parser")

                    artist = {}
                    artist['id'] = artist_id

                    # 아티스트 이름
                    artist_name_tag = soup.find("p", class_="title_atist")
                    artist['artist_name'] = artist_name_tag.contents[1].strip() if artist_name_tag else None
                
                    # 프로필 이미지
                    wrap_thumb_div = soup.find("div", class_="wrap_thumb")

                    if wrap_thumb_div:
                        profile_img_tag = wrap_thumb_div.find("img")
                        if profile_img_tag and profile_img_tag.has_attr('src'):
                            artist['img'] = profile_img_tag['src']
                        else:
                            artist['img'] = None
                    else:
                        artist['img'] = None

                    # 수상이력
                    award_section = soup.find("div", id="d_artist_award")
                    if award_section:
                        artist['awards'] = extract_awards(award_section)

                    # 소개
                    intro_section = soup.find("div", id="d_artist_intro")
                    if intro_section:
                        artist['artist_intro'] = intro_section.get_text(strip=True)

                    # 활동정보
                    activity_section = soup.find("div", class_="section_atistinfo03")
                    if activity_section:
                        artist.update(extract_info(activity_section))

                    # 신상정보
                    info_section = soup.find("div", class_="section_atistinfo04")
                    if info_section:
                        artist.update(extract_info(info_section))

                    # 팬맺기 수
                    fan_url = f"https://www.melon.com/artist/getArtistFanNTemper.json?artistId={artist_id}"
                    async with session.get(fan_url, headers=headers) as fan_response:
                        if fan_response.status == 200:
                            fan_data = await fan_response.json()
                            artist['followers'] = fan_data.get('fanInfo', {}).get('SUMMCNT', 0)
                        else:
                            logger.error(f"Failed to fetch fan count data: HTTP {fan_response.status}")
                            artist['followers'] = 0

                    return artist

        except aiohttp.ClientError as e:
            attempt += 1
            logger.error(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                await asyncio.sleep(delay)
            else:
                raise Exception(f"Failed to fetch page after {max_retries} attempts: {e}")
