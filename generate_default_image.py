#!/usr/bin/env python
"""
Generate Default Profile Image
-----------------------------
This script generates a default silhouette avatar for profiles without images.
"""

from PIL import Image, ImageDraw
import os

def generate_silhouette_avatar(output_path="static/default-profile.jpg", size=(200, 200)):
    """
    Generate a simple silhouette profile image.
    
    Args:
        output_path (str): Path to save the generated image
        size (tuple): Width and height of the image in pixels
    """
    # Create a directory for the output file if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create a new image with white background
    img = Image.new('RGB', size, color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    # Draw a circle for the head
    circle_center = (size[0] // 2, size[1] // 3)
    circle_radius = size[0] // 6
    draw.ellipse(
        (
            circle_center[0] - circle_radius,
            circle_center[1] - circle_radius,
            circle_center[0] + circle_radius,
            circle_center[1] + circle_radius
        ),
        fill=(180, 180, 180)
    )
    
    # Draw a trapezoid for the body
    body_top_width = size[0] // 3
    body_top_y = circle_center[1] + circle_radius
    body_bottom_width = size[0] // 2
    body_bottom_y = size[1] - size[1] // 6
    
    body_points = [
        (size[0] // 2 - body_top_width // 2, body_top_y),  # Top left
        (size[0] // 2 + body_top_width // 2, body_top_y),  # Top right
        (size[0] // 2 + body_bottom_width // 2, body_bottom_y),  # Bottom right
        (size[0] // 2 - body_bottom_width // 2, body_bottom_y),  # Bottom left
    ]
    
    draw.polygon(body_points, fill=(180, 180, 180))
    
    # Draw a subtle border around the image
    border_width = 1
    draw.rectangle(
        [border_width, border_width, size[0] - border_width, size[1] - border_width],
        outline=(200, 200, 200),
        width=border_width
    )
    
    # Save the image
    img.save(output_path, format='JPEG', quality=95)
    print(f"Default profile image created at: {output_path}")

if __name__ == "__main__":
    generate_silhouette_avatar() 