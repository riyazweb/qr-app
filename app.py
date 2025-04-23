from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
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

# In‑memory clipboard store
clipboard_data: dict[str, str] = {}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    base_url = str(request.base_url).rstrip("/")
    unique_id = str(uuid.uuid4())[:8]
    post_url = f"{base_url}/post/{unique_id}"

    # Generate QR code
    qr = qrcode.make(post_url)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    img_str = base64.b64encode(buf.getvalue()).decode("utf-8")

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>QR Clipboard</title>
      <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-50 min-h-screen flex items-center justify-center p-4">
      <div class="bg-white shadow-md rounded-md max-w-4xl w-full flex flex-col md:flex-row overflow-hidden">
        <!-- Left panel: Recent clipboard -->
        <section class="w-full md:w-1/2 border-b md:border-b-0 md:border-r border-gray-200 p-6 flex flex-col">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-lg font-semibold text-gray-700">📥 Recent</h2>
            <button id="clear-all"
                    class="text-red-500 hover:text-red-700 text-sm font-medium">
              Clear All
            </button>
          </div>
          <div id="recent-list" class="flex-1 space-y-2 overflow-auto"></div>
        </section>

        <!-- Right panel: QR + form -->
        <section class="w-full md:w-1/2 p-6 flex flex-col items-center">
          <h1 class="text-2xl font-semibold text-gray-800 mb-4">📋 QR Clipboard</h1>
          <div class="flex flex-col items-center space-y-3">
            <img src="data:image/png;base64,{img_str}" 
                 alt="QR code" class="w-32 h-32"/>
            <code class="text-xs text-gray-500 truncate max-w-full">{post_url}</code>
          </div>
          <form id="send-form"
                action="/post/{unique_id}"
                method="post"
                class="mt-6 w-full flex space-x-2">
            <input type="text" name="text" placeholder="Type here…"
                   class="flex-1 bg-gray-100 border border-gray-200 text-gray-700 text-sm rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-400"/>
            <button type="submit"
                    class="bg-green-500 text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-green-600 focus:outline-none focus:ring-2 focus:ring-green-400">
              Send
            </button>
          </form>
        </section>
      </div>

      <script>
        // Fetch and render recent clipboard
        async function fetchRecent() {{
          const resp = await fetch('/data');
          const data = await resp.json();
          const container = document.getElementById('recent-list');
          container.innerHTML = '';
          const entries = Object.entries(data).reverse();
          if (!entries.length) {{
            container.innerHTML = '<p class="text-gray-400">No data yet.</p>';
            return;
          }}
          for (const [id, text] of entries) {{
            const row = document.createElement('div');
            row.className = "flex items-center justify-between py-2 border-b border-gray-200";
            row.innerHTML = `
              <div class="truncate">
                <p class="font-mono text-xs text-gray-400 truncate">${{id}}</p>
                <p class="text-gray-800 text-sm truncate">${{text}}</p>
              </div>
              <div class="flex space-x-2">
                <button data-copy="${{text}}" class="text-indigo-600 hover:text-indigo-800 text-sm font-medium">
                  Copy
                </button>
                <button data-delete="${{id}}" class="text-red-500 hover:text-red-700 text-sm font-medium">
                  Delete
                </button>
              </div>
            `;
            container.appendChild(row);
          }}
          // Attach button handlers
          container.querySelectorAll('button[data-copy]').forEach(btn => {{
            btn.onclick = () => {{
              navigator.clipboard.writeText(btn.dataset.copy);
            }};
          }});
          container.querySelectorAll('button[data-delete]').forEach(btn => {{
            btn.onclick = async () => {{
              await fetch(`/post/${{btn.dataset.delete}}`, {{ method: 'DELETE' }});
              fetchRecent();
            }};
          }});
        }}

        // Submit without full page reload
        document.getElementById('send-form').addEventListener('submit', async e => {{
          e.preventDefault();
          const form = e.target;
          const formData = new FormData(form);
          await fetch(form.action, {{
            method: 'POST',
            body: formData
          }});
          form.reset();
          fetchRecent();
        }});

        // Clear all
        document.getElementById('clear-all').addEventListener('click', async () => {{
          await fetch('/clear', {{ method: 'DELETE' }});
          fetchRecent();
        }});

        // Initial load and polling every 5s
        fetchRecent();
        setInterval(fetchRecent, 5000);
      </script>
    </body>
    </html>
    """
    return HTMLResponse(html)

@app.get("/data")
async def get_data():
    return JSONResponse(clipboard_data)

@app.post("/post/{clip_id}")
async def post_clip(clip_id: str, text: str = Form(...)):
    clipboard_data[clip_id] = text
    return JSONResponse({"status": "ok"})

@app.delete("/post/{clip_id}")
async def delete_clip(clip_id: str):
    if clip_id in clipboard_data:
        del clipboard_data[clip_id]
        return JSONResponse({"status": "deleted"})
    raise HTTPException(status_code=404, detail="Not found")

@app.delete("/clear")
async def clear_all():
    clipboard_data.clear()
    return JSONResponse({"status": "cleared"})

if __name__ == "__main__":
    def run():
        uvicorn.run(app, host="127.0.0.1", port=8000)
    threading.Thread(target=run).start()
    webbrowser.open("http://127.0.0.1:8000")
