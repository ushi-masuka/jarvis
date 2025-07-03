import re
import nltk
from nltk.corpus import stopwords, wordnet

def normalize_query(query: str) -> str:
    """Normalize the query by converting to lowercase, removing special characters, and handling spaces."""
    query = query.lower()
    query = re.sub(r'\W+', ' ', query)  # Replace non-alphanumeric characters with a space
    query = ' '.join(query.split())     # Collapse multiple spaces into one
    return query

def remove_stopwords(text: str) -> str:
    """Remove common English stopwords from the text."""
    stop_words = set(stopwords.words('english'))
    words = text.split()
    filtered_words = [word for word in words if word not in stop_words]
    return ' '.join(filtered_words)

def expand_with_synonyms(text: str) -> str:
    """Expand the text by adding synonyms from WordNet, using only the first synset for each word."""
    words = text.split()
    expanded = set(words)  # Start with original words to avoid duplicates
    for word in words:
        synsets = wordnet.synsets(word)
        if synsets:
            # Use the first synset (most common meaning) and get its lemmas
            synonyms = {lemma.name().replace('_', ' ') for lemma in synsets[0].lemmas()}
            expanded.update(synonyms)
    return ' '.join(expanded)

def process_query(query: str) -> str:
    """Process the query by normalizing, removing stopwords, and expanding with synonyms."""
    normalized = normalize_query(query)
    filtered = remove_stopwords(normalized)
    expanded = expand_with_synonyms(filtered)
    return expanded

# Example usage (for testing purposes)
if __name__ == "__main__":
    sample_query = ""
    result = process_query(sample_query)
    print(f"Original query: {sample_query}")
    print(f"Processed query: {result}")