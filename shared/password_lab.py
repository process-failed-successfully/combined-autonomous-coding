import secrets
import string
import math
import hashlib
import base64
import os
import sys
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional

try:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    from cryptography.hazmat.backends import default_backend
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

class PasswordLabManager:
    """
    Manages Password Lab operations: generation, strength checking, and hashing.
    """

    # A short list of common, distinct words for passphrase generation.
    # In a full implementation, this could be the EFF short wordlist.
    DEFAULT_WORDLIST = [
    "abacus", "abdomen", "ability", "abnormal", "above", "absence", "absent",
    "absolute", "abstract", "abundance", "abuse", "academic", "academy", "accent",
    "accept", "access", "accident", "accompany", "accomplish", "according",
    "account", "accuracy", "accurate", "accuse", "achieve", "acid", "acquire",
    "across", "action", "active", "activity", "actor", "actress", "actual",
    "adapt", "add", "addition", "address", "adjust", "admin", "admit", "adopt",
    "adult", "advance", "advantage", "adventure", "advice", "advise", "affair",
    "affect", "afford", "afraid", "after", "afternoon", "again", "against",
    "agency", "agent", "agree", "agreement", "ahead", "aim", "air", "aircraft",
    "airline", "airport", "alarm", "album", "alcohol", "alive", "allow", "almost",
    "alone", "along", "already", "also", "alter", "always", "amazed", "amazing",
    "among", "amount", "analysis", "analyst", "analyze", "ancient", "anger",
    "angle", "angry", "animal", "ankle", "announce", "annual", "another", "answer",
    "anticipate", "anxiety", "anxious", "anybody", "anymore", "anyone", "anything",
    "anyway", "anywhere", "apart", "apartment", "apparent", "appeal", "appear",
    "apple", "apply", "appoint", "approach", "approve", "area", "argue",
    "argument", "arise", "arm", "army", "around", "arrange", "arrest", "arrive",
    "arrow", "art", "article", "artist", "aside", "ask", "asleep", "aspect",
    "assault", "assert", "assess", "asset", "assign", "assist", "assume",
    "assure", "athlete", "athletic", "atm", "atom", "attach", "attack",
    "attempt", "attend", "attention", "attitude", "attract", "attribute",
    "auction", "audience", "audio", "audit", "aunt", "author", "authority",
    "auto", "available", "average", "avoid", "award", "aware", "awareness",
    "away", "awesome", "awful", "awkward", "baby", "back", "background",
    "backpack", "backward", "bacon", "bad", "badly", "bag", "bake", "balance",
    "ball", "balloon", "ballot", "ban", "banana", "band", "bank", "bar",
    "barely", "barrel", "barrier", "base", "baseball", "basic", "basically",
    "basis", "basket", "basketball", "bat", "batch", "bath", "bathroom",
    "battery", "battle", "bay", "beach", "bean", "bear", "beat", "beautiful",
    "beauty", "because", "become", "bed", "bedroom", "bee", "beef", "beer",
    "before", "begin", "beginning", "behave", "behavior", "behind", "being",
    "belief", "believe", "bell", "belong", "below", "belt", "bench", "bend",
    "beneath", "benefit", "beside", "besides", "best", "bet", "better", "between",
    "beyond", "bicycle", "bid", "big", "bike", "bill", "billion", "bind",
    "biology", "bird", "birth", "birthday", "bit", "bite", "bitter", "black",
    "blade", "blame", "blank", "blanket", "blast", "blend", "blind", "block",
    "blood", "blow", "blue", "board", "boat", "body", "boil", "bomb", "bond",
    "bone", "book", "boom", "boot", "border", "born", "borrow", "boss", "both",
    "bother", "bottle", "bottom", "boundary", "bowl", "box", "boy", "boyfriend",
    "brain", "branch", "brand", "bread", "break", "breakfast", "breast", "breath",
    "breathe", "brick", "bridge", "brief", "briefly", "bright", "brilliant",
    "bring", "broad", "broken", "brother", "brown", "brush", "buck", "budget",
    "build", "building", "bullet", "bunch", "burden", "burn", "bury", "bus",
    "business", "busy", "but", "butter", "button", "buy", "buyer", "by", "cabin",
    "cabinet", "cable", "cake", "calculate", "call", "camera", "camp", "campaign",
    "campus", "can", "cancel", "cancer", "candidate", "candle", "candy", "cap",
    "capable", "capacity", "capital", "captain", "capture", "car", "carbon",
    "card", "care", "career", "careful", "carefully", "cargo", "carpet", "carrier",
    "carry", "cart", "case", "cash", "cast", "cat", "catch", "category", "cause",
    "ceiling", "celebrate", "cell", "center", "central", "century", "ceo",
    "ceremony", "certain", "certainly", "chain", "chair", "chairman", "challenge",
    "chamber", "champion", "championship", "chance", "change", "changing",
    "channel", "chapter", "character", "charge", "charity", "charm", "chart",
    "chase", "cheap", "check", "cheek", "cheese", "chef", "chemical", "chest",
    "chicken", "chief", "child", "childhood", "chill", "chin", "chip",
    "chocolate", "choice", "cholesterol", "choose", "chop", "church", "circle",
    "citizen", "city", "civil", "civilian", "claim", "class", "classic",
    "classroom", "clean", "clear", "clearly", "clerk", "click", "client",
    "cliff", "climate", "climb", "clinic", "clinical", "clip", "clock", "close",
    "closely", "closer", "clothes", "clothing", "cloud", "club", "clue",
    "cluster", "coach", "coal", "coalition", "coast", "coat", "code", "coffee",
    "cognitive", "cold", "collapse", "colleague", "collect", "collection",
    "college", "color", "column", "combine", "come", "comedy", "comfort",
    "comfortable", "command", "commander", "comment", "commercial", "commission",
    "commit", "commitment", "committee", "common", "commonly", "communicate",
    "communication", "community", "company", "compare", "comparison", "compete",
    "competition", "competitive", "competitor", "complain", "complaint",
    "complete", "completely", "complex", "complicated", "component", "compose",
    "composition", "comprehensive", "computer", "concentrate", "concentration",
    "concept", "concern", "concerned", "concert", "conclude", "conclusion",
    "concrete", "condition", "conduct", "conference", "confidence", "confident",
    "confirm", "conflict", "confront", "confusion", "congress", "congressional",
    "connect", "connection", "consciousness", "consensus", "consequence",
    "conservative", "consider", "considerable", "consideration", "consist",
    "consistent", "constant", "constantly", "constitute", "constitutional",
    "construct", "construction", "consultant", "consume", "consumer",
    "consumption", "contact", "contain", "container", "contemporary", "content",
    "contest", "context", "continue", "continued", "contract", "contrast",
    "contribute", "contribution", "control", "controversial", "controversy",
    "convention", "conventional", "conversation", "convert", "conviction",
    "convince", "cook", "cookie", "cooking", "cool", "cooperation", "cop", "cope",
    "copy", "core", "corn", "corner", "corporate", "corporation", "correct",
    "correspondent", "cost", "cotton", "couch", "could", "council", "counselor",
    "count", "counter", "country", "county", "couple", "courage", "course",
    "court", "cousin", "cover", "coverage", "cow", "crack", "craft", "crash",
    "crazy", "cream", "create", "creation", "creative", "creature", "credit",
    "crew", "crime", "criminal", "crisis", "criteria", "critic", "critical",
    "criticism", "criticize", "crop", "cross", "crowd", "crucial", "cry",
    "cultural", "culture", "cup", "curious", "current", "currently", "curriculum",
    "custom", "customer", "cut", "cycle", "dad", "daily", "damage", "dance",
    "danger", "dangerous", "dare", "dark", "darkness", "data", "date", "daughter",
    "day", "dead", "deal", "dealer", "dear", "death", "debate", "debt", "decade",
    "decide", "decision", "deck", "declare", "decline", "decrease", "deep",
    "deeply", "deer", "defeat", "defend", "defendant", "defense", "defensive",
    "deficit", "define", "definitely", "definition", "degree", "delay", "deliver",
    "delivery", "demand", "democracy", "democrat", "democratic", "demonstrate",
    "demonstration", "deny", "department", "depend", "dependent", "depending",
    "depict", "depression", "depth", "deputy", "derive", "describe", "description",
    "desert", "deserve", "design", "designer", "desire", "desk", "desperate",
    "despite", "destroy", "destruction", "detail", "detailed", "detect",
    "determine", "develop", "developing", "development", "device", "devote",
    "dialogue", "diet", "differ", "difference", "different", "differently",
    "difficult", "difficulty", "dig", "digital", "dimension", "dining", "dinner",
    "direct", "direction", "directly", "director", "dirt", "dirty", "disability",
    "disagree", "disappear", "disaster", "discipline", "discourse", "discover",
    "discovery", "discrimination", "discuss", "discussion", "disease", "dish",
    "dismiss", "disorder", "display", "dispute", "distance", "distant", "distinct",
    "distinction", "distinguish", "distribute", "distribution", "district",
    "diverse", "diversity", "divide", "division", "divorce", "dna", "doctor",
    "document", "dog", "domestic", "dominant", "dominate", "door", "double",
    "doubt", "down", "downtown", "dozen", "draft", "drag", "drama", "dramatic",
    "dramatically", "draw", "drawing", "dream", "dress", "drink", "drive",
    "driver", "drop", "drug", "dry", "due", "during", "dust", "duty", "each",
    "eager", "ear", "early", "earn", "earnings", "earth", "ease", "easily", "east",
    "eastern", "easy", "eat", "economic", "economics", "economist", "economy",
    "edge", "edition", "editor", "educate", "education", "educational", "educator",
    "effect", "effective", "effectively", "efficiency", "efficient", "effort",
    "egg", "eight", "either", "elder", "elderly", "elect", "election", "electric",
    "electricity", "electronic", "element", "elephant", "eleven", "else",
    "elsewhere", "email", "embrace", "emerge", "emergency", "emission", "emotion",
    "emotional", "emphasis", "emphasize", "employ", "employee", "employer",
    "employment", "empty", "enable", "encounter", "encourage", "end", "enemy",
    "energy", "enforcement", "engage", "engine", "engineer", "engineering",
    "english", "enhance", "enjoy", "enormous", "enough", "ensure", "enter",
    "enterprise", "entertainment", "entire", "entirely", "entrance", "entry",
    "environment", "environmental", "episode", "equal", "equally", "equipment",
    "era", "error", "escape", "especially", "essay", "essential", "essentially",
    "establish", "establishment", "estate", "estimate", "etc", "ethics", "ethnic",
    "european", "evaluate", "evaluation", "even", "evening", "event", "eventually",
    "ever", "every", "everybody", "everyday", "everyone", "everything",
    "everywhere", "evidence", "evolution", "evolve", "exact", "exactly",
    "examination", "examine", "example", "exceed", "excellent", "except",
    "exception", "exchange", "exciting", "executive", "exercise", "exhibit",
    "exhibition", "exist", "existence", "existing", "expand", "expansion",
    "expect", "expectation", "expense", "expensive", "experience", "experiment",
    "expert", "explain", "explanation", "explode", "explore", "explosion",
    "expose", "exposure", "express", "expression", "extend", "extension",
    "extensive", "extent", "external", "extra", "extraordinary", "extreme",
    "extremely", "eye", "fabric", "face", "facility", "fact", "factor", "factory",
    "faculty", "fade", "fail", "failure", "fair", "fairly", "faith", "fall",
    "false", "familiar", "family", "famous", "fan", "fantasy", "far", "farm",
    "farmer", "fashion", "fast", "fat", "fate", "father", "fault", "favor",
    "favorite", "fear", "feature", "federal", "fee", "feed", "feel", "feeling",
    "fellow", "female", "fence", "few", "fewer", "fiber", "fiction", "field",
    "fifteen", "fifth", "fifty", "fight", "fighter", "fighting", "figure", "file",
    "fill", "film", "final", "finally", "finance", "financial", "find", "finding",
    "fine", "finger", "finish", "fire", "firm", "first", "fish", "fishing", "fit",
    "fitness", "five", "fix", "flag", "flame", "flat", "flavor", "flee", "flesh",
    "flight", "float", "floor", "flow", "flower", "fly", "focus", "folk", "follow",
    "following", "food", "foot", "football", "for", "force", "foreign", "forest",
    "forever", "forget", "form", "formal", "formation", "former", "formula",
    "forth", "fortune", "forward", "found", "foundation", "founder", "four",
    "fourth", "frame", "framework", "free", "freedom", "freeze", "french",
    "frequency", "frequent", "frequently", "fresh", "friend", "friendly",
    "friendship", "from", "front", "fruit", "frustration", "fuel", "full", "fully",
    "fun", "function", "fund", "fundamental", "funding", "funeral", "funny",
    "furniture", "furthermore", "future", "gain", "galaxy", "gallery", "game",
    "gang", "gap", "garage", "garden", "garlic", "gas", "gate", "gather", "gay",
    "gaze", "gear", "gender", "gene", "general", "generally", "generate",
    "generation", "genetic", "gentleman", "gently", "german", "gesture", "get",
    "ghost", "giant", "gift", "gifted", "girl", "girlfriend", "give", "given",
    "glad", "glance", "glass", "global", "glove", "go", "goal", "god", "gold",
    "golden", "golf", "good", "government", "governor", "grab", "grade",
    "gradually", "graduate", "grain", "grand", "grandfather", "grandmother",
    "grant", "grass", "grave", "gray", "great", "greatest", "green", "grocery",
    "ground", "group", "grow", "growing", "growth", "guarantee", "guard", "guess",
    "guest", "guide", "guideline", "guilty", "gun", "guy", "habit", "habitat",
    "hair", "half", "hall", "hand", "handful", "handle", "hang", "happen",
    "happy", "hard", "hardly", "hat", "hate", "have", "he", "head", "headline",
    "headquarters", "health", "healthy", "hear", "hearing", "heart", "heat",
    "heaven", "heavily", "heavy", "heel", "height", "helicopter", "hell", "hello",
    "help", "helpful", "her", "herb", "here", "heritage", "hero", "herself",
    "hide", "high", "highlight", "highly", "highway", "hill", "him", "himself",
    "hip", "hire", "his", "historian", "historic", "historical", "history", "hit",
    "hold", "hole", "holiday", "holy", "home", "homeless", "honest", "honey",
    "honor", "hope", "horizon", "horror", "horse", "hospital", "host", "hot",
    "hotel", "hour", "house", "household", "housing", "how", "however", "huge",
    "human", "humor", "hundred", "hungry", "hunter", "hunting", "hurt", "husband",
    "hypothesis", "I", "ice", "idea", "ideal", "identification", "identify",
    "identity", "ie", "if", "ignore", "ill", "illegal", "illness", "illustrate",
    "image", "imagination", "imagine", "immediate", "immediately", "immigrant",
    "immigration", "impact", "implement", "implication", "imply", "importance",
    "important", "impose", "impossible", "impress", "impression", "impressive",
    "improve", "improvement", "in", "incentive", "incident", "include",
    "including", "income", "incorporate", "increase", "increased", "increasing",
    "increasingly", "incredible", "indeed", "independence", "independent", "index",
    "indian", "indicate", "indication", "individual", "industrial", "industry",
    "infant", "infection", "inflation", "influence", "inform", "information",
    "ingredient", "initial", "initially", "initiative", "injury", "inner",
    "innocent", "inquiry", "inside", "insight", "insist", "inspire", "install",
    "instance", "instead", "institution", "institutional", "instruction",
    "instructor", "instrument", "insurance", "intellectual", "intelligence",
    "intend", "intense", "intensity", "intention", "interaction", "interest",
    "interested", "interesting", "internal", "international", "internet",
    "interpret", "interpretation", "intervention", "interview", "into",
    "introduce", "introduction", "invasion", "invest", "investigate",
    "investigation", "investigator", "investment", "investor", "invite", "involve",
    "involved", "involvement", "iraqi", "irish", "iron", "islamic", "island",
    "israeli", "issue", "it", "italian", "item", "its", "itself", "jacket",
    "jail", "japanese", "jet", "jew", "jewish", "job", "join", "joint", "joke",
    "journal", "journalist", "journey", "joy", "judge", "judgment", "juice",
    "jump", "junior", "jury", "just", "justice", "justify", "keep", "key", "kick",
    "kid", "kill", "killer", "killing", "kind", "king", "kiss", "kitchen", "knee",
    "knife", "knock", "know", "knowledge", "lab", "label", "labor", "laboratory",
    "lack", "lady", "lake", "land", "landscape", "language", "lap", "large",
    "largely", "last", "late", "later", "latin", "latter", "laugh", "launch",
    "law", "lawn", "lawsuit", "lawyer", "lay", "layer", "lead", "leader",
    "leadership", "leading", "leaf", "league", "lean", "learn", "learning",
    "least", "leather", "leave", "left", "leg", "legacy", "legal", "legend",
    "legislation", "legitimate", "lemon", "length", "less", "lesson", "let",
    "letter", "level", "liberal", "library", "license", "lie", "life",
    "lifestyle", "lifetime", "lift", "light", "like", "likely", "limit",
    "limitation", "limited", "line", "link", "lip", "list", "listen", "literally",
    "literary", "literature", "little", "live", "living", "load", "loan", "local",
    "locate", "location", "lock", "long", "look", "loose", "lose", "loss", "lost",
    "lot", "lots", "loud", "love", "lovely", "lover", "low", "lower", "luck",
    "lucky", "lunch", "lung", "machine", "mad", "magazine", "mail", "main",
    "mainly", "maintain", "maintenance", "major", "majority", "make", "maker",
    "makeup", "male", "mall", "man", "manage", "management", "manager", "manner",
    "manufacturer", "manufacturing", "many", "map", "margin", "mark", "market",
    "marketing", "marriage", "married", "marry", "mask", "mass", "massive",
    "master", "match", "material", "math", "matter", "may", "maybe", "mayor",
    "me", "meal", "mean", "meaning", "meanwhile", "measure", "measurement",
    "meat", "mechanism", "media", "medical", "medication", "medicine", "medium",
    "meet", "meeting", "member", "membership", "memory", "mental", "mention",
    "menu", "mere", "merely", "mess", "message", "metal", "meter", "method",
    "mexican", "middle", "might", "military", "milk", "million", "mind", "mine",
    "minister", "minor", "minority", "minute", "miracle", "mirror", "miss",
    "missile", "mission", "mistake", "mix", "mixture", "mode", "model",
    "moderate", "modern", "modest", "mom", "moment", "money", "monitor", "month",
    "mood", "moon", "moral", "more", "moreover", "morning", "mortgage", "most",
    "mostly", "mother", "motion", "motivation", "motor", "mount", "mountain",
    "mouse", "mouth", "move", "movement", "movie", "mr", "mrs", "ms", "much",
    "multiple", "murder", "muscle", "museum", "music", "musical", "musician",
    "muslim", "must", "mutter", "mutual", "my", "myself", "mystery", "myth",
    "naked", "name", "narrative", "narrow", "nation", "national", "native",
    "natural", "naturally", "nature", "near", "nearby", "nearly", "necessarily",
    "necessary", "neck", "need", "negative", "negotiate", "negotiation",
    "neighbor", "neighborhood", "neither", "nerve", "nervous", "net", "network",
    "never", "nevertheless", "new", "newly", "news", "newspaper", "next", "nice",
    "night", "nine", "no", "nobody", "nod", "noise", "nomination", "none",
    "nonetheless", "nor", "normal", "normally", "north", "northern", "nose",
    "not", "note", "nothing", "notice", "notion", "novel", "now", "nowhere",
    "nuclear", "number", "numerous", "nurse", "nut", "object", "objective",
    "obligation", "observation", "observe", "observer", "obtain", "obvious",
    "obviously", "occasion", "occasionally", "occupation", "occupy", "occur",
    "ocean", "odd", "odds", "of", "off", "offense", "offensive", "offer",
    "office", "officer", "official", "often", "oh", "oil", "ok", "okay", "old",
    "olympic", "on", "once", "one", "ongoing", "onion", "online", "only",
    "onto", "open", "opening", "operate", "operating", "operation", "operator",
    "opinion", "opponent", "opportunity", "oppose", "opposite", "opposition",
    "option", "or", "orange", "order", "ordinary", "organic", "organization",
    "organize", "orientation", "origin", "original", "originally", "other",
    "others", "otherwise", "ought", "our", "ourselves", "out", "outcome",
    "outside", "oven", "over", "overall", "overcome", "overlook", "owe", "own",
    "owner", "pace", "pack", "package", "page", "pain", "painful", "paint",
    "painter", "painting", "pair", "pale", "palestinian", "palm", "pan", "panel",
    "pant", "paper", "parent", "park", "parking", "part", "participant",
    "participate", "participation", "particular", "particularly", "partly",
    "partner", "partnership", "party", "pass", "passage", "passenger", "passion",
    "past", "patch", "path", "patient", "pattern", "pause", "pay", "payment",
    "pc", "peace", "peak", "peer", "penalty", "people", "pepper", "per",
    "perceive", "percentage", "perception", "perfect", "perfectly", "perform",
    "performance", "perhaps", "period", "permanent", "permission", "permit",
    "person", "personal", "personality", "personally", "personnel", "perspective",
    "persuade", "pet", "phase", "phenomenon", "philosophy", "phone", "photo",
    "photograph", "photographer", "phrase", "physical", "physically", "physician",
    "piano", "pick", "picture", "pie", "piece", "pig", "pile", "pilot", "pine",
    "pink", "pipe", "pitch", "place", "plan", "plane", "planet", "planning",
    "plant", "plastic", "plate", "platform", "play", "player", "please",
    "pleasure", "plenty", "plot", "plus", "pm", "pocket", "poem", "poet",
    "poetry", "point", "pole", "police", "policy", "political", "politically",
    "politician", "politics", "poll", "pollution", "pool", "poor", "pop",
    "popular", "population", "porch", "port", "portion", "portrait", "portray",
    "pose", "position", "positive", "possess", "possibility", "possible",
    "possibly", "post", "pot", "potato", "potential", "potentially", "pound",
    "pour", "poverty", "powder", "power", "powerful", "practical", "practice",
    "pray", "prayer", "precisely", "predict", "prefer", "preference", "pregnancy",
    "pregnant", "preparation", "prepare", "prescription", "presence", "present",
    "presentation", "preserve", "president", "presidential", "press", "pressure",
    "pretend", "pretty", "prevent", "previous", "previously", "price", "pride",
    "priest", "primarily", "primary", "prime", "principal", "principle", "print",
    "prior", "priority", "prison", "prisoner", "privacy", "private", "probably",
    "problem", "procedure", "proceed", "process", "produce", "producer",
    "product", "production", "profession", "professional", "professor", "profile",
    "profit", "program", "progress", "project", "prominent", "promise",
    "promote", "prompt", "proof", "proper", "properly", "property", "proportion",
    "proposal", "propose", "proposed", "prosecutor", "prospect", "protect",
    "protection", "protein", "protest", "proud", "prove", "provide", "provider",
    "province", "provision", "psychological", "psychologist", "psychology",
    "public", "publication", "publicly", "publish", "publisher", "pull",
    "punishment", "purchase", "pure", "purpose", "pursue", "push", "put",
    "qualify", "quality", "quarter", "quarterback", "question", "quick",
    "quickly", "quiet", "quietly", "quit", "quite", "quote", "race", "racial",
    "radical", "radio", "rail", "rain", "raise", "range", "rank", "rapid",
    "rapidly", "rare", "rarely", "rate", "rather", "rating", "ratio", "raw",
    "reach", "react", "reaction", "read", "reader", "reading", "ready", "real",
    "reality", "realize", "really", "reason", "reasonable", "recall", "receive",
    "recent", "recently", "recipe", "recognition", "recognize", "recommend",
    "recommendation", "record", "recording", "recover", "recovery", "recruit",
    "red", "reduce", "reduction", "refer", "reference", "reflect", "reflection",
    "reform", "refugee", "refuse", "regard", "regarding", "regardless", "regime",
    "region", "regional", "register", "regular", "regularly", "regulate",
    "regulation", "reinforce", "reject", "relate", "relation", "relationship",
    "relative", "relatively", "relax", "release", "relevant", "relief",
    "religion", "religious", "rely", "remain", "remaining", "remarkable",
    "remember", "remind", "remote", "remove", "repeat", "repeatedly", "replace",
    "reply", "report", "reporter", "represent", "representation",
    "representative", "republican", "reputation", "request", "require",
    "requirement", "research", "researcher", "resemble", "reservation", "resident",
    "resist", "resistance", "resolution", "resolve", "resort", "resource",
    "respect", "respond", "respondent", "response", "responsibility",
    "responsible", "rest", "restaurant", "restore", "restriction", "result",
    "retain", "retire", "retirement", "return", "reveal", "revenue", "review",
    "revolution", "rhythm", "rice", "rich", "rid", "ride", "rifle", "right",
    "ring", "rise", "risk", "river", "road", "rock", "role", "roll", "romantic",
    "roof", "room", "root", "rope", "rose", "rough", "roughly", "round", "route",
    "routine", "row", "rub", "rule", "run", "running", "rural", "rush", "russian",
    "sacred", "sad", "safe", "safety", "sake", "salad", "salary", "sale", "sales",
    "salt", "same", "sample", "sanction", "sand", "satellite", "satisfaction",
    "satisfy", "sauce", "save", "saving", "say", "scale", "scandal", "scared",
    "scenario", "scene", "schedule", "scheme", "scholar", "scholarship", "school",
    "science", "scientific", "scientist", "scope", "score", "scream", "screen",
    "script", "sea", "search", "season", "seat", "second", "secret", "secretary",
    "section", "sector", "secure", "security", "see", "seed", "seek", "seem",
    "segment", "seize", "select", "selection", "self", "sell", "senate", "senator",
    "send", "senior", "sense", "sensitive", "sentence", "separate", "sequence",
    "series", "serious", "seriously", "serve", "service", "session", "set",
    "setting", "settle", "settlement", "seven", "several", "severe", "sex",
    "sexual", "shade", "shadow", "shake", "shall", "shape", "share", "sharp",
    "she", "sheet", "shelf", "shell", "shelter", "shift", "shine", "ship",
    "shirt", "shit", "shock", "shoe", "shoot", "shooting", "shop", "shopping",
    "shore", "short", "shortly", "shot", "should", "shoulder", "shout", "show",
    "shower", "shrug", "shut", "sick", "side", "sigh", "sight", "sign", "signal",
    "significance", "significant", "significantly", "silence", "silent", "silver",
    "similar", "similarly", "simple", "simply", "sin", "since", "sing", "singer",
    "single", "sink", "sir", "sister", "sit", "site", "situation", "six", "size",
    "ski", "skill", "skin", "sky", "slave", "sleep", "slice", "slide", "slight",
    "slightly", "slip", "slow", "slowly", "small", "smart", "smell", "smile",
    "smoke", "smooth", "snap", "snow", "so", "so-called", "soccer", "social",
    "society", "soft", "software", "soil", "solar", "soldier", "solid", "solution",
    "solve", "some", "somebody", "somehow", "someone", "something", "sometimes",
    "somewhat", "somewhere", "son", "song", "soon", "sophisticated", "sorry",
    "sort", "soul", "sound", "soup", "source", "south", "southern", "soviet",
    "space", "spanish", "speak", "speaker", "special", "specialist", "species",
    "specific", "specifically", "speech", "speed", "spend", "spending", "spin",
    "spirit", "spiritual", "split", "spokesman", "sport", "spot", "spread",
    "spring", "square", "squeeze", "stability", "stable", "staff", "stage",
    "stair", "stake", "stand", "standard", "standing", "star", "stare", "start",
    "state", "statement", "station", "statistics", "status", "stay", "steady",
    "steal", "steel", "step", "stick", "still", "stir", "stock", "stomach",
    "stone", "stop", "storage", "store", "storm", "story", "straight", "strange",
    "stranger", "strategic", "strategy", "stream", "street", "strength",
    "strengthen", "stress", "stretch", "strike", "string", "strip", "stroke",
    "strong", "strongly", "structure", "struggle", "student", "studio", "study",
    "stuff", "stupid", "style", "subject", "submit", "subsequent", "substance",
    "substantial", "succeed", "success", "successful", "successfully", "such",
    "sudden", "suddenly", "sue", "suffer", "sufficient", "sugar", "suggest",
    "suggestion", "suicide", "suit", "summer", "summit", "sun", "super", "supply",
    "support", "supporter", "suppose", "supposed", "supreme", "sure", "surely",
    "surface", "surgery", "surprise", "surprised", "surprising", "surprisingly",
    "surround", "survey", "survival", "survive", "survivor", "suspect",
    "sustain", "swear", "sweep", "sweet", "swim", "swing", "switch", "symbol",
    "symptom", "system", "table", "tablespoon", "tactic", "tail", "take",
    "tale", "talent", "talk", "tall", "tank", "tap", "tape", "target", "task",
    "taste", "tax", "taxpayer", "tea", "teach", "teacher", "teaching", "team",
    "tear", "teaspoon", "technical", "technique", "technology", "teen",
    "teenager", "telephone", "telescope", "television", "tell", "temperature",
    "temporary", "ten", "tend", "tendency", "tennis", "tension", "tent", "term",
    "terms", "terrible", "territory", "terror", "terrorism", "terrorist", "test",
    "testify", "testimony", "testing", "text", "than", "thank", "thanks", "that",
    "the", "theater", "their", "them", "theme", "themselves", "then", "theory",
    "therapy", "there", "therefore", "these", "they", "thick", "thin", "thing",
    "think", "thinking", "third", "thirty", "this", "those", "though", "thought",
    "thousand", "threat", "threaten", "three", "throat", "through", "throughout",
    "throw", "thus", "ticket", "tie", "tight", "time", "tiny", "tip", "tire",
    "tired", "tissue", "title", "to", "tobacco", "today", "toe", "together",
    "tomato", "tomorrow", "tone", "tongue", "tonight", "too", "tool", "tooth",
    "top", "topic", "toss", "total", "totally", "touch", "tough", "tour",
    "tourist", "tournament", "toward", "towards", "tower", "town", "toy", "trace",
    "track", "trade", "tradition", "traditional", "traffic", "tragedy", "trail",
    "train", "training", "transfer", "transform", "transformation", "transition",
    "translate", "transportation", "travel", "treat", "treatment", "treaty",
    "tree", "tremendous", "trend", "trial", "tribe", "trick", "trip", "troop",
    "trouble", "truck", "true", "truly", "trust", "truth", "try", "tube",
    "tunnel", "turn", "tv", "twelve", "twenty", "twice", "twin", "two", "type",
    "typical", "typically", "ugly", "ultimate", "ultimately", "unable", "uncle",
    "under", "undergo", "understand", "understanding", "unfortunately", "uniform",
    "union", "unique", "unit", "united", "universal", "universe", "university",
    "unknown", "unless", "unlike", "unlikely", "until", "unusual", "up", "upon",
    "upper", "urban", "urge", "us", "use", "used", "useful", "user", "usual",
    "usually", "utility", "vacation", "valley", "valuable", "value", "variable",
    "variation", "variety", "various", "vary", "vast", "vegetable", "vehicle",
    "venture", "version", "versus", "very", "vessel", "veteran", "via", "victim",
    "victory", "video", "view", "viewer", "village", "violate", "violation",
    "violence", "violent", "virtually", "virtue", "virus", "visible", "vision",
    "visit", "visitor", "visual", "vital", "voice", "volume", "volunteer", "vote",
    "voter", "vs", "vulnerable", "wage", "wait", "wake", "walk", "wall", "wander",
    "want", "war", "warm", "warn", "warning", "wash", "waste", "watch", "water",
    "wave", "way", "we", "weak", "wealth", "wealthy", "weapon", "wear", "weather",
    "wedding", "week", "weekend", "weekly", "weigh", "weight", "welcome",
    "welfare", "well", "west", "western", "wet", "what", "whatever", "wheel",
    "when", "whenever", "where", "whereas", "whether", "which", "while",
    "whisper", "white", "who", "whole", "whom", "whose", "why", "wide", "widely",
    "widespread", "wife", "wild", "will", "willing", "win", "wind", "window",
    "wine", "wing", "winner", "winter", "wipe", "wire", "wisdom", "wise", "wish",
    "with", "withdraw", "within", "without", "witness", "woman", "wonder",
    "wonderful", "wood", "wooden", "word", "work", "worker", "working", "works",
    "workshop", "world", "worried", "worry", "worth", "would", "wound", "wrap",
    "write", "writer", "writing", "wrong", "yard", "yeah", "year", "yell",
    "yellow", "yes", "yesterday", "yet", "yield", "you", "young", "your",
    "yours", "yourself", "youth", "zone"
]

    def generate_passphrase(self, words: int = 4, separator: str = "-", capitalize: bool = False, include_number: bool = False) -> str:
        """
        Generates a passphrase consisting of randomly chosen words.
        """
        if words < 1:
            raise ValueError("Passphrase must contain at least 1 word.")

        chosen_words = [secrets.choice(self.DEFAULT_WORDLIST) for _ in range(words)]

        if capitalize:
            chosen_words = [word.capitalize() for word in chosen_words]

        passphrase = separator.join(chosen_words)

        if include_number:
            passphrase += str(secrets.choice(range(10)))

        return passphrase

    def generate(self, length: int = 16, use_upper: bool = True, use_lower: bool = True, use_digits: bool = True, use_symbols: bool = True) -> str:
        """
        Generates a cryptographically secure random password.
        """
        if length < 4:
            raise ValueError("Password length must be at least 4.")

        charset = ""
        if use_upper: charset += string.ascii_uppercase
        if use_lower: charset += string.ascii_lowercase
        if use_digits: charset += string.digits
        if use_symbols: charset += string.punctuation

        if not charset:
            raise ValueError("At least one character set must be selected.")

        # Ensure at least one character from each selected set is included
        password_chars = []
        if use_upper: password_chars.append(secrets.choice(string.ascii_uppercase))
        if use_lower: password_chars.append(secrets.choice(string.ascii_lowercase))
        if use_digits: password_chars.append(secrets.choice(string.digits))
        if use_symbols: password_chars.append(secrets.choice(string.punctuation))

        # Fill the rest
        remaining_length = length - len(password_chars)
        for _ in range(remaining_length):
            password_chars.append(secrets.choice(charset))

        # Shuffle the result
        password_list = list(password_chars)
        # shuffle doesn't exist in secrets, use SystemRandom which secrets uses
        # or just use random.shuffle if we don't care about order leakage (which we shouldn't for password generation usually, but let's be safe)
        # Actually secrets module suggests using SystemRandom().shuffle if needed, or just manual shuffle.
        # But random.shuffle uses Mersenne Twister, not CSPRNG.
        # A simple fisher-yates using secrets.randbelow is better.
        for i in range(len(password_list) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            password_list[i], password_list[j] = password_list[j], password_list[i]

        return "".join(password_list)

    def check_strength(self, password: str) -> Dict[str, Any]:
        """
        Analyzes password strength using entropy calculation and heuristics.
        """
        length = len(password)

        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_symbol = any(c in string.punctuation for c in password)

        pool_size = 0
        if has_lower: pool_size += 26
        if has_upper: pool_size += 26
        if has_digit: pool_size += 10
        if has_symbol: pool_size += 32

        if pool_size == 0:
            entropy = 0
        else:
            entropy = length * math.log2(pool_size)

        # Score (0-4)
        score = 0
        if entropy > 28: score += 1
        if entropy > 40: score += 1
        if entropy > 60: score += 1
        if entropy > 100: score += 1 # Bonus for very strong

        feedback = []
        if length < 8:
            feedback.append("Password is too short.")
            score = min(score, 1) # Cap score for short passwords
        if not (has_upper and has_lower and has_digit):
            feedback.append("Add more variety (uppercase, lowercase, numbers).")
        if not has_symbol:
            feedback.append("Add symbols for higher entropy.")
        if entropy < 40 and length >= 8:
            feedback.append("Entropy is low, consider a longer password or more variety.")

        # Common word check (very basic)
        common_words = ["password", "123456", "admin", "welcome", "qwerty"]
        if password.lower() in common_words:
            score = 0
            feedback.append("This is a very common password.")

        return {
            "score": score,
            "entropy": round(entropy, 2),
            "feedback": feedback,
            "length": length
        }

    def check_pwned(self, password: str) -> int:
        """
        Checks if the password has been exposed in data breaches using the Have I Been Pwned API.
        Returns the number of times it has appeared, or 0 if it hasn't.
        """
        sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()  # nosec B324
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Combined-Autonomous-Coding-Agent'})

        try:
            with urllib.request.urlopen(req) as response:  # nosec B310
                res_body = response.read().decode('utf-8')

                for line in res_body.splitlines():
                    if line.startswith(suffix):
                        _, count_str = line.split(':')
                        return int(count_str)
        except urllib.error.URLError:
            pass # Return 0 or raise? Better to just fail silently or raise exception. Let's raise to let the UI know it failed.
            raise RuntimeError("Failed to contact Have I Been Pwned API.")

        return 0

    def hash_password(self, password: str, algo: str = "scrypt", salt: Optional[str] = None) -> str:
        """
        Hashes a password.
        """
        if algo == "bcrypt":
            import bcrypt
            if salt:
                salt_bytes = salt.encode('utf-8')
                # bcrypt requires a specific salt format; typically it generates its own.
                # If a custom salt is provided, it might not be a valid bcrypt salt,
                # but we will try to use it if it is 22 characters long base64.
                # However, it's safer to just use gensalt if not a valid bcrypt salt.
                if not salt_bytes.startswith(b"$2"):
                    salt_bytes = bcrypt.gensalt()
            else:
                salt_bytes = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt_bytes)
            return hashed.decode('utf-8')

        if salt:
            salt_bytes = base64.b64decode(salt) if len(salt) % 4 == 0 and salt.endswith("==") or salt.endswith("=") else salt.encode('utf-8')
        else:
            salt_bytes = os.urandom(16)
            salt = base64.b64encode(salt_bytes).decode('utf-8')

        if algo == "scrypt":
            if not HAS_CRYPTOGRAPHY:
                return "Error: 'cryptography' library not installed. Cannot use scrypt."

            kdf = Scrypt(
                salt=salt_bytes,
                length=32,
                n=2**14,
                r=8,
                p=1,
                backend=default_backend()
            )
            key = kdf.derive(password.encode('utf-8'))
            hash_str = base64.b64encode(key).decode('utf-8')
            # Format: $scrypt$salt$hash
            return f"$scrypt${salt}${hash_str}"

        elif algo == "pbkdf2":
            # PBKDF2-HMAC-SHA256
            key = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt_bytes,
                100000
            )
            hash_str = base64.b64encode(key).decode('utf-8')
            return f"$pbkdf2-sha256${salt}${hash_str}"

        else:
            raise ValueError(f"Unsupported algorithm: {algo}")

    def verify_password(self, password: str, hashed: str) -> bool:
        """
        Verifies a password against a hash.
        """
        if hashed.startswith("$scrypt$") or hashed.startswith("$pbkdf2-sha256$"):
            parts = hashed.split("$")
            if len(parts) != 4:
                return False
            algo, salt, _ = parts[1], parts[2], parts[3]

            # Map back to algorithm expected by hash_password
            if algo == "pbkdf2-sha256":
                algo = "pbkdf2"

            expected_hash = self.hash_password(password, algo=algo, salt=salt)
            return secrets.compare_digest(expected_hash, hashed)
        elif hashed.startswith("$2a$") or hashed.startswith("$2b$") or hashed.startswith("$2y$"):
            import bcrypt
            try:
                return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
            except Exception:
                return False
        else:
            raise ValueError(f"Unsupported hash format: {hashed}")

