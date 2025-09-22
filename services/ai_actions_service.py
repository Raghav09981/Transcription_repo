import google.generativeai as genai
import os
from datetime import datetime, timedelta


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")


def analyze_for_meeting_action(notes: str) -> dict:
    """Use Gemini to decide if notes imply scheduling a meeting and extract details."""
    if not notes or not notes.strip():
        return {"should_schedule": False}

    prompt = (
        "You are an assistant that extracts meeting scheduling intents from text. "
        "Given the meeting transcript/notes below, determine if there is an actionable that "
        "requires scheduling a follow-up meeting. If yes, extract: title, short description, "
        "a suggested ISO8601 start time in the near future (using user's locale assumption), "
        "and a duration in minutes. Return a strict JSON with keys: "
        "should_schedule (boolean), title (string), description (string), "
        "start_time_iso (ISO8601 string), duration_minutes (int). If insufficient info, set should_schedule=false.\n\n"
        f"TEXT:\n{notes}"
    )

    response = model.generate_content(prompt)
    text = response.text if hasattr(response, "text") else str(response)

    # naive parsing: try to find a JSON block; if fails, fallback
    import json, re
    json_match = re.search(r"\{[\s\S]*\}", text)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            # Basic defaults/validation
            data["should_schedule"] = bool(data.get("should_schedule", False))
            if data["should_schedule"]:
                if not data.get("start_time_iso"):
                    # Default to 24h from now
                    data["start_time_iso"] = (datetime.utcnow() + timedelta(days=1)).isoformat() + "Z"
                if not data.get("duration_minutes"):
                    data["duration_minutes"] = 30
            return data
        except Exception:
            pass

    return {"should_schedule": False}


