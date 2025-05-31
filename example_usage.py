"""
Example usage of the PDF Text Analyzer
using the pageRank module programmatically,
including processing multiple PDFs and searching for terms.

"""
from pageRank import PDFTextAnalyzer

def example_usage():
    # Initialize the analyzer
    analyzer = PDFTextAnalyzer("example_database.db")
    
    # Example: Process multiple PDF files
    pdf_files = [
        "document1.pdf",
        "document2.pdf",
        # Add your PDF file paths here
    ]
    
    # Process each PDF file
    for pdf_file in pdf_files:
        print(f"Processing {pdf_file}...")
        success = analyzer.process_pdf(pdf_file)
        if success:
            print(f"✓ Successfully processed {pdf_file}")
        else:
            print(f"✗ Failed to process {pdf_file}")
    
    # Example searches with different queries
    search_queries = [
        "machine learning",
        "data analysis", 
        "python programming",
        "artificial intelligence"
    ]
    
    for query in search_queries:
        print(f"\nSearching for: '{query}'")
        results = analyzer.search(query, top_n=5)
        
        if results:
            for i, (filename, score) in enumerate(results, 1):
                print(f"{i}. {filename} (Relevance: {score:.4f})")
        else:
            print("No matching documents found.")
    
    # List all documents in database
    print("\n" + "="*50)
    analyzer.list_documents()

if __name__ == "__main__":
    example_usage()
