import argparse
import logging
import sys

from .processor import ZettelkastenProcessor
from . import exceptions

def setup_logging():
    """Configures logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        stream=sys.stdout,
    )

def main():
    """Main function to run the CLI."""
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="A CLI tool to process reading annotations into a Zettelkasten."
    )
    parser.add_argument("pdf_path", help="Path to the input PDF file with Kindle annotations.")
    parser.add_argument(
        "--title",
        required=True,
        help="Title of the source document (for references in generated notes)."
    )
    
    # Add arguments for running specific steps
    parser.add_argument(
        "--step",
        choices=['all', 'parse', 'transcribe', 'organize', 'generate'],
        default='all',
        help="Run a specific step of the process. 'all' runs the full pipeline."
    )

    args = parser.parse_args()

    try:
        processor = ZettelkastenProcessor(args.pdf_path, document_title=args.title)

        if args.step == 'all':
            processor.run_full_process()
        elif args.step == 'parse':
            processor.run_parser()
            logging.info("✅ Parsing step completed.")
        elif args.step == 'transcribe':
            processor.run_transcriber()
            logging.info("✅ Transcription step completed.")
        elif args.step == 'organize':
            processor.run_organizer()
            logging.info("✅ Organization step completed.")
        elif args.step == 'generate':
            processor.run_note_generator()
            logging.info("✅ Note generation step completed.")
            
    except exceptions.ZettelkastenError as e:
        logging.error(f"An application error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()