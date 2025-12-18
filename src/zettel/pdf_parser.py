import fitz  # PyMuPDF
import os
import hashlib
import re
import json
import logging
from typing import Dict, Any, List

from . import exceptions

class PDFParser:
    """
    Parses a Kindle-exported PDF to extract highlights, notes, and images.
    """
    def __init__(self, pdf_path: str, image_dir: str):
        if not os.path.exists(pdf_path):
            raise exceptions.FileNotFoundError(f"PDF file not found at: {pdf_path}")
        self._pdf_path = pdf_path
        self._image_dir = image_dir
        self._doc = fitz.open(self._pdf_path)
    
    def get_title(self) -> str:
        """
        Extracts the document title from PDF metadata.
        Falls back to filename without extension if no title is found.
        """
        metadata = self._doc.metadata
        title = metadata.get('title', '') if metadata else ''
        
        if not title or title.strip() == '':
            # Fall back to filename without extension
            title = os.path.splitext(os.path.basename(self._pdf_path))[0]
        
        return title.strip()

    def parse(self) -> Dict[str, Any]:
        """
        Executes the full parsing workflow: extract images and text, then structure them.
        
        Returns:
            A dictionary containing the structured annotation data.
        """
        logging.info(f"Starting parsing process for '{self._pdf_path}'...")
        os.makedirs(self._image_dir, exist_ok=True)
        
        self._clear_directory(self._image_dir)
        image_paths = self._extract_unique_images()
        raw_text = self._extract_text()
        structured_data = self._create_structured_data(raw_text, image_paths)
        
        logging.info("PDF parsing completed successfully.")
        return structured_data

    def _clear_directory(self, directory: str):
        """Removes all files from a directory."""
        logging.debug(f"Clearing old files from '{directory}'...")
        for file in os.listdir(directory):
            os.remove(os.path.join(directory, file))

    def _extract_text(self) -> str:
        """Extracts all text content from the PDF document."""
        logging.info("Extracting text from PDF...")
        full_text = ""
        for page in self._doc:
            full_text += page.get_text("text") + "\n\n"
        logging.info("Text extraction complete.")
        return full_text

    def _extract_unique_images(self) -> List[str]:
        """
        Extracts unique images from the PDF, saves them sequentially, and returns their paths.
        """
        logging.info("Extracting unique images from PDF...")
        seen_hashes = set()
        note_counter = 1
        image_paths = []

        for page in self._doc:
            for img in page.get_images(full=True):
                xref = img[0]
                base_image = self._doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_hash = hashlib.sha256(image_bytes).hexdigest()

                if image_hash in seen_hashes:
                    continue

                seen_hashes.add(image_hash)
                
                # Skip the first unique image, which is usually the Kindle logo
                if len(seen_hashes) == 1:
                    logging.debug("Skipping first unique image (likely Kindle logo).")
                    continue

                image_ext = base_image["ext"]
                image_filename = f"note_{note_counter:03d}.{image_ext}"
                output_path = os.path.join(self._image_dir, image_filename)
                
                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                
                image_paths.append(output_path)
                note_counter += 1
        
        logging.info(f"Extracted {len(image_paths)} unique note images.")
        return image_paths

    def _create_structured_data(self, raw_text: str, image_paths: List[str]) -> Dict[str, Any]:
        """
        Parses raw text and combines it with image paths to create structured JSON.
        """
        logging.info("Structuring extracted text and images...")
        lines = raw_text.splitlines()
        data: Dict[str, List[Dict[str, Any]]] = {}
        image_index = 0
        last_loc = None
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Match either "Loc #" or "Page #" format
            loc_match = re.match(r'(?:Loc|Page) (\d+)', line)
            if loc_match:
                current_loc = loc_match.group(1)
                last_loc = current_loc
                if current_loc not in data:
                    data[current_loc] = []
                
                content_lines = []
                note_found = False
                i += 1
                # Continue until we hit another location/page marker
                while i < len(lines) and not re.match(r'(?:Loc|Page) \d+', lines[i].strip()):
                    stripped_line = lines[i].strip()
                    if stripped_line == "Note:":
                        note_found = True
                    else:
                        content_lines.append(stripped_line)
                    i += 1
                
                content = " ".join(content_lines).strip()
                # Clean up trailing page numbers often found in Kindle highlights
                clean_content = re.sub(r'\s+\d+$', '', content)

                if "Highlight" in line:
                    if "Continued" in line:
                        # Find the last highlight for this location and append to it
                        for item in reversed(data[current_loc]):
                            if item['type'] == 'highlight':
                                item['content'] += ' ' + clean_content
                                break
                    else:
                        data[current_loc].append({"type": "highlight", "content": clean_content})

                if "Note" in line or note_found:
                    if image_index < len(image_paths):
                        data[current_loc].append({"type": "note", "image_path": image_paths[image_index]})
                        image_index += 1
                    else:
                        logging.warning(f"Found a note at Loc {current_loc} but no corresponding image.")
                continue

            i += 1
            
        logging.info("Successfully created structured data.")
        return data

    def __del__(self):
        """Ensures the PDF document is closed when the object is destroyed."""
        if hasattr(self, '_doc') and self._doc:
            self._doc.close()