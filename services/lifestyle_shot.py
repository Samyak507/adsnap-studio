from typing import Dict, Any, Optional, List
import requests
import base64

def lifestyle_shot_by_text(
    api_key: str,
    image_data: bytes,
    scene_description: str,
    placement_type: str = "original",
    num_results: int = 4,
    sync: bool = False,
    fast: bool = True,
    optimize_description: bool = True,
    original_quality: bool = False,
    exclude_elements: Optional[str] = None,
    shot_size: List[int] = [1000, 1000],
    manual_placement_selection: List[str] = ["upper_left"],
    padding_values: List[int] = [0, 0, 0, 0],
    foreground_image_size: Optional[List[int]] = None,
    foreground_image_location: Optional[List[int]] = None,
    force_rmbg: bool = False,
    content_moderation: bool = False,
    sku: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a lifestyle shot using text description.
    """

    url = "https://engine.prod.bria-api.com/v1/product/lifestyle_shot_by_text"

    headers = {
        "api_token": api_key.strip(),   # IMPORTANT FIX: remove whitespace/newline
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    # Convert image to base64
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    # Prepare the payload
    data = {
        "file": image_base64,
        "scene_description": scene_description,
        "placement_type": placement_type,
        "num_results": num_results,
        "sync": sync,
        "fast": fast,
        "optimize_description": optimize_description,
        "original_quality": original_quality,
        "force_rmbg": force_rmbg,
        "content_moderation": content_moderation
    }

    if exclude_elements and not fast:
        data["exclude_elements"] = exclude_elements

    if placement_type in ["automatic", "manual_placement", "custom_coordinates"]:
        data["shot_size"] = shot_size

    if placement_type == "manual_placement":
        data["manual_placement_selection"] = manual_placement_selection

    if placement_type == "manual_padding":
        data["padding_values"] = padding_values

    if placement_type == "custom_coordinates":
        if foreground_image_size:
            data["foreground_image_size"] = foreground_image_size
        if foreground_image_location:
            data["foreground_image_location"] = foreground_image_location

    if sku:
        data["sku"] = sku

    try:
        print("Sending Request → lifestyle_shot_by_text")
        print("Headers:", headers)
        print("Payload:", data)

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        print("Status:", response.status_code)
        print("Response:", response.text)

        return response.json()

    except Exception as e:
        raise Exception(f"Lifestyle shot generation failed: {str(e)}")
