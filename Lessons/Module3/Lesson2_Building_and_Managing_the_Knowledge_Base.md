# **Module 3, Lesson 2: Building and Managing the Knowledge Base**

### Building on What We've Learned

In the last lesson, we saw the "what" and "why" of RAG. Now we dive into the "how" of the very first step: preparing the knowledge for the Retriever. This process, often called **"indexing,"** is about creating a well-organized library that our AI can search through efficiently.

### Learning Objectives

By the end of this lesson, you will be able to:
*   **List** the three main steps of the indexing pipeline: Ingestion, Chunking, and Embedding.
*   **Explain** why chunking is necessary and compare different chunking strategies.
*   **Describe** what a vector embedding is and why it's essential for semantic search.
*   **Use** a library to split a document into chunks and generate an embedding for a piece of text.

---

### **1. The Indexing Pipeline: A Three-Step Process**

Think of building a knowledge base like preparing a new library for a research assistant.

1.  **Ingestion (Acquiring the Books):** First, you gather all your raw documents. This can be anything: PDFs, `.txt` files, web pages, or even transcripts from videos. Frameworks like **LlamaIndex** and **LangChain** provide "Document Loaders" that automate this, connecting to sources like websites, YouTube, or Slack.

2.  **Chunking (Creating Index Cards):** You can't hand the assistant a 500-page book and say "find the answer." It's too slow. Instead, you create "index cards" by breaking the book into smaller, meaningful snippets. This is **chunking**. The quality of your chunks directly impacts the quality of your search results.

3.  **Embedding (Organizing by Meaning):** You don't want to organize these index cards alphabetically. You want to organize them by *topic*. An **embedding model** does this by reading each index card (chunk) and assigning it a set of coordinates (a **vector**). Cards with similar topics will be placed close together in this conceptual "space."

---

### **2. Chunking Strategies: How to Make Good Index Cards**

**A. Fixed-Size Chunking:**
The simplest method. You chop the document into chunks of a fixed number of characters, often with some overlap to avoid splitting sentences awkwardly. It's easy but can be clumsy, like ripping a page in half mid-sentence.

**B. Recursive Character Text Splitting:**
A much smarter approach and the recommended starting point. It tries to split text based on a prioritized list of separators, such as:
1.  Double newlines (`\n\n` - paragraphs)
2.  Single newlines (`\n`)
3.  Spaces (` `)

This method is much better at keeping related sentences together.

**Code Example (using a library like LangChain):**
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

my_text = "This is the first paragraph.\n\nThis is the second."

# This splitter tries to make 1000-character chunks, with 200 chars of overlap.
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, length_function=len,
)
chunks = text_splitter.split_text(my_text)
# `chunks` is now a list of strings, each a chunk of the original document.
```

> **Deep Dive: Advanced Chunking**
> For more complex needs, explore **Semantic Chunking**, which uses an embedding model to find natural topic breaks, or **Agentic Chunking**, where a model reasons about the document to produce chunks aligned to the questions users actually ask.

**C. Structure-Aware Chunking**
For documents with real structure — Markdown, HTML, code, PDFs with headings — split on the structure rather than on characters. A Markdown splitter that breaks on headings and carries the heading path into each chunk's metadata gives you chunks that are self-describing. This is usually a larger quality win than tuning `chunk_size`, and it takes about the same effort.

---

### **2b. Contextual Retrieval: Fixing the Orphaned Chunk**

Here's a failure mode that shows up in essentially every naive RAG system, and it's worth fixing early because the fix is cheap.

Chunking destroys context. Consider this chunk, extracted verbatim from a quarterly report:

> *"Revenue grew 12% over the previous quarter, driven primarily by enterprise renewals."*

A user asks: *"What was ACME's Q3 2025 revenue growth?"* This chunk **is the answer** — and it will very likely not be retrieved, because it contains neither "ACME" nor "Q3" nor "2025". The words that would have matched the query were in the document title and the section heading, three pages up. Embedded in isolation, the chunk is an orphan.

**Contextual retrieval** fixes this at indexing time: before embedding, prepend a short generated description situating the chunk in its source document.

```python
CONTEXTUALIZE = (
    "Here is a document:\n<document>{doc}</document>\n\n"
    "Here is a chunk from it:\n<chunk>{chunk}</chunk>\n\n"
    "Write 1-2 sentences situating this chunk within the document, to improve "
    "search retrieval of the chunk. Answer with only that context, nothing else."
)

