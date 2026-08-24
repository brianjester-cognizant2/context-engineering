# **Module 4: Optimizing the Context Window**

This module is about the harder half of context engineering: deciding what *not* to include, and where to put what remains. We cover context rot and the attention budget, compression, re-ranking, and the four techniques that keep long-running agents coherent across hours of work.

### **Lessons**

*   [**Lesson 1: Mastering the Context Window**](./Lesson1_Mastering_the_Context_Window.md)
*   [**Lesson 2: Contextual Compression and Distillation**](./Lesson2_Contextual_Compression_and_Distillation.md)
*   [**Lesson 3: Re-ranking for Relevance**](./Lesson3_Re-ranking_for_Relevance.md)
*   [**Lesson 4: Context Engineering for Long-Horizon Agents**](./Lesson4_Long_Horizon_Context.md)

---

### **By the end of this module you will be able to:**

1. Explain context rot and plan against the effective window rather than the nominal one
2. Assemble context cache-aware and under a budget enforced in code
3. Compress and re-rank retrieved material
4. Keep a long-horizon agent coherent with compaction, notes, sub-agents, and JIT retrieval

**Estimated time:** 4-5 hours, including the hands-on tasks.

---

### **Check yourself**

Answer these before moving on. If one is hard, the section reference tells you where to look.

1. Your model has a 128K window. How much can you actually use, and why?  <sub>(Module 4, Lesson 1 §1)</sub>
2. When over budget, why is dropping the oldest content usually wrong?  <sub>(Module 4, Lesson 1 §4)</sub>
3. Which item does a compaction prompt most often omit, and what does that cost?  <sub>(Module 4, Lesson 4 §2)</sub>
