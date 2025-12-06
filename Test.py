import google.generativeai as genai
from io import BytesIO
from PIL import Image

# 配置你的 API Key
genai.configure(api_key="你的API_KEY")   # 或者提前 export GOOGLE_API_KEY=xxx

model = genai.GenerativeModel("gemini-1.5-flash")

print("正在生成纳米香蕉米其林大餐，请稍等 5-12 秒...")

response = model.generate_content(
    "Create a picture of a nano banana dish in a fancy restaurant with a Gemini theme, "
    "ultra detailed, molecular gastronomy style, cinematic lighting, 8k resolution",
    generation_config={
        "response_mime_type": "image/png"
    }
)

# 2025 年最新写法：直接从 response 里抠出 bytes
image_bytes = response.images[0]._blob.data    # 关键点在这行

# 把 bytes 转成 PIL Image 再保存
img = Image.open(BytesIO(image_bytes))
img.save("nano_banana_gemini_dish.png")

print("生成成功！已保存为：nano_banana_gemini_dish.png")
img.show()   # 直接弹窗打开看图（macOS/Windows/Linux 都行）