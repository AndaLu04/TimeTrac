"""
Material 3 Theme adapted for CustomTkinter.

This module provides color definitions and theme configurations from the original
Kotlin Material 3 theme, converted for use with CustomTkinter library.

Usage:
    import customtkinter as ctk
    from theme import apply_material3_theme, light_theme, dark_theme

    # Apply light theme
    apply_material3_theme(appearance_mode="light")
    
    # Or apply dark theme
    apply_material3_theme(appearance_mode="dark")
    
    # Or use custom themes
    ctk.set_default_color_theme(light_theme)
"""


# =============================================================================
# COLOR DEFINITIONS
# =============================================================================
# All colors are converted from Kotlin format (0xFFAARRGGBB) to Python format (#AARRGGBB or #RRGGBB)
# For CustomTkinter, we use the RRGGBB format (6-digit hex without alpha)

# --- Light Theme Colors ---
PRIMARY_LIGHT = "#415F91"
ON_PRIMARY_LIGHT = "#FFFFFF"
PRIMARY_CONTAINER_LIGHT = "#D6E3FF"
ON_PRIMARY_CONTAINER_LIGHT = "#284777"

SECONDARY_LIGHT = "#565F71"
ON_SECONDARY_LIGHT = "#FFFFFF"
SECONDARY_CONTAINER_LIGHT = "#DAE2F9"
ON_SECONDARY_CONTAINER_LIGHT = "#3E4759"

TERTIARY_LIGHT = "#705575"
ON_TERTIARY_LIGHT = "#FFFFFF"
TERTIARY_CONTAINER_LIGHT = "#FAD8FD"
ON_TERTIARY_CONTAINER_LIGHT = "#573E5C"

ERROR_LIGHT = "#BA1A1A"
ON_ERROR_LIGHT = "#FFFFFF"
ERROR_CONTAINER_LIGHT = "#FFDAD6"
ON_ERROR_CONTAINER_LIGHT = "#93000A"

BACKGROUND_LIGHT = "#F9F9FF"
ON_BACKGROUND_LIGHT = "#191C20"
SURFACE_LIGHT = "#F9F9FF"
ON_SURFACE_LIGHT = "#191C20"
SURFACE_VARIANT_LIGHT = "#E0E2EC"
ON_SURFACE_VARIANT_LIGHT = "#44474E"

OUTLINE_LIGHT = "#74777F"
OUTLINE_VARIANT_LIGHT = "#C4C6D0"
SCRIM_LIGHT = "#000000"

INVERSE_SURFACE_LIGHT = "#2E3036"
INVERSE_ON_SURFACE_LIGHT = "#F0F0F7"
INVERSE_PRIMARY_LIGHT = "#AAC7FF"

SURFACE_DIM_LIGHT = "#D9D9E0"
SURFACE_BRIGHT_LIGHT = "#F9F9FF"
SURFACE_CONTAINER_LOWEST_LIGHT = "#FFFFFF"
SURFACE_CONTAINER_LOW_LIGHT = "#F3F3FA"
SURFACE_CONTAINER_LIGHT = "#EDEDF4"
SURFACE_CONTAINER_HIGH_LIGHT = "#E7E8EE"
SURFACE_CONTAINER_HIGHEST_LIGHT = "#E2E2E9"


# --- Dark Theme Colors ---
PRIMARY_DARK = "#AAC7FF"
ON_PRIMARY_DARK = "#0A305F"
PRIMARY_CONTAINER_DARK = "#284777"
ON_PRIMARY_CONTAINER_DARK = "#D6E3FF"

SECONDARY_DARK = "#BEC6DC"
ON_SECONDARY_DARK = "#283141"
SECONDARY_CONTAINER_DARK = "#3E4759"
ON_SECONDARY_CONTAINER_DARK = "#DAE2F9"

TERTIARY_DARK = "#DDBCE0"
ON_TERTIARY_DARK = "#3F2844"
TERTIARY_CONTAINER_DARK = "#573E5C"
ON_TERTIARY_CONTAINER_DARK = "#FAD8FD"

ERROR_DARK = "#FFB4AB"
ON_ERROR_DARK = "#690005"
ERROR_CONTAINER_DARK = "#93000A"
ON_ERROR_CONTAINER_DARK = "#FFDAD6"

