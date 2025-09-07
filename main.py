from helper_functions import _encode_image
import io
import os
import aiohttp
from PIL import Image as PILImage
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from datetime import datetime
from pytz import timezone
from mcp.types import ImageContent
from aiohttp import ClientTimeout
import pandas as pd
from typing import List, Dict, Any, Optional, Union


_ = load_dotenv()

# Get NASA API key from environment
NASA_API_KEY = os.getenv("NASA_API_KEY")

mcp = FastMCP("NASA MCP", port=8000, host="0.0.0.0")


@mcp.tool()
async def get_picture_of_the_day() -> ImageContent:
    """
    Get NASA's Astronomy Picture of the Day (APOD) as an image with metadata.
    
    Returns the daily featured astronomy image from NASA, which could be a photograph, 
    diagram, or artwork related to space science. The image includes title, date, and 
    detailed explanation printed to console. Use this when users ask about today's 
    astronomy picture, space images, or want to see NASA's featured content.
    
    Returns:
        ImageContent: The APOD image that can be displayed directly in the client
    """

    # Set a longer timeout (30 seconds)
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Get NASA APOD data
            async with session.get(
                f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
            ) as response:
                if response.status != 200:
                    raise Exception(f"NASA API returned status {response.status}")
                data = await response.json()

            # Download the image
            async with session.get(data.get("url", data.get("hdurl"))) as img_response:
                if img_response.status != 200:
                    raise Exception(
                        f"Image download failed with status {img_response.status}"
                    )
                img_bytes = await img_response.read()

        # Convert to PIL Image
        image = PILImage.open(io.BytesIO(img_bytes))

        # Print metadata
        print(
            f"Title: {data['title']}\nDate: {data['date']}\n\nExplanation: {data['explanation']}"
        )

        return _encode_image(image)

    except Exception as e:
        # Create a simple error image instead of returning a string
        error_image = PILImage.new("RGB", (400, 100), color="red")
        # You might want to add error text to the image here
        print(f"Error occurred: {str(e)}")
        return _encode_image(error_image)


@mcp.tool()
async def get_time() -> str:
    """Get the current date and time in IST timezone. Should be run when current time context is needed. Should be ideally called before calling other tools when users define time ranges that are vague (e.g., "last 3 days", "next week", "today") etc."""
    fmt = "%Y-%m-%d"

    ist_time = datetime.now(timezone("Asia/Kolkata"))
    ist_time = ist_time.strftime(fmt)

    return f"""Current Date (IST): {ist_time}"""


