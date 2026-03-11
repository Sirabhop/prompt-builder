import textwrap
from pathlib import Path
from typing import Dict, List

import streamlit as st

TEMPLATE_DIR = Path(__file__).parent / "prompt-template"

TEMPLATE_REGISTRY: Dict[str, str] = {
    "General Worker Helper": "general_worker",
    "Backlog Structurer": "backlog_structurer",
    "User Story Generator": "user_story_generator",
    "Story Validator": "user_story_validator",
    "Executive Summary": "executive_summary",
    "Legal Simplifier": "legal_simplifier",
}


# ---------------------------------------------------------------------------
# Template loading
# ---------------------------------------------------------------------------
def _parse_template_md(text: str) -> Dict[str, str]:
    """Parse a prompt-template markdown file into field values.

    Expects H2 headers (## Role, ## Objective, etc.) with content below each.
    Stops collecting a section when the next H2 or '---' separator appears.
    """
    field_map: Dict[str, str] = {
        "role": "",
        "objective": "",
        "tasks": "",
        "inputs": "",
        "expected output": "",
    }
    current_key: str | None = None
    lines_buf: List[str] = []

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("## "):
            if current_key is not None and current_key in field_map:
                field_map[current_key] = "\n".join(lines_buf).strip()
            header = stripped[3:].strip().lower()
            if header == "prompt":
                current_key = None
                lines_buf = []
                continue
            current_key = header
            lines_buf = []
            continue

        if stripped == "---":
            if current_key is not None and current_key in field_map:
                field_map[current_key] = "\n".join(lines_buf).strip()
            current_key = None
            lines_buf = []
            continue

        if current_key is not None:
            lines_buf.append(line)

    if current_key is not None and current_key in field_map:
        field_map[current_key] = "\n".join(lines_buf).strip()

    return {
        "role": field_map["role"],
        "objective": field_map["objective"],
        "tasks": field_map["tasks"],
        "inputs": field_map["inputs"],
        "expected_output": field_map["expected output"],
    }


def load_template(filename: str) -> Dict[str, str]:
    """Load and parse a template markdown file by its stem name."""
    path = TEMPLATE_DIR / f"{filename}.md"
    if not path.exists():
        return {}
    return _parse_template_md(path.read_text(encoding="utf-8"))


def load_full_prompt_from_template(filename: str) -> str:
    """Extract the full XML prompt block from a template markdown file."""
    path = TEMPLATE_DIR / f"{filename}.md"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    in_prompt_section = False
    in_code_block = False
    lines: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "## Prompt":
            in_prompt_section = True
            continue
        if in_prompt_section and stripped.startswith("```xml"):
            in_code_block = True
            continue
        if in_code_block:
            if stripped == "```":
                break
            lines.append(line)
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Core logic helpers
# ---------------------------------------------------------------------------
def clean_field(text: str) -> str:
    if not text:
        return ""
    return text.strip()


def split_tasks(tasks_text: str) -> List[str]:
    """Turn free-text tasks into a clean list of steps."""
    tasks_text = clean_field(tasks_text)
    if not tasks_text:
        return []

    if "\n" in tasks_text:
        raw_parts = tasks_text.splitlines()
    else:
        for sep in [";", "."]:
            tasks_text = tasks_text.replace(sep, "\n")
        raw_parts = tasks_text.splitlines()

    steps = []
    for part in raw_parts:
        part = part.strip("-\u2022 ").strip()
        if part:
            steps.append(part)
    return steps


