# src/services/__init__.py

# 匯入各個服務模組，方便在其他地方統一引用
from . import weather_service
from . import music_service
from . import movie_service

# 如果需要，也可以直接匯入常用的函數或類別
# 例如: from .weather_service import get_current_weather