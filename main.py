import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain.agents import initialize_agent
from fastapi.middleware.cors import CORSMiddleware


os.environ["GOOGLE_API_KEY"] = "AIzaSyC-sT4cHOva-ouANVnAEeqYra4uyQmafuI"
os.environ["WEATHER_API_KEY"] = "dbbd006c7c6e408083a55658250409"

# 2. Khởi tạo LLM Gemini
# =======================
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0,
    max_output_tokens=None,
    convert_system_message_to_human=True
)

# 3. Tạo tool WeatherAPI
# =======================
@tool
def get_weather(city: str) -> str:
    """Trả về thời tiết hiện tại của một thành phố bằng WeatherAPI."""
    WEATHER_API_KEY = os.environ.get("WEATHER_API_KEY")
    if not WEATHER_API_KEY:
        return "Thiếu WEATHER_API_KEY"
    
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}&aqi=no"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        location = data.get("location", {}).get("name", city)
        condition = data.get("current", {}).get("condition", {}).get("text", "Không rõ")
        temp_c = data.get("current", {}).get("temp_c", "N/A")
        humidity = data.get("current", {}).get("humidity", "N/A")
        last_updated = data.get("current", {}).get("last_updated", "N/A")
        
        return f"Thời tiết ở {location} lúc {last_updated}: {condition}, nhiệt độ {temp_c}°C, độ ẩm {humidity}%."
    
    except Exception as e:
        return f"Không lấy được dữ liệu thời tiết cho {city}. Lỗi: {e}"


# 4. Khởi tạo agent
# =======================
agent = initialize_agent(
    tools=[get_weather],
    llm=llm,
    agent="zero-shot-react-description",
    verbose=True
)



# 5. FastAPI setup
# =======================
app = FastAPI(title="Weather Chatbot API")

# Cho phép frontend gọi (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hoặc thay bằng URL frontend khi deploy
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model dữ liệu nhận từ frontend
class Query(BaseModel):
    question: str

@app.post("/get-weather")
def ask(query: Query):
    """Nhận câu hỏi từ frontend và trả về câu trả lời từ agent."""
    try:
        answer = agent.run(query.question)
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"Có lỗi xảy ra: {e}"}