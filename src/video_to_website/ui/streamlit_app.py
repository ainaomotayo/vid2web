import streamlit as st
import asyncio
import sys
import os

# --- Event Loop Policy for Windows ---
# This must be at the very top of the file, before any other asyncio imports
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import logging
import threading
import queue
import time
import zipfile
import io
import base64
from pathlib import Path
from dotenv import load_dotenv
from google.adk.runners import InMemoryRunner
from google.genai import types
from google.genai.errors import ClientError
from google.adk.models.google_llm import _ResourceExhaustedError

# Import the app definition
# Add the project root/src to sys.path to ensure imports work
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent.parent / "src"
sys.path.append(str(project_root))

from video_to_website.agent import app

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Page Config ---
st.set_page_config(
    page_title="Gemini Video-to-Website",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session State Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "runner" not in st.session_state:
    st.session_state.runner = None
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "generated_html" not in st.session_state:
    st.session_state.generated_html = None
if "generated_css" not in st.session_state:
    st.session_state.generated_css = None
if "generated_js" not in st.session_state:
    st.session_state.generated_js = None
if "generation_complete" not in st.session_state:
    st.session_state.generation_complete = False
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "log_queue" not in st.session_state:
    st.session_state.log_queue = queue.Queue()
if "final_response" not in st.session_state:
    st.session_state.final_response = None
if "fullscreen_preview" not in st.session_state:
    st.session_state.fullscreen_preview = False

# --- Custom Logging Handler ---
class QueueHandler(logging.Handler):
    """Custom logging handler to send logs to a queue for Streamlit display."""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        try:
            msg = self.format(record)
            # We prefix with a different type to distinguish from agent events
            self.log_queue.put({"type": "system_log", "message": msg})
        except Exception:
            self.handleError(record)

# --- Background Runner Logic ---

def run_agent_in_background(runner, session_id, prompt, log_queue):
    """Runs the agent in a separate thread and pushes events to a queue."""
    
    # Setup logging capture
    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(logging.INFO)
    
    # Attach to the root logger of the project to capture tool logs
    project_logger = logging.getLogger("video_to_website")
    project_logger.addHandler(queue_handler)
    project_logger.setLevel(logging.INFO)
    
    async def _async_run():
        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt)],
        )
        
        try:
            async for event in runner.run_async(
                user_id="streamlit_user",
                session_id=session_id,
                new_message=message,
            ):
                # Check for tool call by inspecting the content directly
                is_tool_call = False
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            is_tool_call = True
                            tool_name = part.function_call.name
                            log_queue.put({"type": "log", "message": f"🤖 Agent calling tool: **{tool_name}**..."})
                            break 
                
                if event.is_final_response() and not is_tool_call:
                    text = ""
                    if event.content and event.content.parts:
                        text = event.content.parts[0].text or ""
                    log_queue.put({"type": "result", "content": text})
            
            # Signal completion
            log_queue.put({"type": "done"})
            
        except Exception as e:
            log_queue.put({"type": "error", "message": str(e)})
            logger.error(f"Agent error: {e}", exc_info=True)
        finally:
            # Cleanup handler
            project_logger.removeHandler(queue_handler)

    # Create a new event loop for this thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_async_run())
    loop.close()

async def get_latest_state():
    """Fetches the latest session state."""
    if st.session_state.runner and st.session_state.session_id:
        session = await st.session_state.runner.session_service.get_session(
            app_name="video_to_website_ui",
            user_id="streamlit_user",
            session_id=st.session_state.session_id
        )
        return session.state
    return {}

# --- UI Helper Functions ---
def create_zip_buffer(session_id):
    """Zips the contents of the session-specific output directory and returns a buffer."""
    zip_buffer = io.BytesIO()
    output_dir = Path(f"output/{session_id}/generated_website")
    
    if not output_dir.exists():
        return None

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for entry in output_dir.rglob('*'):
            zip_file.write(entry, entry.relative_to(output_dir))
            
    zip_buffer.seek(0)
    return zip_buffer

