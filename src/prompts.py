# ---- Prompt ----
system_prompt = """
You are an ESG analyst specializing in ESRS (European Sustainability Reporting Standards) under CSRD.

Extract whether the text contains disclosures for ESRS E2–E5 codes (e.g. E2-1, E3-4, E4-2, E5-3).

Rules:
- Only mark YES if there is explicit disclosure.
- Use PARTIAL if implied but incomplete.
- Use NO if not present.
- Provide exact supporting quotes as evidence.
- Be strict and conservative.
"""


# ---- Example input (replace with annual report chunk) ----
user_text = """
The company has implemented a formal environmental policy addressing emissions reduction.
Water usage is monitored but no formal targets exist.
We aim to reduce waste through recycling initiatives.
Biodiversity impacts are assessed in high-risk areas.
"""
