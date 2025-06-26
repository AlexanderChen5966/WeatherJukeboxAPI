# src/models.py
from pydantic import BaseModel, Field
from typing import Optional, List

# --- 天氣查詢相關模型 ---
class WeatherResponse(BaseModel):
    """
    天氣查詢 API 的響應模型。
    """
    city_name: str = Field(..., description="經過自動校正後的標準縣市名稱")
    weather_description: str = Field(..., description="原始的天氣描述，例如 '晴時多雲偶陣雨'")
    display_text: str = Field(..., description="供前端顯示的完整天氣資訊文字")
    current_weather_type: str = Field(..., description="將原始天氣描述歸類為 '晴', '雨', '陰', '多雲', '雪' 中的一種，供前端選擇對應動畫")

# --- 音樂推薦相關模型 ---
class MusicRecommendation(BaseModel):
    """
    音樂推薦 API 的響應模型。
    """
    url: Optional[str] = Field(None, description="推薦的 YouTube 影片網址，如果沒有找到則為 None")
    description: Optional[str] = Field(None, description="影片的描述或標題")
    message: str = Field(..., description="給前端顯示的推薦訊息")

# --- 電影推薦相關模型 ---
class MovieRecommendation(BaseModel):
    """
    電影推薦 API 的響應模型。
    """
    poster_url: Optional[str] = Field(None, description="電影海報的 URL 路徑，如果沒有找到則為 None")
    movie_title: Optional[str] = Field(None, description="電影的標題")
    message: str = Field(..., description="給前端顯示的推薦訊息")

# --- 內部使用的資料模型 (不需要對外暴露在 API 中) ---
class VideoData(BaseModel):
    """
    yt_videos.json 中單一影片的資料結構。
    """
    url: str
    description: str
    matched_weather_descriptions: List[str] # 逗號分隔的關鍵字
    played: bool = False # 新增的狀態追蹤，預設為 False