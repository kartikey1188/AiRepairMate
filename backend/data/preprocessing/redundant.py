# STEP ONE

import os
import json

# Folder containing JSON files
INPUT_FOLDER = "../raw_data"
OUTPUT_FOLDER = "../clean_data"

# Keys to remove from JSON files
KEYS_TO_REMOVE = {
    "ifixit_links",
    "resources_links",
    "social_links",
    "legal_links",
    "license_link",
    "repair_is_noble_link",
    "copyright",
    "preview_statistics",
    "licensing_url",
    "team_info",
    "comments",
    "manifesto_url",
    "comments_section",
    "team",
    "statistics",
    "author_information",
    "team_information",
    "author",
    "author_info",
    "completed_count",
    "favorite_count",
    "comments_count",
    "view_statistics",
    "favorited_count",
    "contributors",
    "view_statistics_preview",
    "stay_in_loop",
    "comments_url",
    "contributors_url"
}

# Keys to remove from metadata
METADATA_KEYS_TO_REMOVE = {
    "member_since",
    "view_statistics",
    "author",
    "author_link",
    "contributors",
    "statistics",
    "completed_count",
    "favorite_count",
    "favorited_count",
    "comments_count",
    "other_contributors"
}

# Ensure output folder exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def clean_json_file(input_path, output_path):
    try:
        with open(input_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if isinstance(data, dict):
            # Remove unwanted top-level keys
            data = {k: v for k, v in data.items() if k not in KEYS_TO_REMOVE}
            
            # Remove unwanted keys inside metadata if present
            if "metadata" in data and isinstance(data["metadata"], dict):
                data["metadata"] = {k: v for k, v in data["metadata"].items() if k not in METADATA_KEYS_TO_REMOVE}
        
        # Save the cleaned data to the output folder
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        
        print(f"Processed: {input_path} -> {output_path}")
    except Exception as e:
        print(f"Error processing {input_path}: {e}")

def process_json_folder(input_folder, output_folder):
    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            clean_json_file(input_path, output_path)

if __name__ == "__main__":
    process_json_folder(INPUT_FOLDER, OUTPUT_FOLDER)
