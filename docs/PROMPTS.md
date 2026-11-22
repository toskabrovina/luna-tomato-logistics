# Prompt playbook (for chat AIs: ChatGPT, Copilot 365, Gemini web)

First run `python tasks.py context` and upload / paste `CONTEXT.md` into the chat. Then use these prompts in order.

1. **Understand** — "Explain this problem to me in simple words with a tiny example I can solve by hand."
2. **Model** — "Propose data structures and a function that checks a solution is valid and computes its score.
   Use the VSI conventions in the context. Include pytest tests."
3. **Baseline** — "Write the simplest correct algorithm as `baseline(instance, meter)` in src/algorithms.py.
   Call meter.count() for each explored state."
4. **Main algorithm** — "Design <technique> for this problem. Give the idea, pseudocode, time/space complexity,
   then the code registered in ALGORITHMS."
5. **Pruning** — "Which search-space reduction fits this problem? Implement it and use meter.prune()."
6. **Results** — "Here is results/metrics.csv: <paste>. Interpret it, compare the algorithms, and suggest improvements."
7. **Report** — "Write README section <n> using my code and results. Keep it accurate; do not invent numbers."
8. **Defense** — "Ask me 10 questions a professor would ask about this project, one at a time, and grade my answers."
