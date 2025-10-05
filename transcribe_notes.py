import os
import json
import base64
from openai import OpenAI
from dotenv import load_dotenv

def encode_image(image_path):
    """Encodes the image at the given path to a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def validate_json_format(json_data):
    """
    Validates if the JSON data is a single object with 'type' and 'transcription' keys.
    """
    if not isinstance(json_data, dict):
        print("❌ Validation failed: The root is not a single object.")
        return False
    
    if 'type' not in json_data or 'transcription' not in json_data:
        print(f"❌ Validation failed: The object is missing 'type' or 'transcription' keys: {json_data}")
        return False
            
    return True

def transcribe_notes():
    """
    Loads notes, sends images to GPT-4o for transcription, 
    and saves the results to a new JSON file.
    """
    # 1. Load environment variables and initialize the OpenAI client
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("🛑 Error: OPENAI_API_KEY not found in a .env file.")
        return
    client = OpenAI(api_key=api_key)

    # 2. Load the structured annotations JSON
    input_json_path = "structured_annotations.json"
    if not os.path.exists(input_json_path):
        print(f"🛑 Error: {input_json_path} not found. Make sure you've run the previous script.")
        return
    with open(input_json_path, 'r') as f:
        data = json.load(f)

    # 3. Load the transcription prompt
    prompt_path = "prompt.txt"
    if not os.path.exists(prompt_path):
        print(f"🛑 Error: {prompt_path} not found.")
        return
    with open(prompt_path, 'r') as f:
        transcription_prompt = f.read().strip()
    
    # 4. Iterate through notes and send them for transcription
    total_notes = sum(1 for loc in data for item in data[loc] if item['type'] == 'note')
    processed_count = 0
    MAX_RETRIES = 3

    for loc, items in data.items():
        for item in items:
            if item['type'] == 'note' and 'transcription' not in item:
                processed_count += 1
                image_path = item['image_path']
                
                if not os.path.exists(image_path):
                    print(f"⚠️ Warning: Image not found for Loc {loc}: {image_path}. Skipping.")
                    item['transcription'] = "Error: Image file not found."
                    continue

                print(f"📄 Transcribing note {processed_count}/{total_notes} for Loc {loc}...")

                base64_image = encode_image(image_path)
                
                retries = 0
                transcription_success = False

                while not transcription_success and retries < MAX_RETRIES:
                    try:
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            response_format={"type": "json_object"},
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": transcription_prompt},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{base64_image}"
                                            },
                                        },
                                    ],
                                }
                            ],
                            temperature=0,
                            max_tokens=2048,
                        )
                        
                        response_content = response.choices[0].message.content
                        transcription_data = json.loads(response_content)
                        
                        # Validate the format
                        if validate_json_format(transcription_data):
                            # The API now returns a single object, not a list.
                            # We assign the single object directly.
                            item['transcription'] = transcription_data
                            print(f"  -> ✔️ Success! Note for Loc {loc} transcribed and validated.")
                            transcription_success = True
                        else:
                            retries += 1
                            print(f"  -> ❌ Validation failed. Retrying... (Attempt {retries}/{MAX_RETRIES})")
                            
                    except json.JSONDecodeError as e:
                        retries += 1
                        print(f"  -> ❌ JSON decode error: The API response was not valid JSON. {e}")
                        print(f"  -> Retrying... (Attempt {retries}/{MAX_RETRIES})")
                        item['transcription'] = f"Error: Failed to parse API response as JSON. {e}"
                        
                    except Exception as e:
                        retries += 1
                        print(f"  -> ❌ General API call error: {e}")
                        print(f"  -> Retrying... (Attempt {retries}/{MAX_RETRIES})")
                        item['transcription'] = f"Error: API call failed. {e}"

                if not transcription_success:
                    print(f"  -> 🛑 Failed to transcribe and validate note for Loc {loc} after {MAX_RETRIES} attempts.")
                    item['transcription'] = "Error: Failed after multiple retries."

    # 5. Save the updated data to a new file to avoid overwriting
    output_json_path = "transcribed_annotations.json"
    with open(output_json_path, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"\n✅ Transcription complete! Updated data saved to {output_json_path}")

if __name__ == "__main__":
    transcribe_notes()