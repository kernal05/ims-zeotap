from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.MONGODB_URL)
mongo_db = client["ims_raw"]

raw_alerts_collection = mongo_db["raw_alerts"]
incident_logs_collection = mongo_db["incident_logs"]

def log_raw_alert(alert_data: dict) -> str:
    result = raw_alerts_collection.insert_one(alert_data)
    return str(result.inserted_id)

def log_incident_event(incident_id: str, event: str, data: dict):
    incident_logs_collection.insert_one({
        "incident_id": incident_id,
        "event": event,
        "data": data
    })