@mcp.tool()
async def get_neo_asteroids(
    start_date: str, end_date: str
) -> List[Dict[str, Any]]:
    """
    Retrieve Near Earth Objects (NEOs) detected by NASA between specified dates.
    
    Searches for asteroids that come close to Earth's orbit and provides detailed 
    information about their size, velocity, distance, and potential hazard status.
    Use this when users ask about asteroids, space threats, or celestial objects.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (e.g., '2024-01-01')
        end_date: End date in YYYY-MM-DD format (e.g., '2024-01-07')
                 Note: Date range limited to 7 days maximum by NASA API
    
    Returns:
        List of NEO records, each containing:
        - id, name: Asteroid identification  
        - observed_date: When it approaches closest to Earth
        - estimated diameters in meters and kilometers
        - relative velocity in km/s and km/h
        - miss distance in astronomical units, lunar distance, km, and miles
        - is_potentially_hazardous_asteroid: Boolean safety indicator
        - orbital details and coordinates
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = (
                f"https://api.nasa.gov/neo/rest/v1/feed?"
                f"start_date={start_date}&end_date={end_date}&api_key={NASA_API_KEY}"
            )
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"NASA API returned status {response.status}")
                data = await response.json()

        rows: List[Dict[str, Any]] = []
        neo_map = data.get("near_earth_objects", {})
        for date_key, neos_on_date in neo_map.items():
            for neo in neos_on_date:
                neo_id = neo.get("id")
                name = neo.get("name")
                abs_mag = neo.get("absolute_magnitude_h")
                is_hazard = neo.get("is_potentially_hazardous_asteroid")
                is_sentry = neo.get("is_sentry_object")

                ed = neo.get("estimated_diameter", {})
                km = ed.get("kilometers", {})
                m = ed.get("meters", {})
                ed_km_min = km.get("estimated_diameter_min")
                ed_km_max = km.get("estimated_diameter_max")
                ed_m_min = m.get("estimated_diameter_min")
                ed_m_max = m.get("estimated_diameter_max")
                ed_m_mean = (
                    (ed_m_min + ed_m_max) / 2.0
                    if ed_m_min is not None and ed_m_max is not None
                    else None
                )

                for cad in neo.get("close_approach_data", []):
                    cad_date = cad.get("close_approach_date")
                    cad_date_full = cad.get("close_approach_date_full")
                    epoch = cad.get("epoch_date_close_approach")

                    rel_vel = cad.get("relative_velocity", {})
                    rv_km_s = _safe_float(rel_vel.get("kilometers_per_second"))
                    rv_km_h = _safe_float(rel_vel.get("kilometers_per_hour"))

                    miss = cad.get("miss_distance", {})
                    miss_astronomical = _safe_float(miss.get("astronomical"))
                    miss_lunar = _safe_float(miss.get("lunar"))
                    miss_km = _safe_float(miss.get("kilometers"))
                    miss_miles = _safe_float(miss.get("miles"))

                    orbiting_body = cad.get("orbiting_body")

                    rows.append(
                        {
                            "id": neo_id,
                            "name": name,
                            "observed_date": cad_date,
                            "observed_date_full": cad_date_full,
                            "epoch_date_close_approach": epoch,
                            "absolute_magnitude_h": _safe_float(abs_mag),
                            "est_diameter_m_min": _safe_float(ed_m_min),
                            "est_diameter_m_max": _safe_float(ed_m_max),
                            "est_diameter_km_min": _safe_float(ed_km_min),
                            "est_diameter_km_max": _safe_float(ed_km_max),
                            "est_diameter_m_mean": _safe_float(ed_m_mean),
                            "is_potentially_hazardous_asteroid": bool(is_hazard),
                            "is_sentry_object": bool(is_sentry),
                            "relative_velocity_km_s": rv_km_s,
                            "relative_velocity_km_h": rv_km_h,
                            "miss_distance_astronomical": miss_astronomical,
                            "miss_distance_lunar": miss_lunar,
                            "miss_distance_km": miss_km,
                            "miss_distance_miles": miss_miles,
                            "orbiting_body": orbiting_body,
                            "api_feed_date": date_key,
                        }
                    )

        df = pd.DataFrame(rows)
        if not df.empty:
            numeric_cols = [
                "absolute_magnitude_h",
                "est_diameter_m_min",
                "est_diameter_m_max",
                "est_diameter_km_min",
                "est_diameter_km_max",
                "est_diameter_m_mean",
                "relative_velocity_km_s",
                "relative_velocity_km_h",
                "miss_distance_astronomical",
                "miss_distance_lunar",
                "miss_distance_km",
                "miss_distance_miles",
                "epoch_date_close_approach",
            ]
            for c in numeric_cols:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce")

            if "observed_date" in df.columns:
                df["observed_date"] = pd.to_datetime(
                    df["observed_date"], errors="coerce"
                )
            if "observed_date_full" in df.columns:
                df["observed_date_full"] = pd.to_datetime(
                    df["observed_date_full"], errors="coerce"
                )

        return df.to_dict(orient="records")

    except Exception as e:
        print(f"Error occurred while fetching NEOs: {e}")
        return [{"error": str(e)}]


@mcp.tool()
async def get_mars_rover_photos(
    rover: str,
    sol: Optional[int] = None,
    earth_date: Optional[str] = None,
    camera: Optional[str] = None,
    page: int = 1,
    return_images: bool = True,
) -> Union[List[Dict[str, Any]], List[ImageContent]]:
    """
    Get photos from Mars rovers with detailed metadata and optional image download.
    
    Retrieves photos from NASA's Mars rovers including mission details, camera info, 
    and coordinates. Use this when users want to see Mars surface images, explore 
    rover missions, or get photos from specific dates or cameras.

    Args:
        rover: Rover name - must be one of: 'curiosity', 'opportunity', 'spirit', 'perseverance'
        sol: Martian sol (day since landing) - use either sol or earth_date, not both
        earth_date: Earth date in YYYY-MM-DD format - use either sol or earth_date
        camera: Camera abbreviation (optional). Available cameras vary by rover:
               Common: FHAZ (Front Hazard), RHAZ (Rear Hazard), NAVCAM (Navigation)
               Curiosity: MAST (Mast Camera), CHEMCAM, MAHLI, MARDI
        page: Page number for pagination (default: 1, returns ~25 photos per page)
        return_images: If True, downloads actual images (default); if False, returns URLs only
    
    Returns:
        If return_images=False: List of photo records with img_src URLs, dates, camera info, rover status
        If return_images=True: List of ImageContent objects that display directly in the client
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Build URL parameters
            params = {"api_key": NASA_API_KEY, "page": page}

            if sol is not None:
                params["sol"] = sol
            elif earth_date is not None:
                params["earth_date"] = earth_date
            else:
                # Default to latest photos if no date specified
                url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/latest_photos"

            if sol is not None or earth_date is not None:
                url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos"

            if camera:
                params["camera"] = camera.upper()

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Mars Rover API returned status {response.status}")
                data = await response.json()

        # Extract photos from response
        photos = data.get("photos", data.get("latest_photos", []))

        # Process and return photo data
        if return_images:
            # Return ImageContent objects for direct client display
            images = []
            async with aiohttp.ClientSession(timeout=timeout) as img_session:
                for photo in photos:
                    if photo.get("img_src"):
                        try:
                            async with img_session.get(photo["img_src"]) as img_response:
                                if img_response.status == 200:
                                    img_bytes = await img_response.read()
                                    image = PILImage.open(io.BytesIO(img_bytes))
                                    images.append(_encode_image(image))
                                else:
                                    print(f"Image download failed for {photo.get('id')}: HTTP {img_response.status}")
                                    # Skip failed downloads instead of creating red boxes
                                    continue
                        except Exception as img_error:
                            print(f"Image processing error for {photo.get('id')}: {str(img_error)}")
                            # Skip failed downloads instead of creating red boxes
                            continue
            return images
        else:
            # Return metadata only
            result = []
            for photo in photos:
                photo_data = {
                    "id": photo.get("id"),
                    "img_src": photo.get("img_src"),
                    "earth_date": photo.get("earth_date"),
                    "sol": photo.get("sol"),
                    "camera_name": photo.get("camera", {}).get("full_name"),
                    "camera_abbrev": photo.get("camera", {}).get("name"),
                    "rover_name": photo.get("rover", {}).get("name"),
                    "rover_status": photo.get("rover", {}).get("status"),
                    "rover_launch_date": photo.get("rover", {}).get("launch_date"),
                    "rover_landing_date": photo.get("rover", {}).get("landing_date"),
                }
                result.append(photo_data)
            return result

    except Exception as e:
        print(f"Error occurred while fetching Mars rover photos: {e}")
        return [{"error": str(e)}]


