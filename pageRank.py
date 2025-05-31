import sqlite3
import re
import math
from collections import Counter, defaultdict
from typing import Dict, List, Tuple
import os

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 not installed. Install with: pip install PyPDF2")
    exit(1)

class PDFTextAnalyzer:
    def __init__(self, db_path: str = "pdf_database.db"):
        """Initialize the PDF analyzer with SQLite database."""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                word_count INTEGER
            )
        ''')
        
        # Create term frequency table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS term_frequency (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                term TEXT,
                frequency INTEGER,
                tf_score REAL,
                FOREIGN KEY (document_id) REFERENCES documents (id),
                UNIQUE(document_id, term)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text content from a PDF file."""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                
                return text.strip()
        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return ""
    
    def preprocess_text(self, text: str) -> List[str]:
        """Preprocess text by cleaning and tokenizing."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and digits, keep only letters and spaces
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Split into words and remove empty strings
        words = [word.strip() for word in text.split() if word.strip()]
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                     'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were',
                     'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did',
                     'will', 'would', 'could', 'should', 'may', 'might', 'must',
                     'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
                     'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        words = [word for word in words if word not in stop_words and len(word) > 2]
        
        return words
    
    def calculate_term_frequency(self, words: List[str]) -> Dict[str, float]:
        """Calculate term frequency (TF) for words."""
        word_count = Counter(words)
        total_words = len(words)
        
        tf_scores = {}
        for word, count in word_count.items():
            tf_scores[word] = count / total_words
        
        return tf_scores
    
    def process_pdf(self, pdf_path: str) -> bool:
        """Process a PDF file and store its content and term frequencies in the database."""
        if not os.path.exists(pdf_path):
            print(f"File {pdf_path} does not exist.")
            return False
        
        filename = os.path.basename(pdf_path)
        print(f"Processing {filename}...")
        
        # Extract text
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            print(f"No text extracted from {filename}")
            return False
        
        # Preprocess text
        words = self.preprocess_text(text)
        if not words:
            print(f"No valid words found in {filename}")
            return False
        
        # Calculate term frequencies
        tf_scores = self.calculate_term_frequency(words)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Insert document
            cursor.execute('''
                INSERT OR REPLACE INTO documents (filename, content, word_count)
                VALUES (?, ?, ?)
            ''', (filename, text, len(words)))
            
            document_id = cursor.lastrowid
            
            # Delete existing term frequencies for this document
            cursor.execute('DELETE FROM term_frequency WHERE document_id = ?', (document_id,))
            
            # Insert term frequencies
            for term, tf_score in tf_scores.items():
                frequency = Counter(words)[term]
                cursor.execute('''
                    INSERT INTO term_frequency (document_id, term, frequency, tf_score)
                    VALUES (?, ?, ?, ?)
                ''', (document_id, term, frequency, tf_score))
            
            conn.commit()
            print(f"Successfully processed {filename} with {len(tf_scores)} unique terms")
            return True
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def calculate_idf(self) -> Dict[str, float]:
        """Calculate Inverse Document Frequency (IDF) for all terms."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total number of documents
        cursor.execute('SELECT COUNT(*) FROM documents')
        total_docs = cursor.fetchone()[0]
        
        if total_docs == 0:
            return {}
        
        # Get document frequency for each term
        cursor.execute('''
            SELECT term, COUNT(DISTINCT document_id) as doc_freq
            FROM term_frequency
            GROUP BY term
        ''')
        
        idf_scores = {}
        for term, doc_freq in cursor.fetchall():
            idf_scores[term] = math.log(total_docs / doc_freq)
        
        conn.close()
        return idf_scores
    
    def search(self, query: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Search for documents most relevant to the query using TF-IDF scoring."""
        # Preprocess query
        query_words = self.preprocess_text(query)
        if not query_words:
            print("No valid search terms found in query")
            return []
        
        # Calculate IDF scores
        idf_scores = self.calculate_idf()
        
        # Calculate TF-IDF scores for each document
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all documents
        cursor.execute('SELECT id, filename FROM documents')
        documents = cursor.fetchall()
        
        doc_scores = {}
        
        for doc_id, filename in documents:
            score = 0.0
            
            for term in query_words:
                # Get TF score for this term in this document
                cursor.execute('''
                    SELECT tf_score FROM term_frequency
                    WHERE document_id = ? AND term = ?
                ''', (doc_id, term))
                
                result = cursor.fetchone()
                if result and term in idf_scores:
                    tf_score = result[0]
                    idf_score = idf_scores[term]
                    tfidf_score = tf_score * idf_score
                    score += tfidf_score
            
            if score > 0:
                doc_scores[filename] = score
        
        conn.close()
        
        # Sort by score and return top N
        sorted_results = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_n]
    
    def list_documents(self):
        """List all documents in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT filename, word_count FROM documents ORDER BY filename')
        documents = cursor.fetchall()
        
        if documents:
            print("\nDocuments in database:")
            print("-" * 50)
            for filename, word_count in documents:
                print(f"{filename} ({word_count} words)")
        else:
            print("No documents in database")
        
        conn.close()
    
    def get_document_stats(self, filename: str):
        """Get statistics for a specific document."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT d.content, d.word_count, COUNT(tf.term) as unique_terms
            FROM documents d
            LEFT JOIN term_frequency tf ON d.id = tf.document_id
            WHERE d.filename = ?
            GROUP BY d.id
        ''', (filename,))
        
        result = cursor.fetchone()
        if result:
            content, word_count, unique_terms = result
            print(f"\nDocument: {filename}")
            print(f"Total words: {word_count}")
            print(f"Unique terms: {unique_terms}")
            print(f"Content preview: {content[:200]}...")
            
            # Get top 10 most frequent terms
            cursor.execute('''
                SELECT term, frequency, tf_score
                FROM term_frequency tf
                JOIN documents d ON tf.document_id = d.id
                WHERE d.filename = ?
                ORDER BY frequency DESC
                LIMIT 10
            ''', (filename,))
            
            print("\nTop 10 most frequent terms:")
            for term, freq, tf_score in cursor.fetchall():
                print(f"  {term}: {freq} times (TF: {tf_score:.4f})")
        else:
            print(f"Document '{filename}' not found in database")
        
        conn.close()


def main():
    """Main function to run the PDF analyzer."""
    analyzer = PDFTextAnalyzer()
    
    print("PDF Text Analyzer with Term Frequency Database")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Process a PDF file")
        print("2. Search documents")
        print("3. List all documents")
        print("4. Get document statistics")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            pdf_path = input("Enter the path to the PDF file: ").strip()
            analyzer.process_pdf(pdf_path)
        
        elif choice == '2':
            query = input("Enter your search query: ").strip()
            if query:
                results = analyzer.search(query)
                if results:
                    print(f"\nTop 10 matching documents for '{query}':")
                    print("-" * 60)
                    for i, (filename, score) in enumerate(results, 1):
                        print(f"{i:2d}. {filename} (Score: {score:.4f})")
                else:
                    print("No matching documents found.")
            else:
                print("Please enter a valid search query.")
        
        elif choice == '3':
            analyzer.list_documents()
        
        elif choice == '4':
            filename = input("Enter the filename: ").strip()
            analyzer.get_document_stats(filename)
        
        elif choice == '5':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1-5.")


if __name__ == "__main__":
    main()