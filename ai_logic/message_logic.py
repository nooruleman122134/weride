def get_dynamic_voice_message(ride):
    name = ride.get("name", "Dear rider")
    status = ride.get("status")
    complaint = ride.get("complaint")

    print(f"💡 DEBUG → Status: {status} | Complaint: {complaint}")

    if complaint == "safety":
        return f"{name}, we’ve received a safety concern for your ride. Please stay calm. Help is on the way."

    elif status == "arrived":
        return f"{name}, your WeRide driver has arrived at your location. Please come to the pickup point."

    elif status == "delayed":
        return f"{name}, your driver is running a little late. Please wait a few more minutes."

    elif status == "cancelled":
        return f"{name}, your ride has been cancelled. You can book again anytime through WeRide."

    else:
        return f"{name}, your ride is on the way. Please stay ready."
