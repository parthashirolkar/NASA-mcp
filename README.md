# NASA MCP Server

This project provides a Model Context Protocol (MCP) server for interacting with NASA APIs, including the Astronomy Picture of the Day (APOD) and Near Earth Object (NEO) feeds. It is designed for use with LM Studio and other MCP-compatible clients.

## Features

- **Get NASA Picture of the Day**: Fetches the daily astronomy image from NASA APOD, returning the image and its metadata.
- **Get Current Date (IST)**: Returns the current date in Indian Standard Time, useful for time-based queries.
- **Get Near Earth Objects (NEOs)**: Retrieves a list of NEOs detected by NASA between specified dates, including detailed features for each close-approach event.

## Requirements

- Python 3.12+
- Pillow (PIL)
- aiohttp
- python-dotenv
- pandas
- pytz
- MCP SDK (`mcp.server.fastmcp`, `mcp.types`)

## Setup

1. **Clone the repository**
2. **Install dependencies**:
   ```zsh
   pip install -r requirements.txt
   ```
   Or use `pyproject.toml` with Poetry or similar tools.
3. **Set up environment variables**:
   - Create a `.env` file in the project root.
   - Add your NASA API key:
     ```
     NASA_API_KEY=your_nasa_api_key_here
     ```

## Usage

Run the MCP server:
```zsh
python main.py
```

The server exposes tools for use via MCP clients. Example tools:
- `get_picture_of_the_day`: Returns the NASA APOD image.
- `get_time`: Returns the current date in IST.
- `get_neo_asteroids(start_date, end_date)`: Returns NEO data for the given date range.

## File Overview

- `main.py`: Main MCP server implementation and tool definitions.
- `helper_functions.py`: Utility functions for image encoding.
- `pyproject.toml`, `uv.lock`: Dependency management files.
- `README.md`: Project documentation.

## Notes

- Ensure your NASA API key is valid and has sufficient quota.
- The server is designed for use with LM Studio and other MCP-compatible clients.
- Error handling is implemented to return informative messages and fallback images when NASA APIs are unavailable.

## License

This project is provided for educational and research purposes. See LICENSE for details.