# Role keyword -> rich description pairs.  Checked top-to-bottom; first match wins.
_ROLE_HINTS: List[tuple] = [
    (("product manager", "backlog"),
     "You are a senior product manager and backlog architect with deep expertise in agile "
     "product development. You excel at decomposing ambiguous ideas into clean, actionable "
     "backlog hierarchies."),
    (("agile", "user story", "scrum"),
     "You are an experienced agile coach and user story specialist. You write user stories "
     "that are clear, testable, well-scoped, and immediately actionable, following INVEST "
     "principles rigorously."),
    (("qa", "quality analyst", "validator"),
     "You are a meticulous QA lead and agile quality analyst who reviews user stories for "
     "logical gaps, missing edge cases, and INVEST compliance before they enter a sprint."),
    (("program manager", "executive", "summary"),
     "You are a senior program manager and executive communications specialist who distills "
     "complex project information into clear, decision-ready summaries for leadership."),
    (("legal", "plain-language", "simplif"),
     "You are a plain-language specialist and legal communications advisor who makes complex "
     "legal and policy text accessible to everyday readers without changing its meaning."),
    (("teacher", "tutor"),
     "You are a clear, patient teacher who explains ideas in simple language and checks "
     "that the user can follow each step."),
    (("doctor", "nurse", "medical"),
     "You are a careful health explainer. You are not giving medical advice, but you explain "
     "health information in simple, calm language that is easy to understand."),
    (("travel", "trip", "planner"),
     "You are a thoughtful travel planner who suggests simple, realistic plans and explains "
     "options clearly, step by step."),
    (("writing", "editor", "coach"),
     "You are a gentle writing coach who helps improve wording, structure, and clarity while "
     "keeping the user's own voice."),
]


def infer_role_description(role: str, data: Dict) -> str:
    """Turn a short role hint into a rich, concrete role description."""
    role = clean_field(role)
    lower = role.lower()

    if not role:
        return (
            "You are a friendly, patient AI assistant who explains things in clear, simple language "
            "for an older adult user."
        )

    for keywords, description in _ROLE_HINTS:
        if any(kw in lower for kw in keywords):
            return description

    return (
        f"You are a helpful, patient {role} who explains things clearly, avoids jargon, "
        f"and supports an older adult user."
    )


def infer_context_section(data: Dict) -> str:
    objective = clean_field(data.get("objective", ""))
    inputs = clean_field(data.get("inputs", ""))
    audience = clean_field(data.get("audience", ""))
    extra_notes = clean_field(data.get("extra_notes", ""))

    lines: List[str] = []

    if objective:
        lines.append(f"The user would like help with the following overall goal: {objective}")
    else:
        lines.append(
            "The user would like help with a general question or task. Ask for more details only "
            "if needed to give a clear answer."
        )

    if audience:
        lines.append(f"The main audience for the answer is: {audience}")
    if inputs:
        lines.append("Use the following information as context:")
        lines.append(inputs)
    if extra_notes:
        lines.append("Additional notes from the user:")
        lines.append(extra_notes)

    return "<context>\n" + "\n".join(lines) + "\n</context>"


def infer_task_section(data: Dict) -> str:
    tasks_text = clean_field(data.get("tasks", ""))
    objective = clean_field(data.get("objective", ""))

    steps = split_tasks(tasks_text)
    lines: List[str] = []

    if steps:
        lines.append("<task>")
        for idx, step in enumerate(steps, start=1):
            lines.append(f"{idx}. {step}")
        lines.append("</task>")
        return "\n".join(lines)

    fallback_steps = [
        "Understand the user's goal and any information they provided.",
        "Decide on a clear, simple way to help.",
        "Explain your answer step by step in plain language.",
    ]
    if objective:
        fallback_steps.insert(1, f"Connect your answer directly to this goal: {objective}")

    lines.append("<task>")
    for idx, step in enumerate(fallback_steps, start=1):
        lines.append(f"{idx}. {step}")
    lines.append("</task>")
    return "\n".join(lines)


def infer_inputs_section(data: Dict) -> str:
    inputs = clean_field(data.get("inputs", ""))
    objective = clean_field(data.get("objective", ""))
    audience = clean_field(data.get("audience", ""))
    constraints = clean_field(data.get("constraints", ""))

    bullets: List[str] = []
    if objective:
        bullets.append(f"- Goal: {objective}")
    if inputs:
        bullets.append(f"- Key information: {inputs}")
    if audience:
        bullets.append(f"- Audience: {audience}")
    if constraints:
        bullets.append(f"- Special limits or rules: {constraints}")

    if not bullets:
        bullets.append(
            "- Use any details the user gives you. If information is missing, make gentle, "
            "reasonable assumptions and keep things simple."
        )

    return "<inputs>\n" + "\n".join(bullets) + "\n</inputs>"


