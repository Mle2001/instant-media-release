"""
Document Processing Module for Instant Media Release
Handles PDF/DOC processing using Agno AI framework
"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

import fitz  # PyMuPDF
from docx import Document
from loguru import logger

from agno.knowledge.pdf import PDFKnowledgeBase
from agno.knowledge.docx import DocxKnowledgeBase
from agno.document.reader.pdf_reader import PDFReader as AgnoPDFReader
from agno.document.chunking.recursive import RecursiveChunking
from agno.embedder.openai import OpenAIEmbedder
from agno.vectordb.chroma import ChromaDb
from agno.document import Document as AgnoDocument

# Configuration
UPLOAD_DIR = "./uploads"
PROCESSED_DIR = "./processed_documents"
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB
SUPPORTED_EXTENSIONS = {".pdf", ".doc", ".docx"}

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


class DocumentProcessor:
    """Enhanced document processor using Agno AI capabilities"""

    def __init__(self, openai_api_key: str):
        """Initialize with OpenAI API key for embeddings"""
        self.openai_api_key = openai_api_key
        self.embedder = OpenAIEmbedder(
            api_key=openai_api_key, id="text-embedding-3-small", dimensions=1536
        )

        # Setup document vector database
        self.doc_vector_db = ChromaDb(
            collection="user_documents", path="./chroma_db_docs", embedder=self.embedder
        )

        if hasattr(self.doc_vector_db, "collection"):
            logger.info(f"📌 collection exists: {self.doc_vector_db.collection}")
            logger.info(f"📦 collection count: {self.doc_vector_db.collection.count()}")
        else:
            logger.warning("⚠️ doc_vector_db.collection NOT found")

        logger.info("✅ Document processor initialized")

    async def process_uploaded_file(
        self, file_content: bytes, filename: str, session_id: str
    ) -> Dict[str, Any]:
        """Process uploaded file and extract content"""

        try:
            # Validate file
            validation_result = self._validate_file(file_content, filename)
            if not validation_result["valid"]:
                return validation_result

            # Save file temporarily
            file_path = await self._save_temp_file(file_content, filename, session_id)

            # Extract content based on file type
            extension = Path(filename).suffix.lower()

            if extension == ".pdf":
                content_data = await self._process_pdf(file_path, session_id)
            elif extension in [".doc", ".docx"]:
                content_data = await self._process_docx(file_path, session_id)
            else:
                return {"success": False, "error": "Unsupported file format"}

            # Create embeddings and store in vector DB
            if content_data["success"]:
                await self._create_document_embeddings(
                    content_data["content"], filename, session_id
                )

            # Cleanup temporary file
            if os.path.exists(file_path):
                os.remove(file_path)

            logger.info(f"✅ Processed document: {filename}")
            return content_data

        except Exception as e:
            logger.error(f"❌ Error processing document {filename}: {e}")
            return {"success": False, "error": f"Processing failed: {str(e)}"}

    def _validate_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded file"""

        # Check file size
        if len(file_content) > MAX_FILE_SIZE:
            return {
                "success": False,
                "error": f"File too large. Max size: {MAX_FILE_SIZE // (1024*1024)}MB",
            }

        # Check file extension
        extension = Path(filename).suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            return {
                "success": False,
                "error": f"Unsupported format. Supported: {', '.join(SUPPORTED_EXTENSIONS)}",
            }

        # Check if file is empty
        if len(file_content) == 0:
            return {"success": False, "error": "Empty file"}

        return {"valid": True}

    async def _save_temp_file(
        self, file_content: bytes, filename: str, session_id: str
    ) -> str:
        """Save file temporarily for processing"""

        # Create unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{session_id}_{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)

        # Write file
        with open(file_path, "wb") as f:
            f.write(file_content)

        return file_path

    async def _process_pdf(self, file_path: str, session_id: str) -> Dict[str, Any]:
        """Process PDF using Agno PDFReader and PyMuPDF"""

        try:
            # Method 1: Use Agno PDFKnowledgeBase for advanced processing
            try:
                knowledge_base = PDFKnowledgeBase(
                    path=os.path.dirname(file_path),
                    reader=AgnoPDFReader(chunk=True),
                    chunking_strategy=RecursiveChunking(chunk_size=2000, overlap=200),
                    vector_db=self.doc_vector_db,
                )

                # Load documents
                knowledge_base.load(recreate=False)

                # Extract text from knowledge base
                content_chunks = []
                for doc_list in knowledge_base.document_lists:
                    for doc in doc_list:
                        content_chunks.append(doc.content)

                if content_chunks:
                    full_content = "\n\n".join(content_chunks)
                    return {
                        "success": True,
                        "content": full_content,
                        "chunks": content_chunks,
                        "method": "agno_knowledge_base",
                        "pages": len(content_chunks),
                    }

            except Exception as agno_error:
                logger.warning(f"Agno processing failed: {agno_error}, trying PyMuPDF")

            # Method 2: Fallback to PyMuPDF direct processing
            doc = fitz.open(file_path)
            pages_content = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()

                if text.strip():  # Only add non-empty pages
                    pages_content.append(
                        {"page": page_num + 1, "content": text.strip()}
                    )

            doc.close()

            if not pages_content:
                return {"success": False, "error": "No text content found in PDF"}

            # Combine all page content
            full_content = "\n\n".join([p["content"] for p in pages_content])

            return {
                "success": True,
                "content": full_content,
                "pages": len(pages_content),
                "method": "pymupdf_direct",
                "page_details": pages_content,
            }

        except Exception as e:
            return {"success": False, "error": f"PDF processing failed: {str(e)}"}

    async def _process_docx(self, file_path: str, session_id: str) -> Dict[str, Any]:
        """Process DOCX using python-docx and Agno"""

        try:
            # Method 1: Try Agno DocxKnowledgeBase (if available)
            try:
                knowledge_base = DocxKnowledgeBase(
                    path=os.path.dirname(file_path), vector_db=self.doc_vector_db
                )

                knowledge_base.load(recreate=False)

                # Extract content
                content_chunks = []
                for doc_list in knowledge_base.document_lists:
                    for doc in doc_list:
                        content_chunks.append(doc.content)

                if content_chunks:
                    full_content = "\n\n".join(content_chunks)
                    return {
                        "success": True,
                        "content": full_content,
                        "chunks": content_chunks,
                        "method": "agno_knowledge_base",
                    }

            except Exception as agno_error:
                logger.warning(
                    f"Agno DOCX processing failed: {agno_error}, trying python-docx"
                )

            # Method 2: Fallback to python-docx direct processing
            doc = Document(file_path)
            paragraphs = []

            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:  # Only add non-empty paragraphs
                    paragraphs.append(text)

            if not paragraphs:
                return {"success": False, "error": "No text content found in DOCX"}

            full_content = "\n\n".join(paragraphs)

            return {
                "success": True,
                "content": full_content,
                "paragraphs": len(paragraphs),
                "method": "python_docx_direct",
            }

        except Exception as e:
            return {"success": False, "error": f"DOCX processing failed: {str(e)}"}

    async def _create_document_embeddings(
        self, content: str, filename: str, session_id: str
    ):
        """Create embeddings for document content"""

        try:
            chunk_size = 1000
            now = datetime.utcnow().isoformat()

            documents = []
            for i in range(0, len(content), chunk_size):
                chunk = content[i : i + chunk_size]
                doc_id = f"{session_id}_{filename}_{i}"
                metadata = {
                    "filename": filename,
                    "session_id": session_id,
                    "chunk_index": i,
                    "created_at": now,
                }
                documents.append(
                    AgnoDocument(id=doc_id, content=chunk, meta_data=metadata)
                )

            self.doc_vector_db.insert(documents)

            logger.info(
                f"✅ Created embeddings for {len(documents)} chunks from {filename}"
            )

        except Exception as e:
            logger.error(f"❌ Failed to create embeddings: {e}")

    async def search_user_documents(
        self, query: str, session_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Search user's uploaded documents"""

        try:
            # Fix: ChromaDB search without 'where' parameter
            # Use get() instead for filtering by metadata
            all_results = self.doc_vector_db.search(
                query=query, limit=limit * 3  # Get more to filter later
            )

            # Manual filtering by session_id
            filtered_results = []
            for result in all_results:
                if result.get("metadata", {}).get("session_id") == session_id:
                    filtered_results.append(result)
                    if len(filtered_results) >= limit:
                        break

            return filtered_results

        except Exception as e:
            logger.error(f"❌ Document search failed: {e}")
            return []

    def get_session_documents(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all documents for a session"""

        try:
            # Fix: Use collection.get() instead of search() for metadata filtering
            if hasattr(self.doc_vector_db, "collection"):
                collection = self.doc_vector_db.collection
                # Get all documents and filter manually
                all_docs = collection.get()

                # Filter by session_id
                session_docs = {}
                if all_docs and "metadatas" in all_docs:
                    for i, metadata in enumerate(all_docs["metadatas"]):
                        if metadata.get("session_id") == session_id:
                            filename = metadata.get("filename")
                            if filename not in session_docs:
                                session_docs[filename] = {
                                    "filename": filename,
                                    "chunks": 0,
                                    "created_at": metadata.get("created_at"),
                                }
                            session_docs[filename]["chunks"] += 1

                return list(session_docs.values())
            else:
                # Fallback: return empty list
                logger.warning("ChromaDB collection not accessible")
                return []

        except Exception as e:
            logger.error(f"❌ Failed to get session documents: {e}")
            return []


# Global instance
document_processor: Optional[DocumentProcessor] = None


def get_document_processor() -> Optional[DocumentProcessor]:
    """Get global document processor instance"""
    return document_processor


def init_document_processor(openai_api_key: str):
    """Initialize global document processor"""
    global document_processor
    try:
        document_processor = DocumentProcessor(openai_api_key)
        logger.info("✅ Global document processor initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize document processor: {e}")
        return False