BACKGROUND_DARK = "#111318"
ON_BACKGROUND_DARK = "#E2E2E9"
SURFACE_DARK = "#111318"
ON_SURFACE_DARK = "#E2E2E9"
SURFACE_VARIANT_DARK = "#44474E"
ON_SURFACE_VARIANT_DARK = "#C4C6D0"

OUTLINE_DARK = "#8E9099"
OUTLINE_VARIANT_DARK = "#44474E"
SCRIM_DARK = "#000000"

INVERSE_SURFACE_DARK = "#E2E2E9"
INVERSE_ON_SURFACE_DARK = "#2E3036"
INVERSE_PRIMARY_DARK = "#415F91"

SURFACE_DIM_DARK = "#111318"
SURFACE_BRIGHT_DARK = "#37393E"
SURFACE_CONTAINER_LOWEST_DARK = "#0C0E13"
SURFACE_CONTAINER_LOW_DARK = "#191C20"
SURFACE_CONTAINER_DARK = "#1D2024"
SURFACE_CONTAINER_HIGH_DARK = "#282A2F"
SURFACE_CONTAINER_HIGHEST_DARK = "#33353A"


# =============================================================================
# FONT DEFINITIONS (from Type.kt)
# =============================================================================
# The original uses JetBrains Mono font, which is available in most systems
# or can be installed via pip: pip install jetbrains-mono-font

BODY_FONT = ("JetBrains Mono", 14)
DISPLAY_FONT = ("JetBrains Mono", 16)
TITLE_FONT = ("JetBrains Mono", 16, "bold")
HEADLINE_FONT = ("JetBrains Mono", 20, "bold")
LABEL_FONT = ("JetBrains Mono", 12)

# Fallback fonts in case JetBrains Mono is not available
FALLBACK_FONTS = ["Consolas", "Courier New", "monospace"]


# =============================================================================
# CUSTOMTKINTER THEME CONFIGURATIONS
# =============================================================================

