# src/services/weather_service.py
import requests
from datetime import datetime
from fuzzywuzzy import process, fuzz
from typing import Optional, Dict, Any, List

from ..config import settings
from ..models import WeatherResponse

# 全局變數用於快取縣市列表和天氣資料，避免重複呼叫 API
# 注意：在生產環境中，更建議使用真正的快取機制（如 Redis）
_location_names: List[str] = []
_weather_data_cache: Dict[str, Any] = {} # 簡單的記憶體快取

async def _get_all_location_names() -> List[str]:
    """
    從 CWA API 獲取所有縣市名稱，並進行快取。
    """
    global _location_names
    if _location_names:
        return _location_names

    url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={settings.CWA_API_KEY}'
    try:
        response = await _fetch_data_from_cwa(url)
        if 'records' in response and 'location' in response['records']:
            _location_names = [loc['locationName'] for loc in response['records']['location']]
            return _location_names
    except Exception as e:
        print(f"錯誤：無法獲取縣市列表，請檢查網路或 API 金鑰：{e}")
    # 如果 API 獲取失敗，使用預設列表
    _location_names = [
        "臺北市", "新北市", "桃園市", "臺中市", "臺南市", "高雄市", "基隆市", "新竹市", "嘉義市",
        "新竹縣", "苗栗縣", "彰化縣", "南投縣", "雲林縣", "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
        "臺東縣", "澎湖縣", "金門縣", "連江縣"
    ]
    return _location_names

async def _fetch_data_from_cwa(url: str) -> Dict[str, Any]:
    """
    執行 CWA API 請求的通用非同步函數。
    """
    # 這裡使用 requests 庫，它本身是同步的。
    # 在 FastAPI 中，如果需要執行耗時的同步操作，建議使用 run_in_threadpool
    # 或改用 httpx 這樣的非同步 HTTP 客戶端。
    # 為了簡化，這裡暫時直接使用 requests。在實際生產中，請替換為非同步方案。
    import httpx # 推薦使用 httpx for async requests
    async with httpx.AsyncClient() as client:
        res = await client.get(url, timeout=10)
        res.raise_for_status() # 對於非 2xx 的狀態碼拋出異常
        return res.json()

def _auto_correct_city(input_city: str, available_locations: List[str]) -> Optional[str]:
    """
    自動校正縣市名稱。
    先檢查手動校正字典，再進行模糊比對。
    """
    corrected = settings.MANUAL_CORRECTIONS.get(input_city, input_city)
    if corrected in available_locations:
        return corrected
    if available_locations:
        match, score, _ = process.extractOne(corrected, available_locations, scorer=fuzz.ratio)
        if score >= 75:  # 設定一個匹配度閾值
            return match
    return None

def _classify_weather_type(weather_desc: str) -> str:
    """
    根據天氣描述歸類為 '晴', '雨', '陰', '多雲', '雪'。
    """
    for keyword, anim_type in settings.WEATHER_KEYWORDS_MAP.items():
        if keyword in weather_desc: # 簡單的包含判斷，可根據需求優化為模糊比對
            return anim_type
    if "晴" in weather_desc: return "晴"
    if "雨" in weather_desc: return "雨"
    if "陰" in weather_desc: return "陰"
    if "多雲" in weather_desc: return "多雲"
    if "雪" in weather_desc: return "雪"
    return "晴" # 預設為晴天

async def get_current_weather(city_input: str) -> Optional[WeatherResponse]:
    """
    獲取指定縣市的當前天氣資訊。
    """
    if any(char.isdigit() for char in city_input):
        return WeatherResponse(
            city_name=city_input, # 這裡保留原始輸入，但在 message 中提示錯誤
            weather_description="無效輸入",
            display_text="縣市名稱不能包含數字！",
            current_weather_type="晴"
        )

    available_locations = await _get_all_location_names()
    corrected_city = _auto_correct_city(city_input, available_locations)

    if not corrected_city:
        return WeatherResponse(
            city_name=city_input,
            weather_description="無效輸入",
            display_text=f"無效或無法識別的縣市: {city_input}",
            current_weather_type="晴"
        )

    # 檢查快取
    if corrected_city in _weather_data_cache:
        cached_data = _weather_data_cache[corrected_city]
        # 簡單的快取過期判斷，這裡假設每 10 分鐘更新一次
        if (datetime.now() - cached_data['timestamp']).total_seconds() < 600:
            return cached_data['response']

    url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={settings.CWA_API_KEY}&locationName={corrected_city}'
    try:
        data = await _fetch_data_from_cwa(url)
        if 'records' in data and 'location' in data['records'] and data['records']['location']:
            # 找到最近時間的預報資料
            time_elements = data['records']['location'][0]['weatherElement'][0]['time']
            forecast = min(time_elements,
                           key=lambda x: abs(datetime.strptime(x['startTime'], '%Y-%m-%d %H:%M:%S') - datetime.now()))
            desc = forecast['parameter']['parameterName']
            start_dt = datetime.strptime(forecast['startTime'], '%Y-%m-%d %H:%M:%S')
            hour = start_dt.hour
            time_desc = "午夜到早晨" if 0 <= hour < 6 else "早晨到中午" if 6 <= hour < 12 else "中午到傍晚" if 12 <= hour < 18 else "傍晚到午夜"

            # 取得降雨機率 (PoP)
            pop_data = next((elem for elem in data['records']['location'][0]['weatherElement'] if elem['elementName'] == 'PoP'), None)
            pop = "N/A"
            if pop_data:
                for pop_time in pop_data['time']:
                    if pop_time['startTime'] == forecast['startTime'] and pop_time['endTime'] == forecast['endTime']:
                        pop = pop_time['parameter']['parameterName'] + "%"
                        break

            display_text = f"{corrected_city} {start_dt.month}/{start_dt.day} {time_desc}是：{desc}，降雨機率{pop}喔！"
            weather_type = _classify_weather_type(desc)

            response = WeatherResponse(
                city_name=corrected_city,
                weather_description=desc,
                display_text=display_text,
                current_weather_type=weather_type
            )
            # 更新快取
            _weather_data_cache[corrected_city] = {'response': response, 'timestamp': datetime.now()}
            return response
        return WeatherResponse(
            city_name=corrected_city,
            weather_description="N/A",
            display_text="無法取得天氣資料：資料結構異常或無有效預報",
            current_weather_type="晴"
        )
    except requests.exceptions.RequestException as e:
        print(f"CWA API 請求錯誤: {e}")
        return WeatherResponse(
            city_name=corrected_city,
            weather_description="N/A",
            display_text=f"無法取得天氣資料：網路或API錯誤 ({e})",
            current_weather_type="晴"
        )
    except Exception as e:
        print(f"處理天氣資料時發生錯誤: {e}")
        return WeatherResponse(
            city_name=corrected_city,
            weather_description="N/A",
            display_text=f"處理天氣資料時發生錯誤: {e}",
            current_weather_type="晴"
        )