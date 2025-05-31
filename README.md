# PDF Text Analyzer with Term Frequency Database

A Python application that extracts text from PDF files, calculates term frequencies, stores the data in a SQLite database, and provides search functionality to find the most relevant documents based on user queries.

## Features

- **PDF Text Extraction**: Extract text content from PDF files using PyPDF2
- **Text Preprocessing**: Clean and tokenize text, remove stop words
- **Term Frequency Calculation**: Calculate TF (Term Frequency) scores for each document
- **TF-IDF Search**: Use TF-IDF (Term Frequency-Inverse Document Frequency) for relevance scoring
- **SQLite Database**: Store document content and term frequencies in a local database
- **Interactive Search**: Find the top 10 most relevant documents for any search query
- **Document Management**: List documents and view statistics

## Installation

1. Install the required dependency:
```bash
pip install PyPDF2
```

Or use the requirements file:
```bash
pip install -r requirements.txt
```

## Usage

### Interactive Mode

Run the main script to use the interactive interface:

```bash
python pageRank.py
```

The interactive menu provides options to:
1. Process a PDF file (extract text and store in database)
2. Search documents (find most relevant documents for a query)
3. List all documents in the database
4. Get detailed statistics for a specific document
5. Exit

### Programmatic Usage

You can also use the analyzer programmatically:

```python
from pageRank import PDFTextAnalyzer

# Initialize the analyzer
analyzer = PDFTextAnalyzer("my_database.db")

# Process a PDF file
analyzer.process_pdf("path/to/your/document.pdf")

# Search for relevant documents
results = analyzer.search("machine learning", top_n=10)
for filename, score in results:
    print(f"{filename}: {score:.4f}")

# List all documents
analyzer.list_documents()

# Get document statistics
analyzer.get_document_stats("document.pdf")
```

## How It Works

### 1. Text Extraction
- Uses PyPDF2 to extract text from PDF files
- Handles multi-page documents automatically

### 2. Text Preprocessing
- Converts text to lowercase
- Removes special characters and digits
- Tokenizes into individual words
- Removes common stop words (the, and, or, etc.)
- Filters out words shorter than 3 characters

### 3. Term Frequency Calculation
- Calculates TF (Term Frequency) = (word count) / (total words in document)
- Stores both raw frequency counts and normalized TF scores

### 4. Search Algorithm
- Uses TF-IDF (Term Frequency-Inverse Document Frequency) scoring
- IDF = log(total documents / documents containing term)
- Final score = TF × IDF for each query term
- Returns documents ranked by relevance score

### 5. Database Schema

**Documents Table:**
- id: Primary key
- filename: Name of the PDF file
- content: Full extracted text
- word_count: Total number of words

**Term Frequency Table:**
- id: Primary key
- document_id: Foreign key to documents table
- term: Individual word/term
- frequency: Raw count of the term
- tf_score: Normalized term frequency score

## Example Output

```
Processing document.pdf...
Successfully processed document.pdf with 1250 unique terms

Top 10 matching documents for 'machine learning':
----------------------------------------------------------
 1. ai_research.pdf (Score: 2.3456)
 2. data_science.pdf (Score: 1.8932)
 3. python_guide.pdf (Score: 1.2341)
 ...
```

## Performance Considerations

- The database file grows with the number of documents and unique terms
- Search performance is optimized with proper indexing
- Large PDF files may take longer to process initially
- Once processed, search queries are very fast

## Error Handling

- Gracefully handles corrupted or unreadable PDF files
- Validates file existence before processing
- Database transactions with rollback on errors
- Informative error messages for troubleshooting

## Requirements

- Python 3.6+
- PyPDF2 3.0.1+
- SQLite3 (included with Python)

## Files

- `pageRank.py`: Main application with PDFTextAnalyzer class
- `example_usage.py`: Example script showing programmatic usage
- `requirements.txt`: Python dependencies
- `README.md`: This documentation file

## License

This project is open source and available under the MIT License.