# Light Theme for CustomTkinter
light_theme = {
    # Color Theme
    "color": {
        # Primary colors
        "primary": PRIMARY_LIGHT,
        "primary_hover": PRIMARY_CONTAINER_LIGHT,
        "primary_active": ON_PRIMARY_CONTAINER_LIGHT,
        
        # Secondary colors
        "secondary": SECONDARY_LIGHT,
        "secondary_hover": SECONDARY_CONTAINER_LIGHT,
        "secondary_active": ON_SECONDARY_CONTAINER_LIGHT,
        
        # Text colors
        "text": ON_BACKGROUND_LIGHT,
        "text_primary": ON_BACKGROUND_LIGHT,
        "text_secondary": ON_SURFACE_VARIANT_LIGHT,
        "text_disabled": SURFACE_VARIANT_LIGHT,
        
        # Background colors
        "bg": BACKGROUND_LIGHT,
        "bg_secondary": SURFACE_CONTAINER_LIGHT,
        "bg_tertiary": SURFACE_CONTAINER_HIGH_LIGHT,
        "bg_hover": SURFACE_CONTAINER_HIGH_LIGHT,
        "bg_active": SURFACE_CONTAINER_HIGHEST_LIGHT,
        
        # Surface colors (frames, widgets)
        "surface": SURFACE_LIGHT,
        "surface_hover": SURFACE_CONTAINER_LOW_LIGHT,
        "surface_active": SURFACE_CONTAINER_LIGHT,
        
        # Border colors
        "border": OUTLINE_LIGHT,
        "border_hover": OUTLINE_VARIANT_LIGHT,
        "border_active": PRIMARY_LIGHT,
        
        # Error colors
        "error": ERROR_LIGHT,
        "error_hover": ERROR_CONTAINER_LIGHT,
        "error_active": ON_ERROR_CONTAINER_LIGHT,
        
        # Placeholder
        "placeholder": ON_SURFACE_VARIANT_LIGHT,
        
        # Scrollbar
        "scrollbar": SURFACE_VARIANT_LIGHT,
        "scrollbar_hover": OUTLINE_LIGHT,
        "scrollbar_active": PRIMARY_LIGHT,
        
        # Switch
        "switch": PRIMARY_LIGHT,
        "switch_hover": PRIMARY_CONTAINER_LIGHT,
        "switch_active": ON_PRIMARY_CONTAINER_LIGHT,
        
        # Slider
        "slider": PRIMARY_LIGHT,
        "slider_hover": PRIMARY_CONTAINER_LIGHT,
        "slider_active": ON_PRIMARY_CONTAINER_LIGHT,
        
        # Progress bar
        "progress": PRIMARY_LIGHT,
        "progress_hover": PRIMARY_CONTAINER_LIGHT,
        
        # Entry/ComboBox
        "entry": SURFACE_LIGHT,
        "entry_hover": SURFACE_CONTAINER_LOW_LIGHT,
        "entry_active": SURFACE_CONTAINER_LIGHT,
        
        # Button colors
        "button": PRIMARY_LIGHT,
        "button_hover": PRIMARY_CONTAINER_LIGHT,
        "button_active": ON_PRIMARY_CONTAINER_LIGHT,
        
        # Tab colors
        "tab": SURFACE_CONTAINER_LOW_LIGHT,
        "tab_hover": SURFACE_CONTAINER_LIGHT,
        "tab_active": PRIMARY_LIGHT,
        
        # Checkbox/Radiobutton
        "checkbox": PRIMARY_LIGHT,
        "checkbox_hover": PRIMARY_CONTAINER_LIGHT,
        "checkbox_active": ON_PRIMARY_CONTAINER_LIGHT,
        "radio": PRIMARY_LIGHT,
        "radio_hover": PRIMARY_CONTAINER_LIGHT,
        "radio_active": ON_PRIMARY_CONTAINER_LIGHT,
        
        # Dropdown menu
        "dropdown": SURFACE_LIGHT,
        "dropdown_hover": SURFACE_CONTAINER_LOW_LIGHT,
        "dropdown_active": SURFACE_CONTAINER_LIGHT,
        
        # Tooltip
        "tooltip": SURFACE_LIGHT,
        "tooltip_text": ON_SURFACE_LIGHT,
        
        # Frame colors
        "frame": SURFACE_LIGHT,
        "frame_hover": SURFACE_CONTAINER_LOW_LIGHT,
        
        # Treeview
        "treeview": SURFACE_LIGHT,
        "treeview_hover": SURFACE_CONTAINER_LOW_LIGHT,
        "treeview_active": SURFACE_CONTAINER_LIGHT,
        
        # Notebook
        "notebook": SURFACE_CONTAINER_LOWEST_LIGHT,
    },
    
    # Font settings
    "font": {
        "family": "JetBrains Mono",
        "size": 14,
        "size_small": 12,
        "size_medium": 14,
        "size_large": 16,
        "size_huge": 20,
    },
    
    # Border settings
    "border": {
        "width": 1,
        "radius": 6,
        "radius_small": 4,
        "radius_large": 8,
    },
    
    # Padding settings
    "padding": {
        "small": 4,
        "medium": 8,
        "large": 12,
    },
}


