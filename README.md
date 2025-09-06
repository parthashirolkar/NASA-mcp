# NASA MCP Server

A comprehensive Model Context Protocol (MCP) server providing access to multiple NASA APIs with 10 powerful tools for space data, imagery, and natural events tracking.

## 🚀 Features

### Core Tools
- **get_picture_of_the_day**: NASA's Astronomy Picture of the Day with metadata
- **get_time**: Current date in IST timezone for time-based queries
- **get_neo_asteroids**: Near Earth Object data with orbital details

### Mars Rover Tools  
- **get_mars_rover_photos**: Photos from Curiosity, Opportunity, Spirit, Perseverance
- **get_latest_mars_photos**: Latest photos from any rover
- **get_rover_mission_info**: Mission data, cameras, and sol ranges

### Earth Imagery Tools
- **get_earth_imagery**: Full-disc Earth images from EPIC/DSCOVR satellite
- **get_available_earth_dates**: Available Earth imagery dates

### Natural Events Tools
- **get_natural_events**: Track wildfires, storms, volcanoes via EONET
- **get_event_categories**: Available natural disaster categories

All image tools support optional rendering with `return_images=True` for direct client display.

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

## 🌐 Smithery Deployment

Deploy this NASA MCP Server on Smithery for automatic scaling, zero maintenance, and 24/7 uptime.

### Prerequisites

1. **NASA API Key**: Get your free API key from [api.nasa.gov](https://api.nasa.gov/)
2. **Smithery Account**: Create an account at [smithery.ai](https://smithery.ai)

### Deployment Steps

1. **Get NASA API Key**:
   - Visit [api.nasa.gov](https://api.nasa.gov/)
   - Complete the simple registration form
   - Receive your API key via email (much higher rate limits than DEMO_KEY)

2. **Deploy to Smithery**:
   - Visit [smithery.ai](https://smithery.ai) and create an account
   - Connect this GitHub repository
   - Configure your NASA API key during setup
   - Smithery will automatically build and deploy the container

3. **Use Your Server**:
   - Access all 10 NASA tools through any MCP-compatible client
   - Each tool uses your provided API key for authentication
   - Enjoy automatic scaling and zero maintenance

### Deployment Benefits

- **Automatic Scaling**: Handles traffic spikes automatically
- **Zero Maintenance**: No server management required  
- **Secure**: NASA API keys stored securely
- **Multi-User**: Share with team members safely
- **24/7 Uptime**: Always available when you need it

## 📊 API Coverage

- **APOD API**: Daily astronomy images with explanations
- **Mars Rover Photos API**: Multi-rover archives with camera filtering
- **EPIC API**: Full-disc Earth imagery from L1 Lagrange point
- **EONET API**: Real-time natural disaster tracking
- **NEO API**: Near-Earth asteroid orbital data

## License

This project is provided for educational and research purposes. See LICENSE for details.