def util_convert_hex_to_rgba(hex_color: str) -> str:
    """
    Convert a hex color string to rgba format.
    Handles hex formats: #RGB, #RGBA, #RRGGBB, #AARRGGBB
    
    Args:
        hex_color: Hex color string
        
    Returns:
        rgba color string
    """
    # Remove # if present
    has_hash = hex_color.startswith('#')
    hex_color = hex_color.lstrip('#')
    
    if len(hex_color) == 8:  # #AARRGGBB format from ColorButton
        a = int(hex_color[0:2], 16) / 255
        r = int(hex_color[2:4], 16)
        g = int(hex_color[4:6], 16)
        b = int(hex_color[6:8], 16)
        return f"rgba({r}, {g}, {b}, {a})"
    
    elif len(hex_color) == 6:  # #RRGGBB format
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, 1)"
    
    # elif len(hex_color) == 4:  # #RGBA format
    #     r = int(hex_color[0] + hex_color[0], 16)
    #     g = int(hex_color[1] + hex_color[1], 16)
    #     b = int(hex_color[2] + hex_color[2], 16)
    #     a = int(hex_color[3] + hex_color[3], 16) / 255
    #     return f"rgba({r}, {g}, {b}, {a})"
    
    # elif len(hex_color) == 3:  # #RGB format
    #     r = int(hex_color[0] + hex_color[0], 16)
    #     g = int(hex_color[1] + hex_color[1], 16)
    #     b = int(hex_color[2] + hex_color[2], 16)
    #     return f"rgba({r}, {g}, {b}, 1)"
    
    else:
        # If the format is not recognized, return the original color
        ret = f"{hex_color}"
        if has_hash:
            return '#' + ret
        else:
            return ret