@mcp.tool()
async def get_latest_mars_photos(
    rover: str, return_images: bool = True
) -> Union[List[Dict[str, Any]], List[ImageContent]]:
    """
    Get the most recent photos from a specified Mars rover.
    
    Retrieves the latest available photos from a rover, which is useful when you want 
    the most current Mars surface images without specifying dates. Automatically 
    finds the rover's most recent photography session.

    Args:
        rover: Rover name - must be one of: 'curiosity', 'opportunity', 'spirit', 'perseverance'
        return_images: If True, downloads and embeds actual images (default); if False, returns URLs only
    
    Returns:
        If return_images=False: List of photo records with img_src URLs, dates, camera info
        If return_images=True: List of ImageContent objects that display directly in the client
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = (
                f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/latest_photos"
            )
            params = {"api_key": NASA_API_KEY}

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Mars Rover API returned status {response.status}")
                data = await response.json()

        # Extract latest photos
        latest_photos = data.get("latest_photos", [])

        # Process and return photo data
        if return_images:
            # Return ImageContent objects for direct client display
            images = []
            async with aiohttp.ClientSession(timeout=timeout) as img_session:
                for photo in latest_photos:
                    if photo.get("img_src"):
                        try:
                            async with img_session.get(photo["img_src"]) as img_response:
                                if img_response.status == 200:
                                    img_bytes = await img_response.read()
                                    image = PILImage.open(io.BytesIO(img_bytes))
                                    images.append(_encode_image(image))
                                else:
                                    print(f"Image download failed for {photo.get('id')}: HTTP {img_response.status}")
                                    continue
                        except Exception as img_error:
                            print(f"Image processing error for {photo.get('id')}: {str(img_error)}")
                            continue
            return images
        else:
            # Return metadata only
            result = []
            for photo in latest_photos:
                photo_data = {
                    "id": photo.get("id"),
                    "img_src": photo.get("img_src"),
                    "earth_date": photo.get("earth_date"),
                    "sol": photo.get("sol"),
                    "camera_name": photo.get("camera", {}).get("full_name"),
                    "camera_abbrev": photo.get("camera", {}).get("name"),
                    "rover_name": photo.get("rover", {}).get("name"),
                }
                result.append(photo_data)
            return result

    except Exception as e:
        print(f"Error occurred while fetching latest Mars rover photos: {e}")
        return [{"error": str(e)}]


@mcp.tool()
async def get_rover_mission_info(rover: str) -> Dict[str, Any]:
    """
    Get comprehensive mission information for a Mars rover including operational details.
    
    Retrieves mission manifest data including launch/landing dates, operational status,
    available cameras, sol ranges, and total photo counts. Use this to understand 
    rover capabilities before requesting specific photos or to get mission overview.

    Args:
        rover: Rover name - must be one of: 'curiosity', 'opportunity', 'spirit', 'perseverance'
    
    Returns:
        Mission data including:
        - name, landing_date, launch_date, status (active/complete)
        - max_sol: Latest sol (Martian day) with available data
        - max_date: Latest Earth date with photos
        - total_photos: Total number of photos taken by this rover
        - cameras: List of available cameras with abbreviations and full names
        - sols_with_photos: Number of sols that have photo data
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"https://api.nasa.gov/mars-photos/api/v1/manifests/{rover}"
            params = {"api_key": NASA_API_KEY}

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Mars Rover API returned status {response.status}")
                data = await response.json()

        # Extract manifest data
        manifest = data.get("photo_manifest", {})

        return {
            "name": manifest.get("name"),
            "landing_date": manifest.get("landing_date"),
            "launch_date": manifest.get("launch_date"),
            "status": manifest.get("status"),
            "max_sol": manifest.get("max_sol"),
            "max_date": manifest.get("max_date"),
            "total_photos": manifest.get("total_photos"),
            "cameras": [
                {"name": cam.get("name"), "full_name": cam.get("full_name")}
                for cam in manifest.get("cameras", [])
            ],
            "sols_with_photos": len(manifest.get("photos", [])),
        }

    except Exception as e:
        print(f"Error occurred while fetching rover mission info: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_earth_imagery(
    date: Optional[str] = None,
    image_type: str = "natural",
    return_images: bool = True,
) -> Union[List[Dict[str, Any]], List[ImageContent]]:
    """
    Get full-disc Earth images from NASA's EPIC camera on the DSCOVR satellite.
    
    Retrieves images of Earth from space showing the full sunlit side of the planet,
    taken from the L1 Lagrange point ~1 million miles away. Images show weather patterns,
    seasonal changes, and Earth's rotation. Use for Earth observation, climate study,
    or when users want to see Earth from space.

    Args:
        date: Date in YYYY-MM-DD format (optional, defaults to most recent available)
              Note: EPIC data typically starts from 2015-06-13 and only has historical data.
              Use get_available_earth_dates() to see available dates.
        image_type: Image processing type - 'natural' (true color) or 'enhanced' (processed)
        return_images: If True, downloads actual images (default); if False, returns URLs and metadata only
    
    Returns:
        If return_images=False: List of Earth image records with metadata:
            - image name, caption, date, and direct image_url
            - centroid_coordinates: lat/lon of Earth's center in the image  
            - satellite positions: DSCOVR, Moon, and Sun coordinates in J2000 reference
            - attitude_quaternions: Camera orientation data
        If return_images=True: List of ImageContent objects that display directly in the client
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Build URL based on parameters
            if date:
                url = f"https://api.nasa.gov/EPIC/api/{image_type}/date/{date}"
            else:
                url = f"https://api.nasa.gov/EPIC/api/{image_type}"

            params = {"api_key": NASA_API_KEY}

            async with session.get(url, params=params) as response:
                if response.status == 503:
                    raise Exception(f"EPIC API service unavailable (503). The service may be down or the date {date} has no available imagery. Try omitting the date parameter for most recent imagery.")
                elif response.status == 404:
                    raise Exception(f"No EPIC imagery available for date {date}. Try a different date (YYYY-MM-DD format) or omit date parameter for most recent imagery.")
                elif response.status != 200:
                    raise Exception(f"EPIC API returned status {response.status}")
                data = await response.json()

        # Process EPIC data
        if return_images:
            # Return ImageContent objects for direct client display
            images = []
            async with aiohttp.ClientSession(timeout=timeout) as img_session:
                for image in data:
                    # Extract date for image URL construction
                    image_date = (
                        image.get("date", "").split(" ")[0] if image.get("date") else ""
                    )
                    formatted_date = image_date.replace("-", "/") if image_date else ""

                    # Construct image URL
                    image_name = image.get("image", "")
                    if formatted_date and image_name:
                        image_url = f"https://epic.gsfc.nasa.gov/archive/{image_type}/{formatted_date}/png/{image_name}.png"

                        try:
                            async with img_session.get(image_url) as img_response:
                                if img_response.status == 200:
                                    img_bytes = await img_response.read()
                                    pil_image = PILImage.open(io.BytesIO(img_bytes))
                                    images.append(_encode_image(pil_image))
                                else:
                                    print(f"Earth image download failed for {image.get('image')}: HTTP {img_response.status}")
                                    continue
                        except Exception as img_error:
                            print(f"Earth image processing error for {image.get('image')}: {str(img_error)}")
                            continue
            return images
        else:
            # Return metadata only
            result = []
            for image in data:
                # Extract date for image URL construction
                image_date = (
                    image.get("date", "").split(" ")[0] if image.get("date") else ""
                )
                formatted_date = image_date.replace("-", "/") if image_date else ""

                # Construct image URL
                image_name = image.get("image", "")
                if formatted_date and image_name:
                    image_url = f"https://epic.gsfc.nasa.gov/archive/{image_type}/{formatted_date}/png/{image_name}.png"
                else:
                    image_url = None

                image_data = {
                    "image": image.get("image"),
                    "caption": image.get("caption"),
                    "date": image.get("date"),
                    "image_url": image_url,
                    "centroid_coordinates": image.get("centroid_coordinates", {}),
                    "dscovr_j2000_position": image.get("dscovr_j2000_position", {}),
                    "lunar_j2000_position": image.get("lunar_j2000_position", {}),
                    "sun_j2000_position": image.get("sun_j2000_position", {}),
                    "attitude_quaternions": image.get("attitude_quaternions", {}),
                    "coords": {
                        "lat": image.get("centroid_coordinates", {}).get("lat"),
                        "lon": image.get("centroid_coordinates", {}).get("lon"),
                    },
                }
                result.append(image_data)
            return result

    except aiohttp.ClientConnectorError as e:
        print(f"EPIC API connection failed: {e}")
        return [{"error": "EPIC API is currently unavailable due to connection issues. NASA's EPIC service may be experiencing downtime. Please try again later."}]
    except Exception as e:
        print(f"Error occurred while fetching Earth imagery: {e}")
        error_msg = str(e)
        if "503" in error_msg or "502" in error_msg or "504" in error_msg:
            return [{"error": f"{error_msg} NASA's EPIC service appears to be experiencing issues. This is common and usually temporary."}]
        return [{"error": str(e)}]


@mcp.tool()
async def get_available_earth_dates(
    image_type: str = "natural"
) -> List[str]:
    """
    Get all available dates when EPIC Earth imagery was captured.
    
    Returns a chronological list of dates when the EPIC camera took Earth images.
    Useful for finding available dates before requesting specific Earth imagery,
    or for understanding the temporal coverage of the dataset.

    Args:
        image_type: Image processing type - 'natural' (true color) or 'enhanced' (processed)
    
    Returns:
        Sorted list of date strings in YYYY-MM-DD format when imagery is available
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"https://api.nasa.gov/EPIC/api/{image_type}/all"
            params = {"api_key": NASA_API_KEY}

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"EPIC API returned status {response.status}")
                data = await response.json()

        # Extract dates from response
        if isinstance(data, list):
            dates = []
            for item in data:
                if isinstance(item, dict) and "date" in item:
                    date_str = (
                        item["date"].split(" ")[0]
                        if " " in item["date"]
                        else item["date"]
                    )
                    if date_str not in dates:
                        dates.append(date_str)
                elif isinstance(item, str):
                    dates.append(item)
            return sorted(dates)
        else:
            return []

    except aiohttp.ClientConnectorError as e:
        print(f"EPIC API connection failed: {e}")
        return ["EPIC API is currently unavailable due to connection issues. NASA's EPIC service may be experiencing downtime. Please try again later."]
    except Exception as e:
        print(f"Error occurred while fetching available Earth dates: {e}")
        error_msg = str(e)
        if "503" in error_msg or "502" in error_msg or "504" in error_msg:
            return [f"Error: {error_msg} NASA's EPIC service appears to be experiencing issues. This is common and usually temporary."]
        return [f"Error: {str(e)}"]