def infer_output_format_section(data: Dict) -> str:
    expected_output = clean_field(data.get("expected_output", ""))
    tone = clean_field(data.get("tone", ""))

    lines = ["<output_format>"]

    if expected_output:
        lines.append("Provide a response that matches this description of a good answer:")
        lines.append(expected_output)
    else:
        lines.append(
            "Provide a clear, well-structured answer in short paragraphs or simple bullet points."
        )

    lines.append("")
    lines.append("When helpful, structure your response as:")
    lines.append("1. A short summary in 1-3 sentences.")
    lines.append("2. Step-by-step guidance or bullet points.")
    lines.append("3. A brief recap at the end.")

    if tone:
        lines.append("")
        lines.append(f"Keep the tone: {tone}")

    lines.append("</output_format>")
    return "\n".join(lines)


def infer_quality_bar(data: Dict) -> str:
    constraints = clean_field(data.get("constraints", ""))
    audience = clean_field(data.get("audience", ""))

    lines = ["<quality_bar>"]
    lines.append("Aim for the following quality:")
    lines.append("- Use plain, simple language and avoid technical jargon.")
    lines.append("- Be kind, patient, and respectful.")
    lines.append("- Do not skip important steps; explain the 'why' when it helps.")
    lines.append("- Prefer shorter sentences and clear headings or bullet points.")
    lines.append(
        "- If something is unclear, briefly say what is missing, but still do your best "
        "with the information you have."
    )

    if audience:
        lines.append(
            f"- Make sure the answer is easy for this audience to understand: {audience}"
        )
    if constraints:
        lines.append(
            f"- Follow these limits or preferences from the user: {constraints}"
        )

    lines.append("</quality_bar>")
    return "\n".join(lines)


def infer_helpful_additions_section(data: Dict) -> str:
    audience = clean_field(data.get("audience", ""))
    tone = clean_field(data.get("tone", ""))
    constraints = clean_field(data.get("constraints", ""))

    items: List[str] = []
    if audience:
        items.append(f"- Likely audience: {audience}")
    if tone:
        items.append(f"- Preferred tone: {tone}")
    if constraints:
        items.append(f"- Constraints or limits: {constraints}")

    if not items:
        return ""

    lines = ["<helpful_additions>"]
    lines.append("These extra details may help you shape a more useful answer for the user:")
    lines.extend(items)
    lines.append("</helpful_additions>")
    return "\n".join(lines)


def build_example_section(example_output: str) -> str:
    example_output = clean_field(example_output)
    if not example_output:
        return ""
    return "<example>\n" + example_output + "\n</example>"


def build_prompt(data: Dict) -> str:
    """Assemble the final polished prompt from user-provided data."""
    role_description = infer_role_description(data.get("role", ""), data)

    sections = [
        "<role>\n" + role_description + "\n</role>",
        infer_context_section(data),
        infer_task_section(data),
        infer_inputs_section(data),
        infer_output_format_section(data),
        infer_quality_bar(data),
    ]

    helpful_additions = infer_helpful_additions_section(data)
    if helpful_additions:
        sections.append(helpful_additions)

    example_section = build_example_section(data.get("example_output", ""))
    if example_section:
        sections.append(example_section)

    return "\n\n".join(sections).strip()


def is_vague(text: str) -> bool:
    text = clean_field(text).lower()
    if not text:
        return True
    if len(text) < 25:
        return True
    vague_words = ["something", "good", "nice", "anything", "stuff", "make it better"]
    return any(word in text for word in vague_words)