def get_image_as_base64(path: Path) -> str:
    """Reads an image file and returns it as a Base64 encoded string."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except Exception:
        return ""

def inject_base64_images(html_content: str, session_id: str) -> str:
    """Replaces local image paths with Base64 data URIs for preview."""
    if not html_content:
        return ""
        
    output_dir = Path(f"output/{session_id}/generated_website")
    
    # Find all image tags with local 'assets/' path
    import re
    img_pattern = re.compile(r'<img src="assets/([^"]+)"')
    
    def replacer(match):
        img_filename = match.group(1)
        img_path = output_dir / "assets" / img_filename
        if img_path.exists():
            base64_data = get_image_as_base64(img_path)
            if base64_data:
                # Simple check for image type based on extension
                ext = img_path.suffix.lower().replace(".", "")
                return f'<img src="data:image/{ext};base64,{base64_data}"'
        # If file not found or other error, return original tag
        return match.group(0)
        
    return img_pattern.sub(replacer, html_content)

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Configuration")
    
    api_key = st.text_input("Google API Key", type="password", value=os.environ.get("GOOGLE_API_KEY", ""))
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    
    st.divider()
    
    # Framework Selection
    target_framework = st.selectbox(
        "Target Framework",
        options=["html", "react", "vue"],
        index=0,
        help="Choose the output format for the generated code."
    )
    
    st.divider()
    
    if st.session_state.generation_complete and st.session_state.session_id:
        st.subheader("Download Source Code")
        zip_data = create_zip_buffer(st.session_state.session_id)
        if zip_data:
            st.download_button(
                label="Download as .zip",
                data=zip_data,
                file_name="generated_website.zip",
                mime="application/zip",
            )
        else:
            st.warning("No files found to download.")
    
    st.divider()
    st.info("This tool uses Gemini 3 Flash/Pro to analyze video and generate code.")

# --- Main Interface ---
st.title("🎥 Gemini Video-to-Website Generator")

# Input Section
video_url = st.text_input("Enter YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...", disabled=st.session_state.is_running)

# Start Generation Button
if st.button("Generate Website", type="primary", disabled=not video_url or st.session_state.is_running):
    if not api_key:
        st.error("Please provide a Google API Key in the sidebar.")
    else:
        st.session_state.is_running = True
        st.session_state.generation_complete = False
        st.session_state.final_response = None
        
        # Initialize Runner
        if st.session_state.runner is None:
            st.session_state.runner = InMemoryRunner(
                agent=app.root_agent,
                app_name="video_to_website_ui",
            )
            # Register plugins
            for plugin in app.plugins:
                st.session_state.runner.plugin_manager.register_plugin(plugin)

        # Create Session (Sync wrapper for async init)
        async def init_session():
            session = await st.session_state.runner.session_service.create_session(
                app_name="video_to_website_ui",
                user_id="streamlit_user",
                state={
                    "input_video_path": video_url,
                    "target_framework": target_framework, # Pass framework preference
                    # Initialize code keys to avoid KeyError in prompt templates
                    "generated_html": "",
                    "generated_css": "",
                    "generated_js": "",
                    "validation_results": {}
                },
            )
            return session.id

        st.session_state.session_id = asyncio.run(init_session())
        
        # Start Background Thread
        thread = threading.Thread(
            target=run_agent_in_background,
            args=(
                st.session_state.runner,
                st.session_state.session_id,
                f"Generate a {target_framework} website from the video at {video_url}.",
                st.session_state.log_queue
            )
        )
        thread.start()
        st.rerun()

# --- Status & Progress Area ---
if st.session_state.is_running:
    with st.status("🚀 Generating Website...", expanded=True) as status:
        st.write("Initializing agents...")
        
        # Process Queue Loop
        while True:
            try:
                # Non-blocking get
                event = st.session_state.log_queue.get_nowait()
                
                if event["type"] == "log":
                    # Agent-level logs (Tool calls)
                    st.write(event["message"])
                elif event["type"] == "system_log":
                    # System-level logs (Tool internals: downloading, uploading, etc.)
                    # We use a smaller font or different style for system logs
                    st.caption(f"⚙️ {event['message']}")
                elif event["type"] == "result":
                    st.session_state.final_response = event["content"]
                elif event["type"] == "error":
                    st.error(f"Error: {event['message']}")
                    st.session_state.is_running = False
                    status.update(label="❌ Generation Failed", state="error")
                    break
                elif event["type"] == "done":
                    st.session_state.is_running = False
                    st.session_state.generation_complete = True
                    status.update(label="✅ Generation Complete!", state="complete", expanded=False)
                    
                    # Fetch final state
                    state = asyncio.run(get_latest_state())
                    st.session_state.generated_html = state.get("generated_html")
                    st.session_state.generated_css = state.get("generated_css")
                    st.session_state.generated_js = state.get("generated_js")
                    
                    # Add initial message to chat history
                    if st.session_state.final_response:
                        st.session_state.messages.append({"role": "assistant", "content": st.session_state.final_response})
                    else:
                         st.session_state.messages.append({"role": "assistant", "content": "I've generated the website based on the video. You can see the preview below."})
                    
                    st.rerun()
                    break
                    
            except queue.Empty:
                # Wait a bit before checking again to prevent busy loop
                time.sleep(0.1)
                pass

# --- Two-Column Layout (Preview & Chat) ---
if st.session_state.generation_complete:
    
    # Fullscreen Toggle Button
    if st.button("↔️ Toggle Fullscreen Preview"):
        st.session_state.fullscreen_preview = not st.session_state.fullscreen_preview
        st.rerun()
        
    if st.session_state.fullscreen_preview:
        # Fullscreen View
        st.subheader("🌐 Live Preview (Fullscreen)")
        if st.session_state.generated_html:
            html_for_preview = inject_base64_images(st.session_state.generated_html, st.session_state.session_id)
            if st.session_state.generated_css:
                html_for_preview = html_for_preview.replace("</head>", f"<style>{st.session_state.generated_css}</style></head>")
            if st.session_state.generated_js:
                html_for_preview = html_for_preview.replace("</body>", f"<script>{st.session_state.generated_js}</script></body>")
            st.components.v1.html(html_for_preview, height=800, scrolling=True)
    else:
        # Two-Column View
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("🌐 Live Preview")
            if st.session_state.generated_html:
                # We need to inject CSS/JS into HTML for the iframe to render correctly
                html_for_preview = inject_base64_images(st.session_state.generated_html, st.session_state.session_id)
                if st.session_state.generated_css:
                    html_for_preview = html_for_preview.replace("</head>", f"<style>{st.session_state.generated_css}</style></head>")
                if st.session_state.generated_js:
                    html_for_preview = html_for_preview.replace("</body>", f"<script>{st.session_state.generated_js}</script></body>")
                
                st.components.v1.html(html_for_preview, height=600, scrolling=True)
            else:
                st.warning("No HTML generated yet.")
                
            with st.expander("View Source Code"):
                tab1, tab2, tab3 = st.tabs(["HTML", "CSS", "JS"])
                with tab1:
                    st.code(st.session_state.generated_html, language="html")
                with tab2:
                    st.code(st.session_state.get("generated_css", ""), language="css")
                with tab3:
                    st.code(st.session_state.get("generated_js", ""), language="javascript")

        with col2:
            st.subheader("💬 Refine with AI")
            
            # Display chat messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("E.g., 'Make the header background blue'"):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Start Refinement in Background
            st.session_state.is_running = True
            
            # Start Background Thread for Refinement
            thread = threading.Thread(
                target=run_agent_in_background,
                args=(
                    st.session_state.runner,
                    st.session_state.session_id,
                    prompt,
                    st.session_state.log_queue
                )
            )
            thread.start()
            st.rerun()

# --- Refinement Status Handling ---
# This block handles the UI updates when refinement is running
if st.session_state.is_running and st.session_state.generation_complete:
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        with st.status("🛠️ Refining...", expanded=True) as status:
            while True:
                try:
                    event = st.session_state.log_queue.get_nowait()
                    if event["type"] == "log":
                        st.write(event["message"])
                    elif event["type"] == "system_log":
                        st.caption(f"⚙️ {event['message']}")
                    elif event["type"] == "result":
                        st.session_state.final_response = event["content"]
                    elif event["type"] == "error":
                        st.error(f"Error: {event['message']}")
                        st.session_state.is_running = False
                        status.update(label="❌ Refinement Failed", state="error")
                        break
                    elif event["type"] == "done":
                        st.session_state.is_running = False
                        status.update(label="✅ Refinement Complete!", state="complete", expanded=False)
                        
                        if st.session_state.final_response:
                            st.session_state.messages.append({"role": "assistant", "content": st.session_state.final_response})
                        
                        # Refresh state
                        state = asyncio.run(get_latest_state())
                        st.session_state.generated_html = state.get("generated_html")
                        st.session_state.generated_css = state.get("generated_css")
                        st.session_state.generated_js = state.get("generated_js")
                        
                        st.rerun()
                        break
                except queue.Empty:
                    time.sleep(0.1)
