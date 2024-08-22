import httpx
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fetch_page(session, artist_id, album_id, page_no, chnl_seq='102', page_size=10):
    base_url = "https://cmt.melon.com/cmt/api/api_listCmt.json"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Referer': f'https://www.melon.com/album/detail.htm?albumId={album_id}'
    }

    params = {
        '_method': 'GET',
        'cmtPocType': 'pc.web',
        'pocId': 'MP10',
        'chnlSeq': chnl_seq,
        'contsRefValue': album_id,
        'totalCnt': -1,
        'validCnt': -1,
        'startSeq': -1,
        'pageSize': page_size,
        'pageNo': page_no,
        'sortType': '0',
        'srchType': '2',
        'srchWord': ''
    }

    try:
        response = await session.get(base_url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        json_data = response.json()
        comments = json_data.get('result', {}).get('cmtList', [])

        page_comments = []

        for comment in comments:
            cmt_info = comment.get('cmtInfo', {})
            member_info = comment.get('memberInfo', {})

            comment_data = {
                'id': cmt_info.get('cmtSeq'),
                'artist_id': artist_id,
                'album_id': album_id,
                'user_id': member_info.get('memberKey'),
                'username': member_info.get('memberNickname'),
                'content': cmt_info.get('cmtCont'),
                'display_date': cmt_info.get('dsplyDate'),
                'display_time': cmt_info.get('dsplyTime'),
                'recommendations': cmt_info.get('recmCnt'),
                'non_recommendations': cmt_info.get('nonRecmCnt'),
            }
            page_comments.append(comment_data)

        return page_comments

    except httpx.RequestError as e:
        logger.warning(f"Request failed on page {page_no} for album {album_id}: {e}")
        return []

async def retrieve_comments(artist_id, album_id, chnl_seq='102', page_size=10, max_pages=10):
    async with httpx.AsyncClient() as session:
        all_comments = []
        tasks = [
            fetch_page(session, artist_id, album_id, page_no, chnl_seq, page_size)
            for page_no in range(1, max_pages + 1)
        ]

        for responses in await asyncio.gather(*tasks):
            if responses:
                all_comments.extend(responses)

    return all_comments

async def get_comments(artist_id, album_id):
    comments = await retrieve_comments(artist_id, album_id)
    logger.info(f"Processed {len(comments)} comments for album {album_id}")
    return comments