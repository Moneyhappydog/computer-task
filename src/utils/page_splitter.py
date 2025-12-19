import os
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PageSplitter:
    def __init__(self):
        pass

    def split_markdown(self, file_path: str, output_dir: str = None):
        """
        Splits a markdown file into pages based on the delimiter '\n---\n'.
        
        Args:
            file_path: Path to the input markdown file.
            output_dir: Directory to save the split pages. If None, creates a 'pages' subdir in the file's directory.
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"File not found: {file_path}")
            return

        if output_dir is None:
            # Create 'pages' directory at the same level as the parent directory (e.g. sibling of layer1)
            output_dir = path.parent.parent / "pages"
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Reading file: {file_path}")
        try:
            content = path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return

        # Split by the delimiter
        # The delimiter is typically \n---\n
        pages = content.split('\n---\n')
        
        logger.info(f"Found {len(pages)} pages.")
        
        for i, page_content in enumerate(pages):
            page_num = i + 1
            # Naming format: page_{page_num}.md to be consistent with other layer files
            page_filename = f"page_{page_num}.md"
            page_file_path = output_path / page_filename
            
            # Write content
            page_file_path.write_text(page_content.strip(), encoding='utf-8')
            logger.info(f"Saved page {page_num} to {page_file_path}")

if __name__ == "__main__":
    splitter = PageSplitter()
    # Target file from user request
    target_file = r"e:\A-coding\pdf_dita\data\output\2023CVPR-CoMFormer\layer1\2023CVPR-CoMFormer.md"
    splitter.split_markdown(target_file)
