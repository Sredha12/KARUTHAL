"""
Seed definitions and constants for Kerala districts, sample fictional panchayats,
and validated category classifications.

NOTE ON PANCHAYATS:
The panchayat records listed here are strictly SAMPLE / FICTIONAL administrative divisions
provided for prototype testing and evaluation. They do NOT represent an official gazetted
government dataset.
"""

KERALA_DISTRICTS = [
    {"name": "Alappuzha", "code": "ALP"},
    {"name": "Ernakulam", "code": "EKM"},
    {"name": "Idukki", "code": "IDK"},
    {"name": "Kannur", "code": "KNR"},
    {"name": "Kasaragod", "code": "KSD"},
    {"name": "Kollam", "code": "KLM"},
    {"name": "Kottayam", "code": "KTM"},
    {"name": "Kozhikode", "code": "KKD"},
    {"name": "Malappuram", "code": "MLP"},
    {"name": "Palakkad", "code": "PKD"},
    {"name": "Pathanamthitta", "code": "PTA"},
    {"name": "Thiruvananthapuram", "code": "TVM"},
    {"name": "Thrissur", "code": "TSR"},
    {"name": "Wayanad", "code": "WYD"},
]

SAMPLE_PANCHAYATS_BY_DISTRICT = {
    "Alappuzha": ["Ambalappuzha", "Champakulam", "Cherthala", "Kayamkulam", "Mavelikkara"],
    "Ernakulam": ["Aluva", "Angamaly", "Kothamangalam", "Muvattupuzha", "North Paravur"],
    "Idukki": ["Adimali", "Devikulam", "Nedumkandam", "Peermade", "Thodupuzha"],
    "Kannur": ["Iritty", "Payyanur", "Taliparamba", "Thalassery", "Mattannur"],
    "Kasaragod": ["Hosdurg", "Kanhangad", "Manjeshwaram", "Nileshwar", "Uppala"],
    "Kollam": ["Anchal", "Chavara", "Karunagappally", "Kottarakkara", "Sasthamkotta"],
    "Kottayam": ["Changanassery", "Ettumanoor", "Kanjirappally", "Pala", "Vaikom"],
    "Kozhikode": ["Balussery", "Koyilandy", "Kunnamangalam", "Perambra", "Vadakara"],
    "Malappuram": ["Edappal", "Kondotty", "Manjeri", "Nilambur", "Tirur"],
    "Palakkad": ["Alathur", "Chittur", "Mannarkkad", "Ottapalam", "Pattambi"],
    "Pathanamthitta": ["Adoor", "Konni", "Kozhencherry", "Mallappally", "Ranni"],
    "Thiruvananthapuram": ["Chirayinkeezhu", "Kattakada", "Nedumangad", "Neyyattinkara", "Varkala"],
    "Thrissur": ["Chalakkudy", "Chavakkad", "Irinjalakuda", "Kodungallur", "Wadakkanchery"],
    "Wayanad": ["Kalpetta", "Mananthavady", "Meppadi", "Sulthan Bathery", "Vythiri"],
}

ALLOWED_CATEGORIES = [
    "Physical abuse",
    "Sexual abuse",
    "Emotional abuse",
    "Neglect",
    "Child labour",
    "Child marriage",
    "Trafficking",
    "Abandonment",
    "Other",
]

ALLOWED_STATUSES = [
    "Submitted",
    "Under Review",
    "Assigned",
    "Visit Recorded",
    "Referred",
    "Solved",
]

ALLOWED_VISIT_OUTCOMES = [
    "Safe with family",
    "Needs support services",
    "Further assessment required",
    "Child relocated to safe care",
    "No concern detected",
]

ALLOWED_REFERRAL_STATUSES = [
    "New",
    "Pending review",
    "Under review",
    "Follow-up due",
    "Closed",
]

ALLOWED_EMERGENCY_STATUSES = [
    "Active",
    "Acknowledged",
    "Resolved",
]