# Dark Theme for CustomTkinter
dark_theme = {
    # Color Theme
    "color": {
        # Primary colors
        "primary": PRIMARY_DARK,
        "primary_hover": PRIMARY_CONTAINER_DARK,
        "primary_active": ON_PRIMARY_CONTAINER_DARK,
        
        # Secondary colors
        "secondary": SECONDARY_DARK,
        "secondary_hover": SECONDARY_CONTAINER_DARK,
        "secondary_active": ON_SECONDARY_CONTAINER_DARK,
        
        # Text colors
        "text": ON_BACKGROUND_DARK,
        "text_primary": ON_BACKGROUND_DARK,
        "text_secondary": ON_SURFACE_VARIANT_DARK,
        "text_disabled": SURFACE_VARIANT_DARK,
        
        # Background colors
        "bg": BACKGROUND_DARK,
        "bg_secondary": SURFACE_CONTAINER_DARK,
        "bg_tertiary": SURFACE_CONTAINER_HIGH_DARK,
        "bg_hover": SURFACE_CONTAINER_HIGH_DARK,
        "bg_active": SURFACE_CONTAINER_HIGHEST_DARK,
        
        # Surface colors (frames, widgets)
        "surface": SURFACE_DARK,
        "surface_hover": SURFACE_CONTAINER_LOW_DARK,
        "surface_active": SURFACE_CONTAINER_DARK,
        
        # Border colors
        "border": OUTLINE_DARK,
        "border_hover": OUTLINE_VARIANT_DARK,
        "border_active": PRIMARY_DARK,
        
        # Error colors
        "error": ERROR_DARK,
        "error_hover": ERROR_CONTAINER_DARK,
        "error_active": ON_ERROR_CONTAINER_DARK,
        
        # Placeholder
        "placeholder": ON_SURFACE_VARIANT_DARK,
        
        # Scrollbar
        "scrollbar": SURFACE_VARIANT_DARK,
        "scrollbar_hover": OUTLINE_DARK,
        "scrollbar_active": PRIMARY_DARK,
        
        # Switch
        "switch": PRIMARY_DARK,
        "switch_hover": PRIMARY_CONTAINER_DARK,
        "switch_active": ON_PRIMARY_CONTAINER_DARK,
        
        # Slider
        "slider": PRIMARY_DARK,
        "slider_hover": PRIMARY_CONTAINER_DARK,
        "slider_active": ON_PRIMARY_CONTAINER_DARK,
        
        # Progress bar
        "progress": PRIMARY_DARK,
        "progress_hover": PRIMARY_CONTAINER_DARK,
        
        # Entry/ComboBox
        "entry": SURFACE_DARK,
        "entry_hover": SURFACE_CONTAINER_LOW_DARK,
        "entry_active": SURFACE_CONTAINER_DARK,
        
        # Button colors
        "button": PRIMARY_DARK,
        "button_hover": PRIMARY_CONTAINER_DARK,
        "button_active": ON_PRIMARY_CONTAINER_DARK,
        
        # Tab colors
        "tab": SURFACE_CONTAINER_LOW_DARK,
        "tab_hover": SURFACE_CONTAINER_DARK,
        "tab_active": PRIMARY_DARK,
        
        # Checkbox/Radiobutton
        "checkbox": PRIMARY_DARK,
        "checkbox_hover": PRIMARY_CONTAINER_DARK,
        "checkbox_active": ON_PRIMARY_CONTAINER_DARK,
        "radio": PRIMARY_DARK,
        "radio_hover": PRIMARY_CONTAINER_DARK,
        "radio_active": ON_PRIMARY_CONTAINER_DARK,
        
        # Dropdown menu
        "dropdown": SURFACE_DARK,
        "dropdown_hover": SURFACE_CONTAINER_LOW_DARK,
        "dropdown_active": SURFACE_CONTAINER_DARK,
        
        # Tooltip
        "tooltip": SURFACE_DARK,
        "tooltip_text": ON_SURFACE_DARK,
        
        # Frame colors
        "frame": SURFACE_DARK,
        "frame_hover": SURFACE_CONTAINER_LOW_DARK,
        
        # Treeview
        "treeview": SURFACE_DARK,
        "treeview_hover": SURFACE_CONTAINER_LOW_DARK,
        "treeview_active": SURFACE_CONTAINER_DARK,
        
        # Notebook
        "notebook": SURFACE_CONTAINER_LOWEST_DARK,
    },
    
    # Font settings
    "font": {
        "family": "JetBrains Mono",
        "size": 14,
        "size_small": 12,
        "size_medium": 14,
        "size_large": 16,
        "size_huge": 20,
    },
    
    # Border settings
    "border": {
        "width": 1,
        "radius": 6,
        "radius_small": 4,
        "radius_large": 8,
    },
    
    # Padding settings
    "padding": {
        "small": 4,
        "medium": 8,
        "large": 12,
    },
}


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def apply_material3_theme(appearance_mode: str = "system", color_theme: str = "blue"):
    """
    Apply the Material 3 theme to CustomTkinter.
    
    Args:
        appearance_mode: "light", "dark", or "system" (follows system theme)
        color_theme: Currently supports "blue" (default Material 3 theme)
    
    Usage:
        import customtkinter as ctk
        from theme import apply_material3_theme
        
        ctk.set_appearance_mode("dark")
        apply_material3_theme("dark")
    """
    import customtkinter as ctk
    
    # Set appearance mode
    ctk.set_appearance_mode(appearance_mode)
    
    # Set color theme based on appearance mode
    if appearance_mode == "dark" or (appearance_mode == "system" and _is_dark_mode()):
        ctk.set_default_color_theme(dark_theme)
    else:
        ctk.set_default_color_theme(light_theme)


