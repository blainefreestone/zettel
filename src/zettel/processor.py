import json
import logging
import os
from typing import Dict, Any

from . import config
from .pdf_parser import PDFParser
from .ai_services import AIService
from .note_generator import NoteGenerator

class ZettelkastenProcessor:
    """
    Orchestrates the entire Zettelkasten workflow from PDF to markdown notes.
    """
    def __init__(self, pdf_path: str):
        self._pdf_path = pdf_path
        self._parser = PDFParser(pdf_path, config.PDF_IMAGE_DIR)
        self._ai_service = AIService()
        self._note_generator = NoteGenerator(config.TEMPLATE_DIR)
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)

    def run_full_process(self):
        """Runs the complete workflow from parsing to note generation."""
        logging.info("Starting full Zettelkasten process...")
        structured_data = self.run_parser()
        transcribed_data = self.run_transcriber(structured_data)
        organized_data = self.run_organizer(transcribed_data)
        self.run_note_generator(organized_data, transcribed_data)
        logging.info("✅ Full process completed successfully!")

    def run_parser(self) -> Dict[str, Any]:
        """Runs only the PDF parsing stage."""
        data = self._parser.parse()
        self._save_json(data, config.STRUCTURED_JSON_PATH)
        return data

    def run_transcriber(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Runs only the transcription stage."""
        if data is None:
            data = self._load_json(config.STRUCTURED_JSON_PATH)
        
        transcribed_data = self._ai_service.transcribe_notes(data)
        self._save_json(transcribed_data, config.TRANSCRIBED_JSON_PATH)
        return transcribed_data

    def run_organizer(self, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Runs only the idea organization stage."""
        if data is None:
            data = self._load_json(config.TRANSCRIBED_JSON_PATH)
            
        organized_data = self._ai_service.organize_ideas(data)
        self._save_json(organized_data, config.ORGANIZED_JSON_PATH)
        return organized_data
        
    def run_note_generator(self, organized_data: Dict[str, Any] = None, transcribed_data: Dict[str, Any] = None):
        """Runs only the final note generation stage."""
        if organized_data is None:
            organized_data = self._load_json(config.ORGANIZED_JSON_PATH)
        if transcribed_data is None:
            transcribed_data = self._load_json(config.TRANSCRIBED_JSON_PATH)

        self._note_generator.create_literature_note(
            transcribed_data, config.LITERATURE_NOTE_PATH
        )
        self._note_generator.create_permanent_notes(
            organized_data, transcribed_data, config.PERMANENT_NOTE_DIR
        )

    def _save_json(self, data: Dict, path: str):
        """Saves a dictionary to a JSON file."""
        logging.info(f"Saving data to '{path}'...")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def _load_json(self, path: str) -> Dict[str, Any]:
        """Loads data from a JSON file."""
        logging.info(f"Loading data from '{path}'...")
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Could not load data. File not found: {path}")
            raise