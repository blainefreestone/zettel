import base64
import json
import logging
import os
from typing import Dict, Any

from openai import OpenAI, APIConnectionError as OpenAIAPIError, APIStatusError

from . import config, exceptions

class AIService:
    """
    Handles AI-powered transcription and organization using pre-configured OpenAI prompts.
    """
    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise exceptions.ZettelkastenError("OPENAI_API_KEY not found in environment.")
        self._client = OpenAI(api_key=config.OPENAI_API_KEY)

    def transcribe_notes(self, annotations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Iterates through annotations, transcribes notes using a configured prompt,
        and returns the updated data.
        """
        notes_to_process = [
            (loc, item)
            for loc, items in annotations.items()
            for item in items
            if item.get('type') == 'note' and 'transcription' not in item
        ]
        
        total_notes = len(notes_to_process)
        logging.info(f"Found {total_notes} notes to transcribe.")

        for i, (loc, item) in enumerate(notes_to_process, 1):
            logging.info(f"Transcribing note {i}/{total_notes} for Loc {loc}...")
            image_path = item['image_path']

            if not os.path.exists(image_path):
                logging.warning(f"Image not found for Loc {loc}: {image_path}. Skipping.")
                item['transcription'] = {"error": "Image file not found."}
                continue
            
            base64_image = self._encode_image(image_path)
            
            for attempt in range(config.MAX_RETRIES):
                try:
                    response = self._client.responses.create(
                        prompt={"id": config.TRANSCRIPTION_PROMPT_ID},
                        input=[{
                            "role": "user",
                            "content": [{
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{base64_image}",
                            }],
                        }]
                    )
                    
                    response_content = response.output[0].content[0].text
                    transcription_data = json.loads(response_content)
                    item['transcription'] = transcription_data
                    logging.info(f"  -> Successfully transcribed note for Loc {loc}.")
                    break  # Success
                except (OpenAIAPIError, APIStatusError, json.JSONDecodeError) as e:
                    logging.warning(f"  -> Attempt {attempt + 1}/{config.MAX_RETRIES} failed: {e}")
                    if attempt + 1 == config.MAX_RETRIES:
                        logging.error(f"Failed to transcribe note for Loc {loc} after {config.MAX_RETRIES} attempts.")
                        item['transcription'] = {"error": f"Failed after multiple retries. Last error: {e}"}
        
        return annotations

    def organize_ideas(self, transcribed_annotations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends transcribed annotations to a configured prompt to identify and link core ideas.
        """
        logging.info("Organizing ideas using pre-configured AI prompt...")
        
        try:
            response = self._client.responses.create(
                prompt={
                    "id": config.ORGANIZATION_PROMPT_ID,
                    "variables": {
                        "transcribed_annotations": json.dumps(transcribed_annotations)
                    }
                }
            )
            
            response_text = response.output[0].content[0].text
            organized_data = json.loads(response_text)
            logging.info("Successfully organized ideas.")
            return organized_data
        except (OpenAIAPIError, APIStatusError) as e:
            raise exceptions.APIConnectionError(f"Failed to connect to OpenAI API: {e}")
        except json.JSONDecodeError as e:
            raise exceptions.JSONParsingError(f"Failed to parse AI response as JSON: {e}")

    def _encode_image(self, image_path: str) -> str:
        """Encodes an image file to a base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')