def contextualize(chunk, doc):
    blurb = cheap_model(CONTEXTUALIZE.format(doc=doc, chunk=chunk))
    return f"{blurb}\n\n{chunk}"      # embed this; store the original for display
```

The chunk that gets embedded becomes:

> *"This chunk is from ACME Corp's Q3 2025 quarterly earnings report, in the section on revenue performance. Revenue grew 12% over the previous quarter, driven primarily by enterprise renewals."*

Now it matches the query. Reported retrieval-failure reductions from this technique are substantial — commonly cited around a third, and larger still when combined with hybrid search and re-ranking (Lesson 3 and Module 4, Lesson 3).

**The trade-off is real but usually favourable:** you pay one cheap model call per chunk, once, at index time — and prompt caching makes it cheaper still, since the same document is the prefix for all of its chunks. You pay nothing extra per query, forever. **Store the original chunk for display and embed the contextualized version**, so users see clean text while the index sees enriched text.

---

### **3. Vector Embeddings: The Language of Meaning**

Once we have our chunks, we need a way to search them not by keywords, but by **semantic meaning**. This is the magic of **vector embeddings**.

An **embedding model** is a neural network that converts a piece of text into a list of numbers called a **vector**. This vector is a mathematical representation of the text's meaning.

*   Chunks with similar meanings will have vectors that are "close" to each other in this vector space.
*   Chunks with different meanings will have vectors that are "far apart."

**Diagram: A Conceptual View of Vector Space**
Imagine a 3D space (though in reality it's often 1536+ dimensions):
*   The chunk "How much is a subscription?" is at one point.
*   The chunk "Our pricing plans are..." is a point very close by.
*   The chunk "The company was founded in 2015" is a point far, far away.

**Code Example: Creating an Embedding with OpenAI**
```python
from openai import OpenAI
client = OpenAI()

def get_embedding(text, model="text-embedding-3-small"):
   # The vector has a fixed length (e.g., 1536 for this model)
   return client.embeddings.create(input=[text], model=model).data[0].embedding

my_chunk = "Our pricing plans are listed on the website."
my_vector = get_embedding(my_chunk)

# my_vector is now a list of numbers: [0.012, -0.045, ..., 0.089]
print(f"Created a vector with {len(my_vector)} dimensions.")
```
This vector is the key to our semantic search. In the next lesson, we'll learn how to store these vectors in a specialized **vector database** and use them to retrieve the most relevant "index cards" for any given user query.

---

### **Key Takeaways**

*   The indexing pipeline is **Ingest → Chunk → Embed**.
*   **Chunking** is essential. Recursive splitting is the default; **structure-aware splitting** is usually a bigger win than tuning chunk size.
*   **Contextual retrieval** — prepending a generated situating sentence before embedding — fixes the orphaned-chunk problem for a one-time indexing cost and no per-query cost.
*   **Vector embeddings** turn meaning into coordinates, so "close together" means "similar in meaning."
*   Index-time investment is almost always cheaper than query-time investment: you pay it once, and every query benefits.

### **Hands-On Task: The Chunking Challenge**

**Scenario:**
You are given the following short document as a single string. Your goal is to chunk it effectively.

```
doc = """
The Solar System has 8 planets. Mercury is closest to the Sun. It is very hot.
Venus is the second planet. It has a thick atmosphere.
Earth is the third planet. It is our home.

The Gas Giants are Jupiter, Saturn, Uranus, and Neptune.
Jupiter is the largest planet. It has a Great Red Spot.
Saturn is known for its beautiful rings.
"""
```

**Your Task:**
1.  **Chunk it manually.** How would you split this into meaningful chunks? Paste the text and draw `---` where the best splits are. What's your reasoning?
2.  **Fixed-size chunking.** With `chunk_size=70` characters, write out the first chunk. What's wrong with it?
3.  **Recursive chunking.** `RecursiveCharacterTextSplitter` prioritizes `\n\n`. What would its first two chunks be, and why is that better?
4.  **Find the orphan.** A user asks *"How many planets are gas giants?"* Which of your recursive chunks contains the answer? Now read that chunk in isolation, with no document title — would a semantic search for that query actually retrieve it? Explain what's missing.
5.  **Contextualize it.** Write the 1–2 sentence blurb you'd prepend to that chunk before embedding. Then state precisely which words in your blurb do the retrieval work, and why they weren't in the chunk already.
