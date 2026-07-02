# styles.py
STYLES = {
    1: {
        "name": "Karaoke Classic",
        "description": "Purple rounded box behind active word.",
        "type": "box",
        "defaults": {"box_color": "#8A2BE2", "text_color": "#FFFFFF"},
        "params": [("box_color", "color", "Box Color"), ("text_color", "color", "Text Color")]
    },
    2: {
        "name": "Neon Box",
        "description": "Bright yellow box with black text.",
        "type": "box",
        "defaults": {"box_color": "#FFFF00", "text_color": "#000000"},
        "params": [("box_color", "color", "Box Color"), ("text_color", "color", "Text Color")]
    },
    3: {
        "name": "Active Color (Hormozi)",
        "description": "Active word turns a custom color.",
        "type": "color",
        "defaults": {"active_color": "#FFFF00", "text_color": "#FFFFFF"},
        "params": [("active_color", "color", "Active Color"), ("text_color", "color", "Base Color")]
    },
    5: {
        "name": "Word Pop",
        "description": "Active word scales up.",
        "type": "scale",
        "defaults": {"scale_factor": 1.3, "text_color": "#FFFFFF"},
        "params": [("text_color", "color", "Text Color")]
    },
    6: {
        "name": "Classic Outline",
        "description": "White text with thick outline.",
        "type": "outline",
        "defaults": {"stroke_width": 4, "text_color": "#FFFFFF", "outline_color": "#000000"},
        "params": [("text_color", "color", "Text Color"), ("outline_color", "color", "Outline Color")]
    },
    7: {
        "name": "Minimalist Bar",
        "description": "Semi-transparent bar behind text.",
        "type": "bar",
        "defaults": {"bar_color": "#000000", "text_color": "#FFFFFF", "opacity": 180, "rounded": False},
        "params": [
            ("bar_color", "color", "Bar Color"),
            ("text_color", "color", "Text Color"),
            ("rounded", "bool", "Rounded Edges?")
        ]
    },
    8: {
        "name": "Word Reveal",
        "description": "Words appear one by one.",
        "type": "reveal",
        "defaults": {"text_color": "#FFFFFF"},
        "params": [("text_color", "color", "Text Color")]
    },
    9: {
        "name": "Bounce",
        "description": "Active word bounces up.",
        "type": "bounce",
        "defaults": {"text_color": "#FFFFFF", "bounce_offset": 20},
        "params": [("text_color", "color", "Text Color")]
    },
    10: {
        "name": "Glow",
        "description": "Active word has a blurred glow.",
        "type": "glow",
        "defaults": {"glow_color": "#00FFFF", "text_color": "#FFFFFF"},
        "params": [("glow_color", "color", "Glow Color"), ("text_color", "color", "Text Color")]
    },
    11: {
        "name": "Fade Highlight (Cinematic)",
        "description": "Fade In/Out with optional highlight.",
        "type": "cinematic",
        "defaults": {"text_color": "#FFFFFF", "highlight_enabled": False, "highlight_color": "#FFFF00"},
        "params": [
            ("text_color", "color", "Text Color"),
            ("highlight_enabled", "bool", "Highlight Key Words?"),
            ("highlight_color", "color", "Highlight Color")
        ]
    },
    12: {
        "name": "Custom Outline & Fill",
        "description": "Thick outline + Active word changes color.",
        "type": "outline_active",
        "defaults": {"stroke_width": 5, "text_color": "#FFFFFF", "outline_color": "#000000", "active_color": "#FFFF00"},
        "params": [
            ("text_color", "color", "Base Color"),
            ("outline_color", "color", "Outline Color"),
            ("active_color", "color", "Active Color")
        ]
    },
}

def get_style_names():
    return [f"{k}: {v['name']}" for k, v in STYLES.items()]

def get_style_config(index):
    # Returns a copy of defaults merged with type info
    style = STYLES.get(index, STYLES[1])
    config = style["defaults"].copy()
    config["type"] = style["type"]
    config["name"] = style["name"]
    # Add hidden defaults that aren't user-editable but needed
    if "extra_space" not in config: config["extra_space"] = 18
    if "box_padding" not in config: config["box_padding"] = 12
    return config

def get_style_params(index):
    return STYLES.get(index, STYLES[1]).get("params", [])