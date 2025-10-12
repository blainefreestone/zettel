import json
import logging
import os
from typing import Dict, Any

from jinja2 import Environment, FileSystemLoader

from . import config, exceptions

class NoteGenerator:
    """
    Generates markdown notes from structured data using Jinja2 templates.
    """
    def __init__(self, template_dir: str):
        if not os.path.isdir(template_dir):
            raise exceptions.FileNotFoundError(f"Template directory not found: {template_dir}")
        self._env = Environment(loader=FileSystemLoader(template_dir))

    def create_literature_note(self, transcribed_data: Dict[str, Any], output_path: str):
        """
        Generates a single literature note summarizing highlights and summaries.
        """
        logging.info("Generating literature note...")
        try:
            template = self._env.get_template('literature_template.md')
            
            filtered_data = {}
            for loc, items in transcribed_data.items():
                filtered_items = [
                    item for item in items
                    if item.get('type') == 'highlight' or
                    (item.get('type') == 'note' and item.get('transcription', {}).get('type') == 'summary')
                ]
                if filtered_items:
                    filtered_data[loc] = filtered_items

            markdown_output = template.render(data=filtered_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown_output)
            
            logging.info(f"Literature note saved to '{output_path}'.")

        except Exception as e:
            raise exceptions.ZettelkastenError(f"Failed to generate literature note: {e}")

    def create_permanent_notes(
            self,
            organized_data: Dict[str, Any],
            transcribed_data: Dict[str, Any],
            output_dir: str
        ):
            """
            Generates individual markdown files for each permanent idea (Zettel).
            """
            logging.info("Generating permanent notes...")
            os.makedirs(output_dir, exist_ok=True)
            
            try:
                template = self._env.get_template('permanent_template.md')
                ideas = organized_data.get('ideas', [])
                
                if not ideas:
                    logging.warning("No ideas found in organized data. Skipping permanent note generation.")
                    return

                notes_generated_count = 0
                for i, idea in enumerate(ideas):
                    idea_loc = str(idea.get('idea_location'))
                    idea_idx = int(idea.get('idea_index'))
                    idea_content = None # Initialize content as None
                    
                    try:
                        # First, get the item (which could be a note or a highlight)
                        item = transcribed_data[idea_loc][idea_idx]

                        idea_content = item['transcription']['items'][0]['transcription']

                        if idea_content:
                            notes_generated_count += 1
                        else:
                            logging.warning(f"Found item at Loc {idea_loc}, index {idea_idx}, but it has an unknown type or no content. Skipping.")
                            continue

                    except (KeyError, IndexError, TypeError):
                        logging.error(f"Could not find item or content at Loc {idea_loc}, index {idea_idx}. Skipping.")
                        continue

                    linked_locations = [link['ref_location'] for link in idea.get('links', [])]

                    markdown_output = template.render(
                        content=idea_content,
                        locations=linked_locations
                    )

                    filename = f"idea_{i + 1:03d}.md"
                    filepath = os.path.join(output_dir, filename)

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(markdown_output)
                
                logging.info(f"{notes_generated_count} permanent notes generated in '{output_dir}'.")
            
            except Exception as e:
                raise exceptions.ZettelkastenError(f"Failed to generate permanent notes: {e}")