# src/services/movie_service.py
import os
import random
from typing import List, Optional
from fastapi import Request
from urllib.parse import quote  # 為了處理中文檔名安全轉換

from ..config import settings
from ..models import MovieRecommendation

# 全局變數：存放所有海報檔案和可用的（未推薦的）海報列表
_all_movie_posters: List[str] = [] # 存放檔案名稱，例如 'poster1.jpg'
_unrecommended_posters: List[str] = [] # 存放未推薦的檔案名稱

def _load_movie_posters():
    """
    掃描電影海報目錄，載入所有圖片檔案名稱。
    這個函數應該在應用程式啟動時呼叫一次。
    """
    global _all_movie_posters, _unrecommended_posters
    if _all_movie_posters: # 避免重複載入
        return

    try:
        if not os.path.exists(settings.MOVIE_POSTER_FILES_ROOT):
            print(f"警告：找不到電影海報資料夾 '{settings.MOVIE_POSTER_FILES_ROOT}'。")
            return

        formats = ('.png', '.jpg', '.jpeg', '.gif')
        # 篩選出符合圖片格式的檔案名稱
        _all_movie_posters = [
            f for f in os.listdir(settings.MOVIE_POSTER_FILES_ROOT)
            if f.lower().endswith(formats)
        ]
        _unrecommended_posters = _all_movie_posters[:] # 初始化為所有海報
        print(f"電影服務：已從 {settings.MOVIE_POSTER_FILES_ROOT} 載入 {len(_all_movie_posters)} 張電影海報。")

    except Exception as e:
        print(f"載入電影海報時發生錯誤: {e}")

# def get_random_movie_poster() -> Optional[MovieRecommendation]:
#     """
#     隨機推薦一張電影海報。
#     """
#     # 確保資料已載入
#     if not _all_movie_posters:
#         _load_movie_posters()
#         if not _all_movie_posters:
#             return MovieRecommendation(
#                 poster_url=None, movie_title=None, message="電影海報清單尚未初始化或為空。"
#             )
#
#     if not _unrecommended_posters:
#         # 如果所有海報都已推薦，重置列表
#         _unrecommended_posters[:] = _all_movie_posters # 使用切片更新列表內容
#         print("所有電影海報已推薦完畢，列表已重置。")
#         # 重置後，再次嘗試隨機推薦
#         # 注意：這裡會遞迴呼叫，但因列表已重置，不會造成無限循環
#         return get_random_movie_poster()
#
#     if _unrecommended_posters:
#         chosen_poster_filename = random.choice(_unrecommended_posters)
#         _unrecommended_posters.remove(chosen_poster_filename)
#
#         # 從檔案名稱解析電影標題
#         movie_title = os.path.splitext(chosen_poster_filename)[0]
#         # 簡單的格式化，將底線替換為空格（可根據實際需求優化）
#         movie_title = movie_title.replace('_', ' ').replace('-', ' ')
#
#         # 構建海報的 URL 路徑
#         # 例如：/static/movie/poster1.jpg
#         poster_url = f"{settings.STATIC_URL_PREFIX}/movie/{chosen_poster_filename}"
#
#         return MovieRecommendation(
#             poster_url=poster_url,
#             movie_title=movie_title,
#             message=f"為您推薦電影：{movie_title}"
#         )
#     return None # 理論上不應該到達這裡

def get_random_movie_poster(request: Request) -> Optional[MovieRecommendation]:
    if not _all_movie_posters:
        _load_movie_posters()
        if not _all_movie_posters:
            return MovieRecommendation(
                poster_url=None, movie_title=None, message="電影海報清單尚未初始化或為空。"
            )

    if not _unrecommended_posters:
        _unrecommended_posters[:] = _all_movie_posters
        return get_random_movie_poster(request)

    if _unrecommended_posters:
        chosen_poster_filename = random.choice(_unrecommended_posters)
        _unrecommended_posters.remove(chosen_poster_filename)

        movie_title = os.path.splitext(chosen_poster_filename)[0]
        movie_title = movie_title.replace('_', ' ').replace('-', ' ')

        # 使用 request 產生完整 URL
        encoded_filename = quote(chosen_poster_filename)
        # poster_url = request.url_for("statics", path=f"movie/{encoded_filename}")
        poster_url = str(request.url_for("statics", path=f"movie/{encoded_filename}"))

        return MovieRecommendation(
            poster_url=poster_url,
            movie_title=movie_title,
            message=f"為您推薦電影：{movie_title}"
        )

    return None