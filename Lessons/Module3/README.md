# **Module 3: Retrieval-Augmented Generation (RAG)**

This module covers grounding: making a model answer from supplied evidence rather than from memory. We build the full RAG pipeline — indexing, retrieval, and generation — and then examine its limits and the agentic retrieval approach that displaced it for an important class of problems.

### **Lessons**

*   [**Lesson 1: Introduction to Retrieval-Augmented Generation (RAG)**](./Lesson1_Introduction_to_RAG.md)
*   [**Lesson 2: Building and Managing the Knowledge Base**](./Lesson2_Building_and_Managing_the_Knowledge_Base.md)
*   [**Lesson 3: The Retrieval Process**](./Lesson3_The_Retrieval_Process.md)
*   [**Lesson 4: The Generation and Synthesis Process**](./Lesson4_The_Generation_and_Synthesis_Process.md)
*   [**Lesson 5: Agentic Retrieval and the Limits of Vector RAG**](./Lesson5_Agentic_Retrieval.md)

---

### **By the end of this module you will be able to:**

1. Build an indexing pipeline: ingest, chunk, contextualize, embed
2. Choose a retrieval strategy from your corpus's properties rather than by default
3. Write a generator prompt that grounds, cites, and can say 'I don't know'
4. Recognize where vector RAG is the wrong tool

**Estimated time:** 4-5 hours, including the hands-on tasks.

---

### **Check yourself**

Answer these before moving on. If one is hard, the section reference tells you where to look.

1. A chunk contains the answer but is never retrieved. What is the mechanism, and the fix?  <sub>(Module 3, Lesson 2 §2b)</sub>
2. Why does pure vector search fail on 'error code G-451'?  <sub>(Module 3, Lesson 3 §3)</sub>
3. Why did coding agents drop their vector indexes? Name three of the five reasons.  <sub>(Module 3, Lesson 5 §2)</sub>
