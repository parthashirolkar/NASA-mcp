import os
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
from typing import List, Dict, Any


_ = load_dotenv()

mcp = FastMCP("NASA MCP")


@mcp.tool()
async def get_picture_of_the_day() -> ImageContent:
    """Get the NASA Picture of the Day."""
    NASA_API_KEY = os.getenv("NASA_API_KEY")

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
async def get_neo_asteroids(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Retrieve Near Earth Objects between start_date and end_date and return a list of records (dicts).

    Each record (one per close-approach event) contains useful features (id, name, observed_date, etc.).
    Returns a JSON-serializable list of dicts suitable for MCP/LM Studio.
    """
    NASA_API_KEY = os.getenv("NASA_API_KEY")
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


def _safe_float(v):
    try:
        return float(v) if v is not None else None
    except Exception:
        return None


if __name__ == "__main__":
    mcp.run(transport="stdio")
