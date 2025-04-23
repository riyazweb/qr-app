from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import qrcode
import io
import base64
import threading
import webbrowser
import uvicorn

app = FastAPI()

# 🔓 CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clipboard_data = {}  # 🧠 Dictionary to store clipboard text by ID

# 🏠 Home Page - QR Code Generator
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    unique_id = str(uuid.uuid4())[:8]
    request_url = str(request.base_url)  # 🌐 Dynamic URL
    url = f"{request_url}get/{unique_id}"

    # 📸 Generate QR code
    qr = qrcode.make(url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    html_content = f"""
    <html>
    <head>
        <title>QR Clipboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 2em; background: #f2f2f2; }}
            .container {{ background: white; padding: 2em; border-radius: 1em; display: inline-block; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            input[type='text'] {{ width: 300px; padding: 0.5em; font-size: 1em; }}
            button {{ padding: 0.5em 1em; font-size: 1em; margin-top: 1em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 QR Clipboard</h1>
            <p>Scan this QR code to send clipboard text to:</p>
            <img src="data:image/png;base64,{img_str}" alt="QR Code" /><br>
            <code>{url}</code>
            <p>Or paste content <b>here</b> to save:</p>
            <form method="post" action="/post/{unique_id}">
                <input type="text" name="text" placeholder="Enter text here" />
                <br>
                <button type="submit">Save</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# 📨 Save clipboard text
@app.post("/post/{clip_id}", response_class=HTMLResponse)
async def post_clip(clip_id: str, text: str = Form(...)):
    clipboard_data[clip_id] = text
    return HTMLResponse(f"<script>alert('✅ Saved!'); window.location.href = '/get/{clip_id}';</script>")

# 🔍 Get clipboard text
@app.get("/get/{clip_id}", response_class=HTMLResponse)
async def get_clip(clip_id: str):
    text = clipboard_data.get(clip_id, "❌ No data found for this code.")
    html_content = f"""
    <html>
    <head>
        <title>Clipboard Data</title>
        <script>
            function copyText() {{
                navigator.clipboard.writeText("{text}").then(() => alert("📋 Copied to clipboard!"));
            }}
        </script>
        <style>
            body {{ font-family: Arial; text-align: center; padding-top: 2em; background: #e8f4f8; }}
            .box {{ background: white; padding: 2em; border-radius: 1em; display: inline-block; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            button {{ margin-top: 1em; padding: 0.5em 1em; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h2>📋 Clipboard Content</h2>
            <p><b>{text}</b></p>
            <button onclick="copyText()">Copy to Clipboard</button>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# 🚀 Run the server and open browser
if __name__ == "__main__":
    def run():
        uvicorn.run(app, host="127.0.0.1", port=8000)

    threading.Thread(target=run).start()
    webbrowser.open("http://127.0.0.1:8000")
