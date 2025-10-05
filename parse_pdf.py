import fitz
import re
import json
import os
import hashlib

def process_kindle_pdf(pdf_path, text_output_filename="raw_kindle_text.txt", image_output_folder="extracted_unique_images"):
    """
    Extracts raw text and renames images sequentially from a Kindle PDF.
    """
    # --- Part 1: Text Extraction ---
    try:
        doc = fitz.open(pdf_path)
        print(f"Opened PDF: {pdf_path}")

        full_text = ""
        for page in doc:
            full_text += page.get_text("text") + "\n\n"

        with open(text_output_filename, "w", encoding="utf-8") as outfile:
            outfile.write(full_text)
            
        print(f"Text extraction successful! Raw text saved to: {text_output_filename}")
    
    except FileNotFoundError:
        print(f"Error: The file '{pdf_path}' was not found.")
        return
    except Exception as e:
        print(f"An error occurred during text extraction: {e}")
        return
    
    # --- Part 2: Image Extraction and Sequential Renaming ---
    if not os.path.exists(image_output_folder):
        os.makedirs(image_output_folder)
        print(f"\nCreated output folder: {image_output_folder}")

    try:
        # Counters for sequential renaming
        unique_image_count = 0
        note_counter = 1
        seen_hashes = set()

        # Iterate through pages in order to extract images chronologically
        for page_index, page in enumerate(doc):
            image_list = page.get_images(full=True)
            
            for image_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                
                image_bytes = base_image["image"]
                image_hash = hashlib.sha256(image_bytes).hexdigest()

                if image_hash in seen_hashes:
                    continue

                seen_hashes.add(image_hash)
                unique_image_count += 1
                
                image_ext = base_image["ext"]
                
                # The first unique image found is the Kindle logo.
                if unique_image_count == 1:
                    image_filename = f"kindle_logo.{image_ext}"
                else:
                    # Subsequent images are notes and are named sequentially.
                    image_filename = f"note_{note_counter:03d}.{image_ext}"
                    note_counter += 1

                output_path = os.path.join(image_output_folder, image_filename)
                
                with open(output_path, "wb") as image_file:
                    image_file.write(image_bytes)
                
                print(f"  -> Saved unique image: {output_path}")
                
        print("\nPDF processing complete.")
        print(f"Total unique images extracted: {unique_image_count}")
    
    except Exception as e:
        print(f"An error occurred during image extraction: {e}")
    finally:
        if 'doc' in locals() and doc:
            doc.close()

def create_structured_data(text_file, image_folder):
    """
    Parses the raw text from Kindle annotations and creates a structured dictionary.
    """
    with open(text_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Sort the sequentially named image files.
    all_images = sorted([os.path.join(image_folder, img) for img in os.listdir(image_folder)])
    
    # Exclude the kindle logo from the list of notes to be processed.
    image_files = [img for img in all_images if 'kindle_logo' not in img]
    image_index = 0
    
    data = {}
    last_loc = None
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
            
        loc_match = re.match(r'Loc (\d+)', line)
        if loc_match:
            current_loc = loc_match.group(1)
            last_loc = current_loc
            if current_loc not in data:
                data[current_loc] = []
            
            if "Highlight Continued" in line:
                i += 1
                content = ""
                note_found_in_continued = False
                while i < len(lines) and not re.match(r'Loc \d+', lines[i].strip()):
                    if lines[i].strip() == "Note:":
                        note_found_in_continued = True
                    else:
                        content += lines[i].strip() + " "
                    i += 1
                
                # Clean up the content by removing trailing numbers
                clean_content = re.sub(r'\s+\d+$', '', content.strip())

                for item in reversed(data[current_loc]):
                    if item['type'] == 'highlight':
                        item['content'] += ' ' + clean_content
                        break
                
                if note_found_in_continued:
                    if image_index < len(image_files):
                        data[current_loc].append({"type": "note", "image_path": image_files[image_index]})
                        image_index += 1
                continue
            
            elif "Highlight" in line:
                i += 1
                content = ""
                note_found_in_content = False
                while i < len(lines) and not re.match(r'Loc \d+', lines[i].strip()):
                    if lines[i].strip() == "Note:":
                        note_found_in_content = True
                    else:
                        content += lines[i].strip() + " "
                    i += 1

                # Clean up the content by removing trailing numbers
                clean_content = re.sub(r'\s+\d+$', '', content.strip())
                    
                data[current_loc].append({"type": "highlight", "content": clean_content})
                
                if note_found_in_content:
                    if image_index < len(image_files):
                        data[current_loc].append({"type": "note", "image_path": image_files[image_index]})
                        image_index += 1
                continue

            elif "Note" in line:
                if image_index < len(image_files):
                    data[current_loc].append({"type": "note", "image_path": image_files[image_index]})
                    image_index += 1
                i += 1
                continue
        
        elif line == "Note:":
             if last_loc and image_index < len(image_files):
                data[last_loc].append({"type": "note", "image_path": image_files[image_index]})
                image_index += 1
            
        i += 1
        
    with open("structured_annotations.json", "w") as f:
        json.dump(data, f, indent=4)
        
    print("\n✅ Structured data created successfully!")
    print(" -> Saved to: structured_annotations.json")


# --- Main Execution ---
if __name__ == "__main__":
    pdf_file_path = "pdf.pdf"
    text_output_filename="raw_kindle_text.txt"
    image_output_folder="extracted_unique_images"
    
    # It's a good idea to clear out old images before running
    if os.path.exists(image_output_folder):
        for file in os.listdir(image_output_folder):
            os.remove(os.path.join(image_output_folder, file))

    process_kindle_pdf(pdf_file_path, text_output_filename, image_output_folder)
    create_structured_data(text_output_filename, image_output_folder)