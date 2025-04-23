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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

clipboard_data = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    base_url = str(request.base_url)
    unique_id = str(uuid.uuid4())[:8]
    post_url = f"{base_url}post/{unique_id}"

    qr = qrcode.make(post_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # 🧠 Show all data
    display_data = ""
    for cid, val in clipboard_data.items():
        display_data += f"<p><b>{cid}</b>: {val}</p>"

    html_content = f"""
    <html>
    <head>
        <title>📋 QR Clipboard</title>
        <meta http-equiv="refresh" content="16">
        <style>
            body {{ font-family: Arial; text-align: center; background: #f2f2f2; }}
            .container {{ background: white; padding: 2em; border-radius: 1em; margin: auto; width: 50%; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            input[type='text'] {{ width: 80%; padding: 0.5em; }}
            button {{ padding: 0.5em 1em; margin-top: 1em; }}
            .box {{ text-align: left; margin-top: 2em; background: #e8f4f8; padding: 1em; border-radius: 1em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📋 QR Clipboard</h1>
            <p>Scan to post text to:</p>
            <img src="data:image/png;base64,{img_str}" alt="QR Code" /><br>
            <code>{post_url}</code>
            <form method="post" action="/post/{unique_id}">
                <input type="text" name="text" placeholder="Type here..." />
                <br>
                <button type="submit">Send</button>
            </form>
            <div class="box">
                <h3>📥 Received Clipboard:</h3>
                {display_data if display_data else "<p>No data yet.</p>"}
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/post/{clip_id}", response_class=HTMLResponse)
async def post_clip(clip_id: str, text: str = Form(...)):
    clipboard_data[clip_id] = text
    return HTMLResponse("<script>window.location.href='/'</script>")

if __name__ == "__main__":
    def run():
        uvicorn.run(app, host="127.0.0.1", port=8000)
    threading.Thread(target=run).start()
    webbrowser.open("http://127.0.0.1:8000")
