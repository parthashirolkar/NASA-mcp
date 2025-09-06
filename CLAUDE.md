# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server that provides access to NASA APIs. It's designed to work with LM Studio and other MCP-compatible clients, offering ten comprehensive tools:

## Core Tools
- `get_picture_of_the_day(nasa_api_key)`: Fetches NASA's Astronomy Picture of the Day with metadata
- `get_time`: Returns current date in IST timezone (useful for time-based queries)  
- `get_neo_asteroids(nasa_api_key, start_date, end_date)`: Retrieves Near Earth Object data between specified dates

## Mars Rover Tools
- `get_mars_rover_photos(nasa_api_key, rover, sol, earth_date, camera, page, return_images)`: Get photos from Mars rovers with optional image rendering
- `get_latest_mars_photos(nasa_api_key, rover, return_images)`: Get the latest photos from a specific rover with optional image rendering
- `get_rover_mission_info(nasa_api_key, rover)`: Get mission data including available cameras and sol ranges

## Earth Imagery Tools  
- `get_earth_imagery(nasa_api_key, date, image_type, return_images)`: Get full-disc Earth images from EPIC/DSCOVR satellite with optional image rendering
- `get_available_earth_dates(nasa_api_key, image_type)`: List available dates for Earth imagery

## Natural Events Tools
- `get_natural_events(nasa_api_key, category, status, days)`: Track wildfires, storms, volcanoes, and other natural events via EONET (returns 1 event per call)
- `get_event_categories(nasa_api_key)`: Get available natural event categories

## Development Commands

**Run the server:**
```bash
python main.py
```
*Note: Server runs on SSE transport at port 8000 for remote hosting*

**Install dependencies:**
```bash
pip install -e .
```

**Code formatting/linting:**
```bash
ruff format .
ruff check .
```

## Architecture

The codebase follows a simple FastMCP server pattern:

- `main.py`: Core MCP server implementation with ten async tool functions
- `helper_functions.py`: Image encoding utilities for PIL to ImageContent conversion
- Environment configuration via `.env` file for NASA API key

## Key Implementation Details

- All NASA API calls use aiohttp with 30-second timeouts
- Error handling returns fallback responses (error images for APOD, error dicts for other APIs)
- NEO data is processed into structured records using pandas for data cleaning
- Mars rover photos include comprehensive metadata (rover info, cameras, coordinates)
- Earth imagery from EPIC includes full orbital position data and image URLs
- Natural events tracking via EONET includes coordinates and event categorization
- Time operations use IST timezone (Asia/Kolkata) via pytz
- **Image Rendering**: Tools with `return_images=True` download and render actual images using `_encode_image`
- Images are encoded as PNG format via PIL and converted to MCP ImageContent for client display

## API Endpoint Coverage

- **APOD API**: Daily astronomy images and explanations
- **NEO API**: Near-Earth asteroid tracking and orbital data  
- **Mars Rover Photos API**: Multi-rover image archives with camera filtering
- **EPIC API**: Full-disc Earth imagery from L1 Lagrange point
- **EONET API**: Real-time natural disaster and event tracking

## API Key Usage

**For Remote Hosting**: Users must provide their own NASA API key as a parameter to most tools. Note that EONET tools don't require an API key but accept the parameter for consistency.

**For Local Development**: You can still use a `.env` file, but the tools now require the API key as a parameter rather than reading from environment variables.
- Use `uv` to run everything related to python