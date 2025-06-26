# src/services/music_service.py
import json
import os
import random
from fuzzywuzzy import process, fuzz
from typing import List, Optional

from ..config import settings
from ..models import MusicRecommendation, VideoData

# 全局變數：存放所有影片資料和可用的（未播放的）影片列表
_all_available_videos: List[VideoData] = []
_unplayed_videos: List[VideoData] = []


def _load_videos_data():
    """
    從 JSON 檔案載入影片資料，並初始化已播放狀態。
    這個函數應該在應用程式啟動時呼叫一次。
    """
    global _all_available_videos, _unplayed_videos
    if _all_available_videos:  # 避免重複載入
        return

    try:
        # 確保路徑正確，處理相對路徑問題
        json_path = os.path.join(os.path.dirname(__file__), '..', 'data',
                                 os.path.basename(settings.YT_VIDEOS_JSON_PATH))

        # 修正：直接使用 settings.YT_VIDEOS_JSON_PATH
        # 因為 settings.YT_VIDEOS_JSON_PATH 已經是完整的相對路徑 "src/data/yt_videos.json"
        # 這裡需要一個從專案根目錄開始的絕對路徑，或者確保運行時的工作目錄正確
        # 更穩健的做法是確保 settings.YT_VIDEOS_JSON_PATH 是從應用程式根目錄算起的絕對路徑
        # 在 main.py 中啟動時處理路徑會更好

        if not os.path.exists(settings.YT_VIDEOS_JSON_PATH):
            print(f"警告：找不到 '{settings.YT_VIDEOS_JSON_PATH}'。請檢查路徑。")
            return

        with open(settings.YT_VIDEOS_JSON_PATH, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            _all_available_videos = [VideoData(**item) for item in raw_data]
            _unplayed_videos = [video for video in _all_available_videos if not video.played]
            print(f"音樂服務：已從 {settings.YT_VIDEOS_JSON_PATH} 載入 {len(_all_available_videos)} 筆影片。")

    except FileNotFoundError:
        print(f"錯誤：'{settings.YT_VIDEOS_JSON_PATH}' 檔案未找到。")
    except json.JSONDecodeError:
        print(f"錯誤：'{settings.YT_VIDEOS_JSON_PATH}' 不是有效的 JSON 檔案。")
    except Exception as e:
        print(f"載入影片資料時發生錯誤: {e}")


def find_and_recommend_music_by_desc(weather_desc: str) -> Optional[MusicRecommendation]:
    """
    根據天氣描述推薦最匹配的音樂。
    """
    # 確保資料已載入
    if not _all_available_videos:
        _load_videos_data()
        if not _all_available_videos:  # 如果載入後仍然為空，則無法推薦
            return MusicRecommendation(
                url=None, description=None, message="音樂清單尚未初始化或為空。"
            )

    if not _unplayed_videos:
        # 如果所有影片都已播放，重置列表
        for video in _all_available_videos:
            video.played = False
        _unplayed_videos[:] = _all_available_videos  # 使用切片更新列表內容
        print("所有音樂已播放完畢，列表已重置。")
        # 重置後，再次嘗試推薦
        return find_and_recommend_music_by_desc(weather_desc)  # 遞迴呼叫一次，嘗試在重置後尋找

    best_match: Optional[VideoData] = None
    best_score = -1

    # 在未播放的影片中尋找最佳匹配
    for video in _unplayed_videos:
        # 使用 fuzzywuzzy 比較天氣描述和影片的 matched_weather_descriptions
        # 原本（錯誤）：
        # score = fuzz.partial_ratio(weather_desc.lower(), video.matched_weather_descriptions.lower())

        # 改成（正確）：
        best_score_for_video = max(
            fuzz.partial_ratio(weather_desc.lower(), desc.lower()) for desc in video.matched_weather_descriptions
        )
        if best_score_for_video > best_score:
            best_score = best_score_for_video
            best_match = video

    # 設置一個匹配度閾值，避免不相關的推薦
    if best_match and best_score >= 70:
        best_match.played = True  # 標記為已播放
        _unplayed_videos.remove(best_match)  # 從未播放列表中移除
        return MusicRecommendation(
            url=best_match.url,
            description=best_match.description,
            message=f"已為您推薦與「{weather_desc}」相關的音樂：{best_match.description}"
        )

    return None  # 沒有找到足夠匹配的影片


def get_random_music_recommendation() -> Optional[MusicRecommendation]:
    """
    隨機推薦一首未播放的音樂。
    """
    # 確保資料已載入
    if not _all_available_videos:
        _load_videos_data()
        if not _all_available_videos:
            return MusicRecommendation(
                url=None, description=None, message="音樂清單尚未初始化或為空。"
            )

    if not _unplayed_videos:
        # 如果所有影片都已播放，重置列表
        for video in _all_available_videos:
            video.played = False
        _unplayed_videos[:] = _all_available_videos
        print("所有音樂已播放完畢，列表已重置。")
        # 重置後，再次嘗試隨機推薦
        return get_random_music_recommendation()  # 遞迴呼叫一次

    if _unplayed_videos:
        chosen_video = random.choice(_unplayed_videos)
        chosen_video.played = True
        _unplayed_videos.remove(chosen_video)
        return MusicRecommendation(
            url=chosen_video.url,
            description=chosen_video.description,
            message=f"已為您隨機推薦了一首音樂：{chosen_video.description}"
        )
    return None  # 理論上不應該到達這裡，除非 _unplayed_videos 剛好為空