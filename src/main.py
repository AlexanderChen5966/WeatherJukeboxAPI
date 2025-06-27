# src/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# 從專案內部模組導入必要的設定和服務
from .config import settings
from .api.routes import router as api_router
from .services import music_service, movie_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式啟動和關閉時的事件處理器。
    用於在應用程式啟動時載入資料。
    """
    print("應用程式啟動中：載入數據...")
    music_service._load_videos_data() # 載入音樂影片資料
    movie_service._load_movie_posters() # 載入電影海報資料
    print("數據載入完成。")
    yield
    print("應用程式關閉中：清理資源...")
    # 在這裡可以添加應用程式關閉時的清理邏輯，例如關閉資料庫連接等

app = FastAPI(
    title="天氣與娛樂推薦 API",
    description="提供天氣查詢、音樂推薦及電影海報推薦服務。",
    version="1.0.0",
    docs_url="/docs",       # Swagger UI 文檔路徑
    redoc_url="/redoc",     # ReDoc 文檔路徑
    lifespan=lifespan       # 掛載生命週期事件處理器
)

# 定義允許的來源
# 這裡將 'https://alexanderchen5966.github.io' 加入到允許的來源列表中
origins = [
    "http://localhost:5173",                 # 開發時前端 Vue 執行的網址
    "https://alexanderchen5966.github.io",   # GitHub Pages 部署後的網址
    # 如果你還有其他前端來源，也可以在這裡新增
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允許的來源列表
    allow_credentials=True, # 允許跨來源請求中包含憑證 (如 cookies, HTTP authentication, client-side SSL certificates)
    allow_methods=["*"],    # 允許所有 HTTP 方法 (GET, POST, PUT, DELETE 等)
    allow_headers=["*"],    # 允許所有 HTTP 請求頭
)

# 1. 掛載 API 路由
# 將 src/api/routes.py 中定義的所有路由添加到應用程式中
app.include_router(api_router, prefix="/api", tags=["API 服務"])

# 2. 掛載靜態檔案服務
# StaticFiles 的 directory 參數需要一個檔案系統路徑
# Path(__file__).parent.parent 是指從 main.py 所在的 src/ 目錄往上兩層，即專案根目錄
# Path(__file__).parent 是 src/ 目錄
# 我們需要指向 src/statics，因為裡面有 movie 和 music 子目錄
static_files_directory = Path(__file__).parent / "statics"

app.mount(
    settings.STATIC_URL_PREFIX,  # URL 前綴，例如 /static
    StaticFiles(directory=static_files_directory),
    name="statics" # 靜態檔案服務的名稱
)

# 根路徑（可選）：提供一個基本的歡迎訊息或API說明
@app.get("/", summary="API 歡迎頁面")
async def read_root():
    return {"message": "歡迎使用天氣與娛樂推薦API！請訪問 /docs 查看API文檔。"}