def run_password_lab_logic(args):
    """
    Logic for the password-lab command.
    """
    manager = PasswordLabManager()

    if args.action == "generate":
        try:
            pwd = manager.generate(
                length=args.length,
                use_upper=not args.no_upper,
                use_lower=not args.no_lower,
                use_digits=not args.no_digits,
                use_symbols=not args.no_symbols
            )
            print(pwd)
            # Optional: Show strength of generated password
            if args.verbose:
                strength = manager.check_strength(pwd)
                print(f"\nEntropy: {strength['entropy']} bits")
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.action == "passphrase":
        try:
            pwd = manager.generate_passphrase(
                words=args.words,
                separator=args.separator,
                capitalize=getattr(args, 'capitalize', False),
                include_number=getattr(args, 'include_number', False)
            )
            print(pwd)
        except ValueError as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.action == "check":
        if not args.password:
            # Prompt securely
            import getpass
            password = getpass.getpass("Enter password to check: ")
        else:
            password = args.password

        result = manager.check_strength(password)

        score_display = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]
        score_idx = min(result['score'], 4)

        print(f"--- Password Strength: {score_display[score_idx]} ({result['score']}/4) ---")
        print(f"Length: {result['length']}")
        print(f"Entropy: {result['entropy']} bits")
        if result['feedback']:
            print("Feedback:")
            for item in result['feedback']:
                print(f"  - {item}")

    elif args.action == "hash":
        if not args.password:
            import getpass
            password = getpass.getpass("Enter password to hash: ")
        else:
            password = args.password

        try:
            hashed = manager.hash_password(password, algo=args.algo, salt=args.salt)
            print(hashed)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.action == "pwned":
        if not getattr(args, 'password', None):
            import getpass
            password = getpass.getpass("Enter password to check if pwned: ")
        else:
            password = args.password

        try:
            count = manager.check_pwned(password)
            if count > 0:
                print(f"⚠️ Oh no! This password has been seen {count} times before in data breaches.")
                sys.exit(1)
            else:
                print("✅ Good news! This password wasn't found in any known data breaches.")
                sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif args.action == "verify":
        if not args.password:
            import getpass
            password = getpass.getpass("Enter password to verify: ")
        else:
            password = args.password

        if not getattr(args, 'hash', None):
            print("Error: --hash is required for verify.")
            sys.exit(1)

        try:
            is_valid = manager.verify_password(password, args.hash)
            if is_valid:
                print("✅ Password is valid.")
                sys.exit(0)
            else:
                print("❌ Invalid password.")
                sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
