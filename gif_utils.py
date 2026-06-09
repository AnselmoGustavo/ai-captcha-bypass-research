import os
from datetime import datetime
from PIL import Image


def create_result_gif(image_paths, output_folder="successful_solves", prefix="success"):
    """Creates a GIF from a list of images and saves it with a timestamped prefix."""
    if not image_paths:
        print("No images provided for GIF creation.")
        return None

    os.makedirs(output_folder, exist_ok=True)

    valid_images = []
    for path in image_paths:
        if os.path.exists(path):
            try:
                valid_images.append(Image.open(path).convert("RGB"))
            except Exception as e:
                print(f"Warning: Could not open or convert image {path}. Skipping. Error: {e}")
        else:
            print(f"Warning: Image path for GIF not found: {path}. Skipping.")

    if not valid_images:
        print("\nCould not create GIF because no valid source images were found.")
        return None

    try:
        max_width = max(img.width for img in valid_images)
        max_height = max(img.height for img in valid_images)
        canvas_size = (max_width, max_height)

        processed_images = []
        for img in valid_images:
            canvas = Image.new("RGB", canvas_size, (255, 255, 255))
            paste_position = ((max_width - img.width) // 2, (max_height - img.height) // 2)
            canvas.paste(img, paste_position)
            processed_images.append(canvas)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(output_folder, f"{prefix}_{timestamp}.gif")

        processed_images[0].save(
            output_path,
            save_all=True,
            append_images=processed_images[1:],
            duration=800,
            loop=0,
        )

        print(f"\nSuccessfully saved GIF to {output_path}")
        return output_path
    except Exception as e:
        print(f"\nCould not create GIF. Error: {e}")
        return None