def _is_dark_mode() -> bool:
    """
    Check if the system is in dark mode.
    Note: This is a simple implementation; you may need to extend it for your OS.
    """
    try:
        import platform
        system = platform.system()
        
        if system == "Windows":
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                              r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as key:
                value = winreg.QueryValueEx(key, "AppsUseLightTheme")[0]
                return value == 0
        elif system == "Darwin":  # macOS
            import subprocess
            result = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"], 
                                  capture_output=True, text=True)
            return result.stdout.strip() == "Dark"
        elif system == "Linux":
            # Try to check for common Linux desktop environments
            import os
            desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
            if "gnome" in desktop:
                import subprocess
                result = subprocess.run(["gsettings", "get", 
                                       "org.gnome.desktop.interface", "color-scheme"],
                                      capture_output=True, text=True)
                return "dark" in result.stdout.lower()
    except Exception:
        pass
    
    # Default to light mode if detection fails
    return False


def get_color(name: str, dark: bool = False) -> str:
    """
    Get a color by name from the theme.
    
    Args:
        name: Color name (e.g., "primary", "background", "error")
        dark: If True, return the dark theme color
    
    Returns:
        Hex color string (e.g., "#415F91")
    """
    colors = {
        # Light colors
        "light": {
            "primary": PRIMARY_LIGHT,
            "on_primary": ON_PRIMARY_LIGHT,
            "primary_container": PRIMARY_CONTAINER_LIGHT,
            "on_primary_container": ON_PRIMARY_CONTAINER_LIGHT,
            "secondary": SECONDARY_LIGHT,
            "on_secondary": ON_SECONDARY_LIGHT,
            "secondary_container": SECONDARY_CONTAINER_LIGHT,
            "on_secondary_container": ON_SECONDARY_CONTAINER_LIGHT,
            "tertiary": TERTIARY_LIGHT,
            "on_tertiary": ON_TERTIARY_LIGHT,
            "tertiary_container": TERTIARY_CONTAINER_LIGHT,
            "on_tertiary_container": ON_TERTIARY_CONTAINER_LIGHT,
            "error": ERROR_LIGHT,
            "on_error": ON_ERROR_LIGHT,
            "error_container": ERROR_CONTAINER_LIGHT,
            "on_error_container": ON_ERROR_CONTAINER_LIGHT,
            "background": BACKGROUND_LIGHT,
            "on_background": ON_BACKGROUND_LIGHT,
            "surface": SURFACE_LIGHT,
            "on_surface": ON_SURFACE_LIGHT,
            "surface_variant": SURFACE_VARIANT_LIGHT,
            "on_surface_variant": ON_SURFACE_VARIANT_LIGHT,
            "outline": OUTLINE_LIGHT,
            "outline_variant": OUTLINE_VARIANT_LIGHT,
        },
        # Dark colors
        "dark": {
            "primary": PRIMARY_DARK,
            "on_primary": ON_PRIMARY_DARK,
            "primary_container": PRIMARY_CONTAINER_DARK,
            "on_primary_container": ON_PRIMARY_CONTAINER_DARK,
            "secondary": SECONDARY_DARK,
            "on_secondary": ON_SECONDARY_DARK,
            "secondary_container": SECONDARY_CONTAINER_DARK,
            "on_secondary_container": ON_SECONDARY_CONTAINER_DARK,
            "tertiary": TERTIARY_DARK,
            "on_tertiary": ON_TERTIARY_DARK,
            "tertiary_container": TERTIARY_CONTAINER_DARK,
            "on_tertiary_container": ON_TERTIARY_CONTAINER_DARK,
            "error": ERROR_DARK,
            "on_error": ON_ERROR_DARK,
            "error_container": ERROR_CONTAINER_DARK,
            "on_error_container": ON_ERROR_CONTAINER_DARK,
            "background": BACKGROUND_DARK,
            "on_background": ON_BACKGROUND_DARK,
            "surface": SURFACE_DARK,
            "on_surface": ON_SURFACE_DARK,
            "surface_variant": SURFACE_VARIANT_DARK,
            "on_surface_variant": ON_SURFACE_VARIANT_DARK,
            "outline": OUTLINE_DARK,
            "outline_variant": OUTLINE_VARIANT_DARK,
        }
    }
    
    mode = "dark" if dark else "light"
    return colors.get(mode, {}).get(name.lower(), "#000000")


