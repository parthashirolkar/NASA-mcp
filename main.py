from helper_functions import _encode_image
import io
import aiohttp
from PIL import Image as PILImage
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from datetime import datetime
from pytz import timezone
from mcp.types import ImageContent
from aiohttp import ClientTimeout
import pandas as pd
from typing import List, Dict, Any, Optional


_ = load_dotenv()

mcp = FastMCP("NASA MCP")


@mcp.tool()
async def get_picture_of_the_day(nasa_api_key: str) -> ImageContent:
    """Get the NASA Picture of the Day. Requires a valid NASA API key."""

    # Set a longer timeout (30 seconds)
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Get NASA APOD data
            async with session.get(
                f"https://api.nasa.gov/planetary/apod?api_key={nasa_api_key}"
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
    nasa_api_key: str, start_date: str, end_date: str
) -> List[Dict[str, Any]]:
    """
    Retrieve Near Earth Objects between start_date and end_date and return a list of records (dicts).
    Requires a valid NASA API key.

    Each record (one per close-approach event) contains useful features (id, name, observed_date, etc.).
    Returns a JSON-serializable list of dicts suitable for MCP/LM Studio.
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = (
                f"https://api.nasa.gov/neo/rest/v1/feed?"
                f"start_date={start_date}&end_date={end_date}&api_key={nasa_api_key}"
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
    nasa_api_key: str,
    rover: str,
    sol: Optional[int] = None,
    earth_date: Optional[str] = None,
    camera: Optional[str] = None,
    page: int = 1,
    return_images: bool = False,
) -> List[Dict[str, Any]]:
    """
    Get photos from Mars rovers (Curiosity, Opportunity, Spirit, Perseverance).
    Requires a valid NASA API key.

    Args:
        rover: Rover name (curiosity, opportunity, spirit, perseverance)
        sol: Martian sol (day) - use either sol or earth_date, not both
        earth_date: Earth date (YYYY-MM-DD format) - use either sol or earth_date
        camera: Camera abbreviation (optional) - e.g., FHAZ, RHAZ, MAST, CHEMCAM, MAHLI, MARDI, NAVCAM
        page: Page number for pagination (default: 1)
        return_images: If True, download and return actual images (default: False, returns URLs only)
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Build URL parameters
            params = {"api_key": nasa_api_key, "page": page}

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

            # Optionally download and encode the actual image
            if return_images and photo.get("img_src"):
                try:
                    async with session.get(photo["img_src"]) as img_response:
                        if img_response.status == 200:
                            img_bytes = await img_response.read()
                            image = PILImage.open(io.BytesIO(img_bytes))
                            photo_data["image"] = _encode_image(image)
                        else:
                            photo_data["image_error"] = (
                                f"Failed to download image: status {img_response.status}"
                            )
                except Exception as img_error:
                    photo_data["image_error"] = (
                        f"Image processing error: {str(img_error)}"
                    )

            result.append(photo_data)

        return result

    except Exception as e:
        print(f"Error occurred while fetching Mars rover photos: {e}")
        return [{"error": str(e)}]


