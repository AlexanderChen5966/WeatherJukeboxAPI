# src/api/routes.py
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from fastapi import Request

# 從 services 模組導入業務邏輯函數
from src.services import weather_service
from src.services import music_service
from src.services import movie_service

# 從 models 模組導入資料模型
from ..models import WeatherResponse, MusicRecommendation, MovieRecommendation

# 建立一個 APIRouter 實例
# 所有的 API 端點都將透過這個 router 註冊
router = APIRouter()

@router.get(
    "/weather",
    response_model=WeatherResponse,
    summary="根據縣市名稱查詢即時天氣資訊",
    description="根據使用者提供的縣市名稱，查詢中央氣象署的即時天氣數據並返回詳細資訊。"
)
async def get_weather(
    city: str = Query(..., description="要查詢天氣的縣市名稱，例如：台北市")
):
    """
    查詢指定縣市的即時天氣預報。
    """
    weather_data = await weather_service.get_current_weather(city)
    if not weather_data:
        raise HTTPException(
            status_code=404, detail=f"無法取得 {city} 的天氣資料，請確認縣市名稱或稍後再試。"
        )
    return weather_data

@router.get(
    "/recommend_music",
    response_model=MusicRecommendation,
    summary="根據天氣描述推薦相關的 YouTube 音樂影片",
    description="根據提供的天氣關鍵字（例如：晴天、下雨），推薦一首相關的 YouTube 影片。已播放過的影片會被標記，直到所有影片都播放完畢後才會重置。"
)
async def recommend_music(
    desc: str = Query(..., description="天氣描述關鍵字，例如：晴天、下雨")
):
    """
    根據天氣描述推薦 YouTube 音樂影片。
    """
    recommended_video = music_service.find_and_recommend_music_by_desc(desc)
    if not recommended_video:
        # 雖然沒有找到精確匹配，但為了給使用者反饋，我們仍返回 200 OK
        # 讓前端根據 url 是否為 None 來判斷
        return MusicRecommendation(
            url=None,
            description=None,
            message=f"找不到與「{desc}」相關的未播放音樂，或所有音樂已播放完畢。"
        )
    return recommended_video

@router.get(
    "/random_music",
    response_model=MusicRecommendation,
    summary="隨機推薦一首未播放過的 YouTube 音樂影片",
    description="從可用的音樂列表中隨機選取一首未播放過的 YouTube 影片進行推薦。當所有影片都播放完畢後，列表會自動重置。"
)
async def get_random_music():
    """
    隨機推薦一首 YouTube 音樂影片。
    """
    random_video = music_service.get_random_music_recommendation()
    if not random_video:
        return MusicRecommendation(
            url=None,
            description=None,
            message="所有音樂都已播放完畢！列表已重置。"
        )
    return random_video

# @router.get(
#     "/random_movie",
#     response_model=MovieRecommendation,
#     summary="隨機推薦一部電影海報",
#     description="隨機推薦一部電影海報的圖片路徑和標題。當所有海報都推薦完畢後，列表會自動重置。"
# )
# async def get_random_movie():
#     """
#     隨機推薦一張電影海報。
#     """
#     random_poster = movie_service.get_random_movie_poster()
#     if not random_poster:
#         # 這應該在 movie_service.py 中處理重置邏輯並返回相應訊息
#         return MovieRecommendation(
#             poster_url=None,
#             movie_title=None,
#             message="所有電影都已推薦完畢！列表已重置。"
#         )
#     return random_poster

@router.get(
    "/random_movie",
    response_model=MovieRecommendation,
    summary="隨機推薦一部電影海報",
    description="隨機推薦一部電影海報的圖片路徑和標題。當所有海報都推薦完畢後，列表會自動重置。"
)
async def get_random_movie(request: Request):  # ✅ 新增參數 request
    """
    隨機推薦一張電影海報。
    """
    random_poster = movie_service.get_random_movie_poster(request)  # ✅ 傳入 request
    if not random_poster:
        return MovieRecommendation(
            poster_url=None,
            movie_title=None,
            message="所有電影都已推薦完畢！列表已重置。"
        )
    return random_poster