def build_simple_explanation(data: Dict) -> str:
    role = clean_field(data.get("role", "")) or "a helpful AI assistant"
    objective = clean_field(data.get("objective", "")) or "help with a general question"
    expected_output = clean_field(data.get("expected_output", "")) or "a clear, easy-to-read answer"

    return textwrap.dedent(f"""\
        - The AI is asked to act as **{role}**.
        - The main goal is: **{objective}**.
        - It will follow clear steps, using any information you provided.
        - It is asked to give: **{expected_output}**.
        - The prompt reminds the AI to use simple language and be patient with the user.""")


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
def apply_accessible_styling():
    st.markdown(
        """
        <style>
        body { font-size: 18px; }
        .stMarkdown, .stTextInput label, .stTextArea label { font-size: 18px !important; }
        .stTextInput input, .stTextArea textarea { font-size: 18px !important; padding: 0.75rem; }
        .stButton button { font-size: 18px !important; padding: 0.75rem 1.5rem !important; }
        .small-helper { font-size: 15px; color: #444; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _helper(text: str):
    st.markdown(f'<div class="small-helper">{text}</div>', unsafe_allow_html=True)


def render_basic_fields() -> Dict:
    _helper("Who should the AI pretend to be while helping you?")
    role = st.text_input(
        "Role", key="role",
        placeholder="Example: product manager, agile coach, legal simplifier",
    )
    
    _helper("Describe the main goal in your own words.")
    objective = st.text_area(
        "Objective", key="objective",
        placeholder="What do you want the AI to help you do?",
        height=90,
    )
    
    _helper("You can list one or several steps. One per line is easiest.")
    tasks = st.text_area(
        "Tasks", key="tasks",
        placeholder="List the things you want the AI to do.\nOne per line is easiest.",
        height=120,
    )
    
    _helper("Share any details that will help the AI give a better answer.")
    inputs = st.text_area(
        "Inputs", key="inputs",
        placeholder="Add any information the AI should use.\nExamples: project details, text to analyze, business rules.",
        height=120,
    )
    
    _helper("Explain what kind of answer you would like to see.")
    expected_output = st.text_area(
        "Expected output", key="expected_output",
        placeholder="Describe what a good answer should look like.\nExample: structured backlog, validation report, executive summary.",
        height=120,
    )
    

    return {
        "role": role,
        "objective": objective,
        "tasks": tasks,
        "inputs": inputs,
        "expected_output": expected_output,
    }


def render_advanced_fields() -> Dict:
    st.markdown("### Advanced options (all optional)")

    audience = st.text_input(
        "Audience", key="audience",
        placeholder="Who is this answer for? (Example: leadership team, dev team, stakeholders.)",
    )
    _helper("This helps the AI adjust language and style.")

    tone = st.text_input(
        "Tone", key="tone",
        placeholder="Example: professional and concise, friendly, formal.",
    )
    _helper("How should the answer feel when someone reads it?")

    constraints = st.text_area(
        "Constraints or limits", key="constraints",
        placeholder="Any rules? (Example: keep it under 1 page, use agile terminology, avoid acronyms.)",
        height=90,
    )
    _helper("Add any limits, rules, or preferences.")

    example_output = st.text_area(
        "Example output (optional)", key="example_output",
        placeholder="If you already have a rough example of the answer you want, paste it here.",
        height=120,
    )
    _helper("The AI can use this as a model for the final answer.")

    extra_notes = st.text_area(
        "Extra notes (optional)", key="extra_notes",
        placeholder="Anything else you want the AI to keep in mind.",
        height=90,
    )

    return {
        "audience": audience,
        "tone": tone,
        "constraints": constraints,
        "example_output": example_output,
        "extra_notes": extra_notes,
    }


def apply_template(template_label: str):
    """Load a template from markdown and fill session_state fields."""
    filename = TEMPLATE_REGISTRY.get(template_label)
    if not filename:
        return
    fields = load_template(filename)
    for key in ("role", "objective", "tasks", "inputs", "expected_output"):
        st.session_state[key] = fields.get(key, "")


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Prompt Builder for Seniors",
        page_icon="✨",
        layout="centered",
    )
    apply_accessible_styling()

    if "generated_prompt" not in st.session_state:
        st.session_state.generated_prompt = ""
    if "simple_explanation" not in st.session_state:
        st.session_state.simple_explanation = ""

    # --- Header ---
    st.title("Prompt Builder for Seniors")
    st.write(
        "This tool helps you turn a simple request into a clear, strong AI prompt. "
        "You do not need any technical knowledge \u2014 just describe what you need in your own words."
    )

    # --- Preset templates loaded from prompt-template/ ---
    st.markdown("### Optional: Start from a ready-made template")
    template_labels = list(TEMPLATE_REGISTRY.keys())
    cols = st.columns(len(template_labels))
    for col, label in zip(cols, template_labels):
        with col:
            if st.button(label, use_container_width=True):
                apply_template(label)

    st.markdown("---")
    st.markdown("### 1. Describe your request")

    basic_values = render_basic_fields()
    st.markdown("---")
    with st.expander("Optional: fine-tune the answer (advanced)", expanded=False):
        advanced_values: Dict = render_advanced_fields()

    # --- Prompt quality guidance ---
    st.markdown("---")
    st.markdown("### 2. What makes a good prompt?")
    st.info(
        "Good prompts are clear about **who** the AI should be, **what** it should do, "
        "**what information** it should use, and **what kind of answer** you want. "
        "You fill in the boxes above, and this app turns your words into a strong prompt for you."
    )

    # --- Action buttons ---
    st.markdown("---")
    st.markdown("### 3. Build your final prompt")
    c1, c2 = st.columns([3, 1])
    with c1:
        generate_clicked = st.button(
            "Generate Prompt", type="primary", use_container_width=True,
        )
    with c2:
        clear_clicked = st.button("Clear all fields", use_container_width=True)

    if clear_clicked:
        for key in (
            "role", "objective", "tasks", "inputs", "expected_output",
            "audience", "tone", "constraints", "example_output", "extra_notes",
        ):
            if key in st.session_state:
                st.session_state[key] = ""
        st.session_state.generated_prompt = ""
        st.session_state.simple_explanation = ""
        st.rerun()

    if generate_clicked:
        data = {**basic_values, **advanced_values}
        for k in list(data.keys()):
            data[k] = clean_field(data[k])

        prompt = build_prompt(data)
        st.session_state.generated_prompt = prompt
        st.session_state.simple_explanation = build_simple_explanation(data)

        if is_vague(data.get("objective", "")) or is_vague(data.get("tasks", "")):
            st.warning(
                "Some parts of your request look a bit short or vague. "
                "Try adding a few more details about your goal or steps for a stronger prompt."
            )

    # --- Generated prompt ---
    st.markdown("---")
    st.markdown("### 4. Your ready-to-use AI prompt")

    if st.session_state.generated_prompt:
        prompt_text = st.session_state.generated_prompt
        num_chars = len(prompt_text)
        approx_tokens = max(1, num_chars // 4)

        st.caption(f"Prompt length: about {num_chars} characters (~{approx_tokens} tokens).")
        st.code(prompt_text, language="text")

        st.download_button(
            label="Download prompt as .txt",
            data=prompt_text.encode("utf-8"),
            file_name="prompt_builder_for_seniors_prompt.txt",
            mime="text/plain",
        )
    else:
        st.write("Your final prompt will appear here after you press **Generate Prompt**.")

    # --- Simple explanation ---
    if st.session_state.simple_explanation:
        st.markdown("---")
        st.markdown("### 5. Simple explanation of this prompt")
        st.write("Here is an easy-to-read description of what your prompt is asking the AI to do:")
        st.markdown(st.session_state.simple_explanation)

    # --- Educational section ---
    st.markdown("---")
    st.markdown("### Why this works")
    st.write(
        "This app follows proven prompt-building ideas:\n"
        "- **Role** gives the AI a clear identity so it behaves in a useful way.\n"
        "- **Objective** sets the main goal, so the AI knows what success looks like.\n"
        "- **Tasks** break the work into clear steps the AI can follow.\n"
        "- **Inputs** give context and details, so the answer fits your situation.\n"
        "- **Expected output** reduces confusion by telling the AI what kind of answer you want."
    )
    st.write(
        "The final prompt is organized in simple XML-style sections "
        "(`<role>`, `<context>`, etc.), which many AI systems (including Claude) handle very well."
    )


if __name__ == "__main__":
    main()
