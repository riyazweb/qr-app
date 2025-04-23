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

    # Generate QR code
    qr = qrcode.make(post_url)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    # Build recent items (latest on top)
    items_html = ""
    for cid, val in reversed(list(clipboard_data.items())):
        items_html += f"""
        <div class="flex items-center justify-between py-3 border-b border-gray-200">
          <div class="flex-1 min-w-0">
            <p class="font-mono text-xs text-gray-500 truncate">{cid}</p>
            <p class="text-gray-800 truncate">{val}</p>
          </div>
          <button data-text="{val}"
                  class="ml-4 text-indigo-600 hover:text-indigo-800 text-sm font-medium focus:outline-none">
            Copy
          </button>
        </div>
        """
    if not items_html:
        items_html = '<p class="text-gray-400 py-4">No data yet.</p>'

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta http-equiv="refresh" content="16">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>QR Clipboard</title>
      <script src="https://cdn.tailwindcss.com?plugins=forms"></script>
    </head>
    <body class="bg-gray-50 min-h-screen flex items-center justify-center p-6">
      <div class="bg-white shadow-md rounded-md w-full max-w-sm">
        <header class="px-6 py-4 border-b border-gray-200">
          <h1 class="text-2xl font-semibold text-gray-800 text-center">📋 QR Clipboard</h1>
        </header>
        <main class="p-6 space-y-6">
          <div class="space-y-2 text-center">
            <p class="text-gray-500 text-sm">Scan to post text to:</p>
            <img src="data:image/png;base64,{img_str}" alt="QR Code" class="mx-auto w-28 h-28"/>
            <code class="block text-xs text-gray-400 truncate">{post_url}</code>
          </div>
          <form action="/post/{unique_id}" method="post" class="flex space-x-2">
            <input 
              type="text" 
              name="text" 
              placeholder="Type here…" 
              class="flex-1 bg-gray-100 border border-gray-200 text-gray-700 text-sm rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"/>
            <button 
              type="submit"
              class="bg-green-500 text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
              Send
            </button>
          </form>
          <section>
            <h2 class="text-lg font-medium text-gray-700 mb-2">📥 Recent</h2>
            <div class="divide-y divide-gray-200">
              {items_html}
            </div>
          </section>
        </main>
      </div>
      <script>
        document.querySelectorAll('button[data-text]').forEach(btn => {{
          btn.addEventListener('click', () => {{
            navigator.clipboard.writeText(btn.dataset.text);
            const orig = btn.innerText;
            btn.innerText = 'Copied';
            setTimeout(() => btn.innerText = orig, 1500);
          }});
        }});
      </script>
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