def create_custom_theme(
    primary_color: str = None,
    secondary_color: str = None,
    dark_mode: bool = False
) -> dict:
    """
    Create a custom theme based on the Material 3 color system.
    
    Args:
        primary_color: Custom primary color in hex format (e.g., "#415F91")
        secondary_color: Custom secondary color in hex format
        dark_mode: If True, create a dark theme variant
    
    Returns:
        A CustomTkinter theme dictionary
    """
    base_theme = dark_theme if dark_mode else light_theme
    
    if primary_color:
        base_theme["color"]["primary"] = primary_color
        # Generate lighter/darker variants for hover/active states
        # This is a simple implementation; consider using a proper color library
        base_theme["color"]["primary_hover"] = _lighten_color(primary_color, 20)
        base_theme["color"]["primary_active"] = _darken_color(primary_color, 20)
    
    if secondary_color:
        base_theme["color"]["secondary"] = secondary_color
        base_theme["color"]["secondary_hover"] = _lighten_color(secondary_color, 20)
        base_theme["color"]["secondary_active"] = _darken_color(secondary_color, 20)
    
    return base_theme


def _lighten_color(hex_color: str, percent: int = 10) -> str:
    """Lighten a hex color by a percentage."""
    import colorsys
    
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Convert to HSV
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    
    # Lighten
    l = max(0, min(1, l + (percent / 100.0)))
    
    # Convert back to RGB
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    
    # Convert to hex
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}".upper()


def _darken_color(hex_color: str, percent: int = 10) -> str:
    """Darken a hex color by a percentage."""
    import colorsys
    
    # Remove # if present
    hex_color = hex_color.lstrip('#')
    
    # Convert to RGB
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Convert to HSV
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    
    # Darken
    l = max(0, min(1, l - (percent / 100.0)))
    
    # Convert back to RGB
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    
    # Convert to hex
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}".upper()


# =============================================================================
# EXPORT ALL PUBLIC VARIABLES AND FUNCTIONS
# =============================================================================
__all__ = [
    # Color constants
    "PRIMARY_LIGHT", "ON_PRIMARY_LIGHT", "PRIMARY_CONTAINER_LIGHT",
    "ON_PRIMARY_CONTAINER_LIGHT", "SECONDARY_LIGHT", "ON_SECONDARY_LIGHT",
    "SECONDARY_CONTAINER_LIGHT", "ON_SECONDARY_CONTAINER_LIGHT",
    "TERTIARY_LIGHT", "ON_TERTIARY_LIGHT", "TERTIARY_CONTAINER_LIGHT",
    "ON_TERTIARY_CONTAINER_LIGHT", "ERROR_LIGHT", "ON_ERROR_LIGHT",
    "ERROR_CONTAINER_LIGHT", "ON_ERROR_CONTAINER_LIGHT", "BACKGROUND_LIGHT",
    "ON_BACKGROUND_LIGHT", "SURFACE_LIGHT", "ON_SURFACE_LIGHT",
    "SURFACE_VARIANT_LIGHT", "ON_SURFACE_VARIANT_LIGHT", "OUTLINE_LIGHT",
    "OUTLINE_VARIANT_LIGHT",
    
    "PRIMARY_DARK", "ON_PRIMARY_DARK", "PRIMARY_CONTAINER_DARK",
    "ON_PRIMARY_CONTAINER_DARK", "SECONDARY_DARK", "ON_SECONDARY_DARK",
    "SECONDARY_CONTAINER_DARK", "ON_SECONDARY_CONTAINER_DARK",
    "TERTIARY_DARK", "ON_TERTIARY_DARK", "TERTIARY_CONTAINER_DARK",
    "ON_TERTIARY_CONTAINER_DARK", "ERROR_DARK", "ON_ERROR_DARK",
    "ERROR_CONTAINER_DARK", "ON_ERROR_CONTAINER_DARK", "BACKGROUND_DARK",
    "ON_BACKGROUND_DARK", "SURFACE_DARK", "ON_SURFACE_DARK",
    "SURFACE_VARIANT_DARK", "ON_SURFACE_VARIANT_DARK", "OUTLINE_DARK",
    "OUTLINE_VARIANT_DARK",
    
    # Font constants
    "BODY_FONT", "DISPLAY_FONT", "TITLE_FONT", "HEADLINE_FONT", "LABEL_FONT",
    "FALLBACK_FONTS",
    
    # Theme dictionaries
    "light_theme", "dark_theme",
    
    # Functions
    "apply_material3_theme", "get_color", "create_custom_theme",
    "_lighten_color", "_darken_color",
]