@mcp.tool()
async def get_latest_mars_photos(
    nasa_api_key: str, rover: str, return_images: bool = False
) -> List[Dict[str, Any]]:
    """
    Get the latest photos from a Mars rover.
    Requires a valid NASA API key.

    Args:
        rover: Rover name (curiosity, opportunity, spirit, perseverance)
        return_images: If True, download and return actual images (default: False, returns URLs only)
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = (
                f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/latest_photos"
            )
            params = {"api_key": nasa_api_key}

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Mars Rover API returned status {response.status}")
                data = await response.json()

        # Extract latest photos
        latest_photos = data.get("latest_photos", [])

        # Process and return photo data
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

            # Optionally download and encode the actual image
            if return_images and photo.get("img_src"):
                try:
                    async with session.get(photo["img_src"]) as img_response:
                        if img_response.status == 200:
                            img_bytes = await img_response.read()
                            image = PILImage.open(io.BytesIO(img_bytes))
                            photo_data["image"] = _encode_image(image)
                        else:
                            photo_data["image_error"] = (
                                f"Failed to download image: status {img_response.status}"
                            )
                except Exception as img_error:
                    photo_data["image_error"] = (
                        f"Image processing error: {str(img_error)}"
                    )

            result.append(photo_data)

        return result

    except Exception as e:
        print(f"Error occurred while fetching latest Mars rover photos: {e}")
        return [{"error": str(e)}]


@mcp.tool()
async def get_rover_mission_info(nasa_api_key: str, rover: str) -> Dict[str, Any]:
    """
    Get mission manifest data for a Mars rover including available cameras and sol range.
    Requires a valid NASA API key.

    Args:
        rover: Rover name (curiosity, opportunity, spirit, perseverance)
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/manifests"
            params = {"api_key": nasa_api_key}

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
    nasa_api_key: str,
    date: Optional[str] = None,
    image_type: str = "natural",
    return_images: bool = False,
) -> List[Dict[str, Any]]:
    """
    Get Earth imagery from EPIC (Earth Polychromatic Imaging Camera) on DSCOVR satellite.
    Requires a valid NASA API key.

    Args:
        date: Date in YYYY-MM-DD format (optional, defaults to most recent available)
        image_type: 'natural' or 'enhanced' (default: 'natural')
        return_images: If True, download and return actual images (default: False, returns URLs only)
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Build URL based on parameters
            if date:
                url = f"https://api.nasa.gov/EPIC/api/{image_type}/date/{date}"
            else:
                url = f"https://api.nasa.gov/EPIC/api/{image_type}"

            params = {"api_key": nasa_api_key}

            async with session.get(url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"EPIC API returned status {response.status}")
                data = await response.json()

        # Process EPIC data
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

            # Optionally download and encode the actual image
            if return_images and image_url:
                try:
                    async with session.get(image_url) as img_response:
                        if img_response.status == 200:
                            img_bytes = await img_response.read()
                            pil_image = PILImage.open(io.BytesIO(img_bytes))
                            image_data["rendered_image"] = _encode_image(pil_image)
                        else:
                            image_data["image_error"] = (
                                f"Failed to download image: status {img_response.status}"
                            )
                except Exception as img_error:
                    image_data["image_error"] = (
                        f"Image processing error: {str(img_error)}"
                    )

            result.append(image_data)

        return result

    except Exception as e:
        print(f"Error occurred while fetching Earth imagery: {e}")
        return [{"error": str(e)}]


@mcp.tool()
async def get_available_earth_dates(
    nasa_api_key: str, image_type: str = "natural"
) -> List[str]:
    """
    Get all available dates for Earth imagery from EPIC.
    Requires a valid NASA API key.

    Args:
        image_type: 'natural' or 'enhanced' (default: 'natural')
    """
    timeout = ClientTimeout(total=30)

    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            url = f"https://api.nasa.gov/EPIC/api/{image_type}/all"
            params = {"api_key": nasa_api_key}

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

    except Exception as e:
        print(f"Error occurred while fetching available Earth dates: {e}")
        return [f"Error: {str(e)}"]


@mcp.tool()
async def get_natural_events(
    nasa_api_key: str,
    category: Optional[str] = None,
    status: str = "open",
    limit: Optional[int] = None,
    days: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Get natural events from EONET (Earth Observatory Natural Event Tracker).
    Note: EONET API doesn't require API key but we keep parameter for consistency.

    Args:
        category: Event category (wildfires, severeStorms, volcanoes, etc.) - optional
        status: Event status - 'open', 'closed', or 'all' (default: 'open')
        limit: Maximum number of events to return (optional)
        days: Only show events within last N days (optional)
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
async def get_event_categories(nasa_api_key: str) -> List[Dict[str, Any]]:
    """
    Get available event categories from EONET.
    Note: EONET API doesn't require API key but we keep parameter for consistency.
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
    mcp.run(transport="sse", port=8000)
