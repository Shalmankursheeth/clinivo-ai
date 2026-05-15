from datetime import datetime


def get_greeting(clinic_state: str = "open") -> str:
    if clinic_state == "closed":
        return "Clinic ippo close aagiyirukku. Nalai morning 9 manikku call pannunga sir."

    hour = datetime.now().hour
    if hour < 12:
        return "Good morning. Clinic ku call pannirukinga. Sollunga sir."
    if hour < 17:
        return "Vanakkam. Clinic ku call pannirukinga. Sollunga sir."
    return "Good evening. Clinic ku call pannirukinga. Sollunga sir."