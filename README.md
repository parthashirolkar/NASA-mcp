# NASA MCP Server

A comprehensive Model Context Protocol (MCP) server for interacting with multiple NASA APIs. Designed for local AI clients with rich image rendering and robust error handling.

## Features

### Core Tools
- **Astronomy Picture of the Day (APOD)**: Daily NASA astronomy images with metadata
- **Near Earth Objects (NEOs)**: Asteroid tracking and close approach data
- **Mars Rover Photos**: Images from Curiosity, Opportunity, and Spirit rovers
- **Earth Imagery (EPIC)**: Earth photos from the Deep Space Climate Observatory
- **Natural Events (EONET)**: Real-time tracking of wildfires, storms, volcanoes, etc.
- **Current Time**: IST timezone support for date-based queries

### Image Rendering
- All image tools return rendered `ImageContent` objects by default for direct client display
- Automatic base64 encoding and PIL image processing
- Fallback to URL strings when image rendering is disabled

### Error Handling
- Graceful handling of NASA API outages (common with EPIC and other services)
- Informative error messages with status codes
- Separate HTTP sessions to prevent request conflicts

## Requirements

- Python 3.12+
- NASA API key (get one free at [nasa-api](https://api.nasa.gov/))

## Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd NASA-mcp
   ```

2. **Install dependencies**:
   ```bash
   uv install
   # OR
   pip install -e .
   ```

3. **Set up environment variables**:
   ```bash
   # Create .env file in project root
   echo "NASA_API_KEY=your_nasa_api_key_here" > .env
   ```
   
   Get your free NASA API key at: https://api.nasa.gov/

4. **Configure your AI client**:
   Add this server to your MCP client configuration (Claude Desktop, etc.):
   ```json
   {
     "mcpServers": {
       "nasa": {
         "command": "python",
         "args": ["/path/to/NASA-mcp/main.py"],
         "env": {
           "NASA_API_KEY": "your_nasa_api_key_here"
         }
       }
     }
   }
   ```

## Usage

### Cloud Hosting (Default)
For cloud hosting, simply run:
```bash
python main.py
```
The server defaults to HTTP transport on port 8000 for cloud deployment.

### Local Development
For local development with AI clients (Claude Desktop, etc.):
```bash
python main.py --stdio
```
This uses stdio transport for local AI client communication.

### Available Tools

1. **get_picture_of_the_day()** - NASA's daily astronomy image
2. **get_time()** - Current date in IST timezone
3. **get_neo_asteroids(start_date, end_date)** - Near Earth Object data
4. **get_mars_rover_photos(rover, sol, camera?, return_images?)** - Mars rover imagery
5. **get_latest_mars_photos(rover, return_images?)** - Most recent rover photos
6. **get_rover_mission_info(rover)** - Mission status and specifications
7. **get_earth_imagery(date, return_images?)** - Earth photos from space
8. **get_available_earth_dates()** - Available EPIC imagery dates
9. **get_natural_events(status?, limit?, days?)** - Environmental events tracking
10. **get_event_categories()** - Types of natural events monitored

### Parameters
- Most image tools default to `return_images=True` for better UX
- Dates should be in `YYYY-MM-DD` format
- Rover options: `curiosity`, `opportunity`, `spirit`
- Camera types: `FHAZ`, `RHAZ`, `MAST`, `CHEMCAM`, `MAHLI`, `MARDI`, `NAVCAM`, `PANCAM`, `MINITES`

## File Structure

```
NASA-mcp/
├── main.py                 # MCP server and tool definitions
├── helper_functions.py     # Image processing utilities
├── pyproject.toml         # Dependencies and project config
├── .env                   # NASA API key (not in git)
├── .gitignore            # Excludes .env files
└── README.md             # This file
```

## Cloud Deployment

This server is configured for easy cloud deployment:

### Features for Cloud Hosting
- **HTTP Transport**: Defaults to `streamable-http` on port 8000
- **Environment Variables**: Uses `.env` file or system environment variables for NASA API key
- **Containerization Ready**: Works with any Python hosting platform using `uv`
- **Health Check**: Server starts and runs continuously

### Deployment Instructions
1. **Set NASA_API_KEY environment variable** on your hosting platform
2. **Install dependencies**: Platform will run `uv install`
3. **Start server**: Platform will run `python main.py`
4. **Access**: Server will be available on port 8000

### Environment Variables Required
```bash
NASA_API_KEY=your_nasa_api_key_here
```

## API Rate Limits

NASA APIs are generally free but have rate limits:
- Default: 1,000 requests per hour
- With API key: Higher limits and priority access
- Some services (like EPIC) experience frequent outages

## Troubleshooting

### Common Issues
- **503/404 Errors**: NASA APIs occasionally go down. Try again later.
- **Red box images**: Usually indicates API connectivity issues
- **Missing images**: Check your NASA_API_KEY in .env file
- **Import errors**: Run `uv install` or `pip install -e .`

### Debug Tips
- Check NASA API status at: https://api.nasa.gov/
- Verify your API key at: https://api.nasa.gov/
- Test individual endpoints in browser with your key

## License

Educational and research use. NASA imagery is public domain.