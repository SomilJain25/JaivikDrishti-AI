# ============================================================
# KRISHIBOT — topic_filter.py
# Checks if user question is agriculture-related
# ============================================================

# 80+ agriculture keywords including Hindi words
AGRI_KEYWORDS = [
    # General farming
    "crop", "crops", "farm", "farming", "farmer", "field", "agriculture", "agri",
    "harvest", "sow", "sowing", "transplant", "yield", "produce", "cultivate",

    # Soil
    "soil", "compost", "manure", "fertilizer", "fertilizers", "npk", "nitrogen",
    "phosphorus", "potassium", "ph", "micronutrient", "macronutrient", "loam",
    "clay", "sandy", "humus", "organic matter",

    # Plants & seeds
    "plant", "plants", "seed", "seeds", "seedling", "germination", "root",
    "leaf", "stem", "flower", "pollination", "grafting", "pruning", "cutting",

    # Water
    "irrigation", "drip", "sprinkler", "flood irrigation", "furrow", "water stress",
    "drought", "rainfall", "monsoon", "humidity", "moisture",

    # Crops (Indian + global)
    "wheat", "rice", "paddy", "maize", "corn", "cotton", "sugarcane", "soybean",
    "potato", "tomato", "onion", "garlic", "ginger", "turmeric", "chilli",
    "mustard", "groundnut", "peanut", "sunflower", "mango", "banana", "orange",
    "grapes", "pomegranate", "guava", "papaya", "chickpea", "lentil", "dal",
    "jowar", "bajra", "ragi", "barley", "pea", "moong", "urad",

    # Seasons
    "kharif", "rabi", "zaid", "summer crop", "winter crop",

    # Pests & diseases
    "pest", "pests", "insect", "aphid", "locust", "whitefly", "stem borer",
    "armyworm", "nematode", "thrips", "mite", "weevil", "disease", "blight",
    "rust", "mildew", "wilt", "rot", "fungus", "bacteria", "virus",

    # Chemicals & bio
    "pesticide", "herbicide", "fungicide", "insecticide", "neem", "bio pesticide",
    "biofertilizer", "trichoderma", "rhizobium", "panchagavya",

    # Equipment
    "tractor", "plough", "plow", "rotavator", "combine", "thresher", "sprayer",
    "cultivator", "harrow", "seed drill",

    # Horticulture / allied
    "horticulture", "floriculture", "sericulture", "apiculture", "bee", "honey",
    "pisciculture", "aquaculture", "hydroponics", "greenhouse", "polyhouse",
    "livestock", "cattle", "dairy", "poultry", "goat", "sheep", "buffalo",

    # Storage & market
    "storage", "silo", "cold storage", "mandi", "market", "msp",
    "minimum support price", "enam", "agri market",

    # Government schemes
    "pm kisan", "pm-kisan", "fasal bima", "soil health card", "nabard", "kvk",
    "kisan credit", "kcc", "pmksy", "pkvy", "organic farming", "subsidy",

    # Hindi keywords
    "खेती", "फसल", "मिट्टी", "बीज", "सिंचाई", "खाद", "कीट",
    "बीमारी", "उर्वरक", "बुवाई", "किसान", "फसल बीमा", "मंडी",
]


def is_agriculture_question(text: str) -> bool:
    """
    Returns True if the question is agriculture-related.
    Checks against 80+ keywords including Hindi terms.
    """
    lower = text.lower()
    return any(keyword.lower() in lower for keyword in AGRI_KEYWORDS)