@mcp.tool()
async def get_natural_events(
    category: Optional[str] = None,
    status: str = "open",
    limit: Optional[int] = None,
    days: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Get natural disaster and environmental events tracked by NASA's EONET system.
    
    Retrieves real-time data on natural events like wildfires, storms, volcanoes,
    floods, and other environmental phenomena worldwide. Each event includes location,
    timing, and source information. Use for disaster monitoring, environmental 
    research, or when users ask about current natural events.

    Args:
        category: Event category (optional). Available categories:
                 'wildfires', 'severeStorms', 'volcanoes', 'floods', 'droughts',
                 'dustHaze', 'snowIce', 'earthquakes', 'landslides', 'manmade'
        status: Event status - 'open' (ongoing), 'closed' (ended), or 'all' (default: 'open')
        limit: Maximum number of events to return (optional, useful for large result sets)
        days: Only show events from last N days (optional, e.g., days=7 for past week)
    
    Returns:
        List of natural events with:
        - id, title, description: Event identification and details
        - categories: Event type classifications  
        - latest_coordinates: Most recent lat/lon location
        - latest_date: Most recent observation date
        - closed: Whether event has ended
        - sources: Data source URLs and references
        - geometry_count: Number of location updates tracked
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = "https://eonet.gsfc.nasa.gov/api/v3/events"
            params = {}

            if category:
                params["category"] = category
            if status != "open":
                params["status"] = status
            if limit:
                params["limit"] = limit
            if days:
                params["days"] = days

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"EONET API returned status {response.status}")
                data = await response.json()

        # Process events
        events = data.get("events", [])
        result = []

        for event in events:
            # Get latest geometry (most recent location)
            geometries = event.get("geometry", [])
            latest_geometry = geometries[-1] if geometries else {}

            # Extract coordinates
            coords = latest_geometry.get("coordinates", [])
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]
            else:
                lon, lat = None, None

            result.append(
                {
                    "id": event.get("id"),
                    "title": event.get("title"),
                    "description": event.get("description"),
                    "link": event.get("link"),
                    "closed": event.get("closed"),
                    "categories": [
                        {"id": cat.get("id"), "title": cat.get("title")}
                        for cat in event.get("categories", [])
                    ],
                    "sources": [
                        {"id": src.get("id"), "url": src.get("url")}
                        for src in event.get("sources", [])
                    ],
                    "latest_coordinates": {"lat": lat, "lon": lon}
                    if lat and lon
                    else None,
                    "latest_date": latest_geometry.get("date"),
                    "geometry_count": len(geometries),
                }
            )

        return result

    except Exception as e:
        print(f"Error occurred while fetching natural events: {e}")
        return [{"error": str(e)}]


