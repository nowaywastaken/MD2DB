import os
from typing import Dict, Any
from multiprocessing import Pool
from pymongo import MongoClient
from .chunker import FileChunker
from .worker import parse_chunk
from ..mongodb.writer import BatchWriter
from ..mongodb.deduplicator import Deduplicator
from ..mongodb.models import QuestionDocument, ImageDocument, LatexDocument, OptionDocument


class ParallelProcessor:
    """Coordinates parallel processing of large markdown files."""

    def __init__(
        self,
        file_path: str,
        database_uri: str = "mongodb://localhost:27017",
        database_name: str = "md2db",
        num_workers: int = 4,
        chunk_size_mb: float = 10,
        batch_size: int = 1000
    ):
        self.file_path = file_path
        self.database_uri = database_uri
        self.database_name = database_name
        self.num_workers = num_workers
        self.chunk_size_mb = chunk_size_mb
        self.batch_size = batch_size

    def process(self) -> Dict[str, Any]:
        """Process the file with parallel workers.

        Returns:
            Dict with processing statistics
        """
        # Create MongoDB connection
        client = MongoClient(self.database_uri)
        db = client[self.database_name]

        try:
            # Create chunks
            chunker = FileChunker(self.file_path, self.chunk_size_mb)
            chunks = chunker.create_chunks()

            # Setup writer and deduplicator
            deduplicator = Deduplicator(db)
            writer = BatchWriter(db, self.batch_size, deduplicator)

            # Process chunks in parallel
            questions_processed = 0

            with open(self.file_path, 'r', encoding='utf-8') as f:
                with Pool(self.num_workers) as pool:
                    # Read chunks and process in parallel
                    chunk_contents = []
                    for start, end in chunks:
                        f.seek(start)
                        content = f.read(end - start)
                        chunk_contents.append(content)

                    # Process all chunks
                    results = pool.map(parse_chunk, chunk_contents)

                    # Write results with deduplication
                    for chunk_results in results:
                        for doc_dict in chunk_results:
                            # Process images
                            image_ids = []
                            for img_url in doc_dict.get("images", []):
                                img_doc = ImageDocument(url=img_url)
                                img_id = deduplicator.get_or_create_image(img_doc)
                                if img_id:
                                    image_ids.append(img_id)

                            # Process latex
                            latex_ids = []
                            for formula in doc_dict.get("latex_formulas", []):
                                latex_doc = LatexDocument(formula=formula)
                                latex_id = deduplicator.get_or_create_latex(latex_doc)
                                if latex_id:
                                    latex_ids.append(latex_id)

                            # Process options
                            option_ids = []
                            for i, opt_content in enumerate(doc_dict.get("options", [])):
                                label = chr(65 + i)  # A, B, C, ...
                                opt_doc = OptionDocument(label=label, content=opt_content)
                                opt_id = deduplicator.get_or_create_option(opt_doc)
                                if opt_id:
                                    option_ids.append(opt_id)

                            # Create question document
                            question_doc = QuestionDocument(
                                content=doc_dict["content"],
                                question_type=doc_dict["question_type"],
                                options=option_ids,
                                answer=doc_dict.get("answer"),
                                explanation=doc_dict.get("explanation"),
                                images=image_ids,
                                latex_formulas=latex_ids
                            )
                            writer.add(question_doc)
                            questions_processed += 1

            # Final flush
            writer.flush()

            return {
                "questions_processed": questions_processed,
                "chunks_processed": len(chunks),
                "num_workers": self.num_workers
            }
        finally:
            client.close()
