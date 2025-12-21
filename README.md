# Gemini Powered Video-to-Website Generator

This project is an autonomous website creation system that transforms video walkthroughs or verbal descriptions into fully-functional, responsive websites. It leverages the power of Google's Gemini 3 multimodal models and the Google Agent Development Kit (ADK) to analyze video, plan architecture, generate code, and iteratively refine the output.

> **Note:** This project was developed as part of the **Google AI Sprint H2, 2025**. We gratefully acknowledge Google for providing the Google Cloud credits that made this development possible.

## Core Capabilities

- **Video Analysis**: Uses Gemini's multimodal reasoning to extract design intent, layout patterns, color schemes, and visual hierarchy from video walkthroughs.
- **Content Extraction**: Identifies text content, information architecture, and navigation structure from verbal descriptions in the video.
- **Code Generation**: Produces production-ready HTML, CSS, and JavaScript implementations.
- **Automated Validation**: Employs agents for in-browser validation (using Playwright), accessibility checks, and responsive design verification.
- **Iterative Refinement**: Uses ADK's `LoopAgent` for continuous improvement based on validation feedback.

## Use Cases

This tool is designed to dramatically accelerate the "idea-to-code" and "content-to-web" workflows.

### 1. Automated Content Repurposing (For Creators)
- **Who:** YouTubers, course creators, and content marketers.
- **Problem:** Valuable information is "trapped" inside videos, making it hard to search, skim, or reference.
- **Solution:** Automatically convert a video tutorial or a playlist into a well-structured blog post or a navigable course website. The system transcribes the content, extracts key topics as sections, and generates a content-rich, SEO-friendly webpage.

### 2. High-Fidelity Prototyping (For Designers)
- **Who:** UI/UX Designers.
- **Problem:** Static mockups fail to convey the true feel of a website's animations and responsive behavior.
- **Solution:** A designer records a video walkthrough of their Figma or Sketch prototype. The tool generates a live, interactive HTML/CSS/JS prototype that behaves like a real website, perfect for client feedback and developer handoff.

### 3. Rapid Landing Page Generation (For Entrepreneurs)
- **Who:** Marketers, entrepreneurs, and startups.
- **Problem:** Need a web presence for a new product or campaign immediately, without waiting for developers.
- **Solution:** Sketch a layout on a whiteboard or verbally describe the desired structure while recording. The tool generates a v1 landing page in minutes, ready for idea validation and email sign-ups.

### 4. Developer Scaffolding & Boilerplate
- **Who:** Frontend and Full-Stack Developers.
- **Problem:** The initial project setup—structuring HTML, extracting design tokens (colors, fonts), and writing boilerplate CSS—is tedious.
- **Solution:** Run a video of the final design through the tool to instantly get a complete project scaffold with semantic HTML, a CSS file with variables, and basic layout styles already implemented.

## Tech Stack

- **AI & Orchestration**:
  - **Google Agent Development Kit (ADK)**: For agent orchestration (`SequentialAgent`, `ParallelAgent`, `LoopAgent`).
  - **Google Gemini 3 Flash/Pro**: Multimodal LLM for video understanding and code generation.
- **Development Environment**:
  - **Python 3.11+**
  - **uv**: For fast dependency management.
  - **pip**: For package installation.
- **Core Libraries**:
  - `google-genai`: The official Google Gemini SDK.
  - `playwright`: For browser automation and validation.
  - `yt-dlp`: For downloading YouTube videos for analysis.
  - `dirtyjson`: For robust parsing of LLM-generated JSON.
  - `python-dotenv`: For managing environment variables.

## Project Structure

```
video-to-website-generator/
├── src/
│   └── video_to_website/
│       ├── agent.py             # Root agent and App definition
│       ├── agents/              # Individual agent implementations
│       ├── tools/               # Custom tool functions
│       ├── prompts/             # LLM instruction templates
│       ├── schemas/             # Pydantic models for structured data
│       └── plugins/             # Custom ADK plugins (e.g., ModelFallback)
├── tests/
│   ├── unit/
│   └── integration/
├── examples/
│   └── basic_usage.py       # Runnable example to generate a website
├── output/                      # Generated website output (gitignored)
└── .gitignore                   # Files to ignore in version control
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd video-to-website-generator
```

### 2. Create a Virtual Environment

It is highly recommended to use a virtual environment.

```bash
# Create a virtual environment
python -m venv .venv

# Activate it
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

Install all required packages from `pyproject.toml`.

```bash
pip install -e .[dev]
```
*(Note: The `-e .` installs the project in editable mode, and `[dev]` installs the development dependencies like pytest).*

You will also need to install the browser binaries for Playwright:
```bash
playwright install
```

### 4. Set Up Your API Key

The application requires a Google Gemini API key.

1.  Create a file named `.env` in the root of the project.
2.  Add your API key to the file:

    ```
    GOOGLE_API_KEY="your-api-key-here"
    ```

## How to Run

### Generate a Website

To run the full pipeline and generate a website from the default YouTube video, execute the `basic_usage.py` script from the project root.

**On Windows (Command Prompt):**
```cmd
set PYTHONPATH=src && python examples/basic_usage.py
```

**On Windows (PowerShell):**
```powershell
$env:PYTHONPATH="src"; python examples/basic_usage.py
```

**On macOS/Linux:**
```bash
export PYTHONPATH=src && python examples/basic_usage.py
```

The script will:
1. Download the video.
2. Run the full agent pipeline (Analysis -> Architecture -> Code Gen -> Validation).
3. Save the generated `index.html`, `styles.css`, and `scripts.js` files to the `output/generated_website/` directory.

### Run Tests

To verify that all components are working correctly, run the test suite:

```bash
pytest
```

To run tests in parallel for faster execution:
```bash
pytest -n auto
```