@mcp.tool()
async def get_event_categories() -> List[Dict[str, Any]]:
    """
    Get all available natural event categories that can be tracked by EONET.
    
    Returns the complete list of event categories that EONET monitors, with 
    descriptions and metadata. Use this to discover what types of natural 
    events are available before querying specific categories with get_natural_events.
    
    Returns:
        List of event categories with:
        - id: Category identifier (use this value for get_natural_events category parameter)
        - title: Human-readable category name
        - description: Detailed explanation of what events this category covers
        - link: Reference URL for more information
        - layers: Associated map layer information
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = "https://eonet.gsfc.nasa.gov/api/v3/categories"

            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"EONET API returned status {response.status}")
                data = await response.json()

        # Process categories
        categories = data.get("categories", [])
        result = []

        for category in categories:
            result.append(
                {
                    "id": category.get("id"),
                    "title": category.get("title"),
                    "link": category.get("link"),
                    "description": category.get("description"),
                    "layers": category.get("layers"),
                }
            )

        return result

    except Exception as e:
        print(f"Error occurred while fetching event categories: {e}")
        return [{"error": str(e)}]


def _safe_float(v):
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


if __name__ == "__main__":
    import sys
    
    # Default to HTTP transport for cloud hosting, allow stdio for local development
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        mcp.run(transport="stdio")
    else:
        # Use streamable-http for cloud hosting
        mcp.run(transport="streamable-http")
