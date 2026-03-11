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

GENERAL_TEMPLATES: Dict[str, Dict[str, str]] = {
    "Summarize": {
        "role": "clear communication assistant",
        "objective": "Summarize the provided content clearly and accurately.",
        "tasks": "Read the provided content carefully.\nIdentify key points and remove repetition.\nWrite a concise summary in plain language.",
        "inputs": "Paste the text, meeting notes, article, or transcript to summarize.",
        "expected_output": "A concise summary with the most important points and a short key-takeaways list.",
    },
    "Analyze": {
        "role": "analyst",
        "objective": "Analyze the provided content and explain findings.",
        "tasks": "Review the content.\nIdentify patterns, risks, and opportunities.\nProvide clear insights with rationale.",
        "inputs": "Paste the data, text, report, or scenario to analyze.",
        "expected_output": "A structured analysis with observations, interpretation, and recommended next steps.",
    },
    "Re-write": {
        "role": "writing editor",
        "objective": "Rewrite the provided text to improve clarity, tone, and readability.",
        "tasks": "Understand the original message.\nRewrite for clarity and flow.\nKeep the original meaning while improving wording.",
        "inputs": "Paste the text to rewrite and mention preferred tone (optional).",
        "expected_output": "A polished rewritten version plus a short note about major improvements made.",
    },
    "Brainstorm": {
        "role": "creative idea coach",
        "objective": "Generate useful ideas for the user's topic.",
        "tasks": "Understand the goal and context.\nGenerate diverse ideas.\nGroup ideas and suggest the best options to start with.",
        "inputs": "Share your topic, constraints, and desired outcome.",
        "expected_output": "A list of practical ideas grouped by theme, including top recommendations.",
    },
}

FORM_STATE_KEYS = (
    "role",
    "objective",
    "tasks",
    "inputs",
    "expected_output",
    "audience",
    "tone",
    "constraints",
    "example_output",
    "extra_notes",
)

DEMO_EXAMPLE: Dict[str, str] = {
    "role": "friendly health appointment helper",
    "objective": (
        "Help me prepare for a doctor visit about ongoing knee pain so I can ask clear "
        "questions and understand my treatment choices."
    ),
    "tasks": (
        "List the most useful questions to ask the doctor.\n"
        "Explain what each question helps me learn.\n"
        "Suggest a short checklist of details to bring to the appointment."
    ),
    "inputs": (
        "I am 72 years old. My knee hurts most when I walk up stairs. Physical therapy helped "
        "a little, but the pain keeps returning. I want plain language, not medical jargon."
    ),
    "expected_output": (
        "A short question list in plain language, plus a simple appointment checklist."
    ),
    "audience": "",
    "tone": "",
    "constraints": "",
    "example_output": "",
    "extra_notes": "",
}

STARTER_LIBRARY: Dict[str, Dict[str, str]] = {
    "business_helper": {
        "label": "Business helper",
        "description": "Broad business-analysis support for general project work.",
        "source": "template",
        "filename": "general_worker",
    },
    "backlog_structurer": {
        "label": "Backlog structurer",
        "description": "Turn an idea into epics, features, and user stories.",
        "source": "template",
        "filename": "backlog_structurer",
    },
    "user_story_generator": {
        "label": "User story generator",
        "description": "Create clear user stories from a feature idea.",
        "source": "template",
        "filename": "user_story_generator",
    },
    "story_validator": {
        "label": "Story validator",
        "description": "Review stories for gaps, clarity, and readiness.",
        "source": "template",
        "filename": "user_story_validator",
    },
    "executive_summary": {
        "label": "Executive summary",
        "description": "Summarize work for leaders in a clean, decision-ready format.",
        "source": "template",
        "filename": "executive_summary",
    },
    "legal_simplifier": {
        "label": "Legal simplifier",
        "description": "Rewrite complex legal or policy text into plain language.",
        "source": "template",
        "filename": "legal_simplifier",
    },
    "summarize": {
        "label": "Summarize",
        "description": "Condense notes, articles, or transcripts into key takeaways.",
        "source": "general",
        "general_label": "Summarize",
    },
    "analyze": {
        "label": "Analyze",
        "description": "Review information and explain patterns, risks, and options.",
        "source": "general",
        "general_label": "Analyze",
    },
    "rewrite": {
        "label": "Re-write",
        "description": "Improve the clarity and tone of existing writing.",
        "source": "general",
        "general_label": "Re-write",
    },
    "brainstorm": {
        "label": "Brainstorm",
        "description": "Generate practical ideas and group the best ones.",
        "source": "general",
        "general_label": "Brainstorm",
    },
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
     "that are clear, testable, well-scoped, and immediately actionable, using a story-quality "
     "checklist that asks whether each story is independent, flexible, valuable, estimable, "
     "small enough, and testable."),
    (("qa", "quality analyst", "validator"),
     "You are a meticulous QA lead and agile quality analyst who reviews user stories for "
     "logical gaps, missing edge cases, and whether each story is independent, flexible, "
     "valuable, estimable, small enough, and testable before it enters a sprint."),
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
    # Use Streamlit's native theming; keep this as a placeholder
    # in case we want to add non-CSS accessibility tweaks later.
    return


def _helper(text: str):
    # Use native helper text styling
    st.caption(text)


def initialize_session_state():
    if "generated_prompt" not in st.session_state:
        st.session_state.generated_prompt = ""
    if "simple_explanation" not in st.session_state:
        st.session_state.simple_explanation = ""
    for key in FORM_STATE_KEYS:
        if key not in st.session_state:
            st.session_state[key] = ""


def reset_form():
    for key in FORM_STATE_KEYS:
        st.session_state[key] = ""
    st.session_state.generated_prompt = ""
    st.session_state.simple_explanation = ""


def populate_form(fields: Dict[str, str]):
    for key in FORM_STATE_KEYS:
        st.session_state[key] = fields.get(key, "")
    st.session_state.generated_prompt = ""
    st.session_state.simple_explanation = ""


def apply_start_action(action: str, starter_key: str | None = None):
    if action == "blank":
        reset_form()
        return
    if action == "starter" and starter_key:
        load_starter(starter_key)


def has_saved_answers() -> bool:
    return any(clean_field(st.session_state.get(key, "")) for key in FORM_STATE_KEYS)


def has_advanced_answers() -> bool:
    return any(
        clean_field(st.session_state.get(key, ""))
        for key in ("audience", "tone", "constraints", "example_output", "extra_notes")
    )


def collect_form_data() -> Dict[str, str]:
    return {key: clean_field(st.session_state.get(key, "")) for key in FORM_STATE_KEYS}


def render_step_overview():
    st.subheader("Three simple steps")
    st.markdown(
        "1. Choose a blank form or load a template.\n"
        "2. Answer a few plain-language questions about what you need.\n"
        "3. Create the prompt, then copy it into ChatGPT, Claude, or another AI tool."
    )


def render_question(
    title: str,
    helper_text: str,
    *,
    key: str,
    placeholder: str,
    height: int | None = None,
):
    st.markdown(f"**{title}**")
    _helper(helper_text)
    if height is None:
        st.text_input(
            title,
            key=key,
            placeholder=placeholder,
            label_visibility="collapsed",
        )
        return

    st.text_area(
        title,
        key=key,
        placeholder=placeholder,
        height=height,
        label_visibility="collapsed",
    )


def render_basic_fields():
    render_question(
        "What do you want help with?",
        "Describe your goal in your own words. This is the most important box.",
        key="objective",
        placeholder="Example: Help me prepare questions for my next doctor visit.",
        height=140,
    )
    render_question(
        "What kind of helper should the AI be? (optional)",
        "If you are not sure, leave this blank and the app will choose a friendly helper voice.",
        key="role",
        placeholder="Example: travel planner, writing coach, legal simplifier",
    )
    render_question(
        "What should the AI do? (optional)",
        "List one step per line if you want the AI to follow a sequence.",
        key="tasks",
        placeholder="Example:\nExplain my options.\nGive me a checklist.\nSuggest questions to ask.",
        height=130,
    )
    render_question(
        "What details should the AI use? (optional)",
        "Add facts, notes, or pasted text that will help the answer fit your situation.",
        key="inputs",
        placeholder="Example: Age, important dates, notes, rules, or text to summarize.",
        height=140,
    )
    render_question(
        "What should the answer look like? (optional)",
        "Describe the kind of result you want, such as a checklist, summary, or plan.",
        key="expected_output",
        placeholder="Example: A short checklist in plain language with clear next steps.",
        height=130,
    )


def render_advanced_fields():
    st.markdown("### More options")
    render_question(
        "Who is the answer for? (optional)",
        "This helps the AI choose the right reading level and style.",
        key="audience",
        placeholder="Example: me, my family, my manager, or a leadership team",
    )
    render_question(
        "How should the answer sound? (optional)",
        "Use this if you want the answer to feel more formal, warm, or concise.",
        key="tone",
        placeholder="Example: calm and supportive, professional, friendly",
    )
    render_question(
        "Any rules or limits? (optional)",
        "Use this for word limits, banned jargon, formatting rules, or special requests.",
        key="constraints",
        placeholder="Example: Keep it under 1 page. Avoid acronyms. Use bullet points.",
        height=110,
    )
    render_question(
        "Do you have an example answer? (optional)",
        "Paste a rough example if you want the AI to mirror its style or structure.",
        key="example_output",
        placeholder="Paste a rough example here if you already have one.",
        height=130,
    )
    render_question(
        "Anything else the AI should remember? (optional)",
        "Add final reminders or context that does not fit anywhere else.",
        key="extra_notes",
        placeholder="Example: Keep the tone encouraging and explain unfamiliar terms.",
        height=110,
    )


def load_starter(choice_key: str):
    starter = STARTER_LIBRARY.get(choice_key)
    if not starter:
        return
    if starter["source"] == "template":
        populate_form(load_template(starter["filename"]))
        return
    populate_form(GENERAL_TEMPLATES.get(starter["general_label"], {}))


def build_feedback_messages(data: Dict[str, str]) -> List[str]:
    messages: List[str] = []
    if is_vague(data.get("objective", "")):
        messages.append("Add 1 or 2 more sentences to 'What do you want help with?' for a stronger result.")
    if data.get("tasks") and is_vague(data.get("tasks", "")):
        messages.append("Make the 'What should the AI do?' box more specific by listing clear actions.")
    if not data.get("inputs"):
        messages.append("If the answer needs context, add a few useful details in 'What details should the AI use?'.")
    return messages


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="Prompt Builder for IBMDT",
        page_icon="✨",
        layout="centered",
    )
    apply_accessible_styling()
    initialize_session_state()

    st.title("Prompt Builder for IBMDT")
    st.caption("Powered by Data & AI team")
    st.write(
        "Answer a few simple questions and this tool turns your words into a ready-to-use AI prompt. "
        "No technical knowledge is needed."
    )
    render_step_overview()
    st.info(
        "How it works: choose a blank form or a template, fill in the questions, "
        "then copy the finished prompt into ChatGPT, Claude, or another AI tool."
    )

    st.markdown("### Step 1 of 3: Choose how you want to start")
    start_choice = st.radio(
        "Starting point",
        (
            "Use blank form",
            "Select from template",
        ),
        label_visibility="collapsed",
    )
    if start_choice == "Select from template":
        # Use custom label rendering for selectbox options (text only)
        def selectbox_label(key):
            return STARTER_LIBRARY[key]["label"]

        starter_choice = st.selectbox(
            "Select a template",
            options=list[str](STARTER_LIBRARY.keys()),
            format_func=selectbox_label,
            key="starter_selectbox_black",
            label_visibility="visible",
        )
        st.caption(STARTER_LIBRARY[starter_choice]["description"])
    else:
        st.info("Start with empty fields and type your own request.")

    start_button_label = "Use blank form" if start_choice == "Use blank form" else "Use template"

    if has_saved_answers():
        st.caption("Changing this will replace your current answers.")

    if start_choice == "Use blank form":
        st.button(
            start_button_label,
            use_container_width=True,
            on_click=apply_start_action,
            args=("blank",),
        )
    else:
        st.button(
            start_button_label,
            use_container_width=True,
            on_click=apply_start_action,
            args=("starter", starter_choice),
        )

    st.markdown("---")
    st.markdown("### Step 2 of 3: Tell us what you need")
    with st.expander("Why these questions help", expanded=False):
        st.write(
            "The app builds a stronger prompt when it knows your goal, the details that matter, "
            "and what kind of answer would be most useful."
        )
        st.write(
            "You do not need to fill every box. Start with your goal, then add more detail only if it helps."
        )

    render_basic_fields()

    show_advanced = st.checkbox(
        "I want to add audience, tone, or other extra instructions",
        value=has_advanced_answers(),
    )
    if show_advanced:
        render_advanced_fields()

    st.markdown("---")
    st.markdown("### Step 3 of 3: Create your prompt")
    st.write("Press the button when you are ready. You can update your answers and create the prompt again at any time.")
    action_col_1, action_col_2 = st.columns(2)
    with action_col_1:
        generate_clicked = st.button(
            "Generate prompt",
            icon="🤩",
            # type="primary",
            use_container_width=True,
        )
    with action_col_2:
        st.button(
            "Clear form",
            use_container_width=True,
            on_click=reset_form,
        )

    if generate_clicked:
        data = collect_form_data()
        prompt = build_prompt(data)
        st.session_state.generated_prompt = prompt
        st.session_state.simple_explanation = build_simple_explanation(data)

        feedback_messages = build_feedback_messages(data)
        if feedback_messages:
            st.warning("\n".join(f"- {message}" for message in feedback_messages))

    st.markdown("---")
    st.markdown("### Your ready-to-use AI prompt")

    if st.session_state.generated_prompt:
        prompt_text = st.session_state.generated_prompt
        num_chars = len(prompt_text)
        approx_tokens = max(1, num_chars // 4)

        st.success("Your prompt is ready. Copy it, then paste it into your AI tool.")
        st.caption(f"Prompt length: about {num_chars} characters (~{approx_tokens} tokens).")
        st.text_area(
            "Review or copy the prompt below",
            value=prompt_text,
            height=320,
        )
        st.info(
            "Next step: open ChatGPT, Claude, or another AI tool, paste this prompt, and add any extra details you want the AI to consider."
        )
    else:
        st.write("Your finished prompt will appear here after you press **Create my prompt**.")

    if st.session_state.simple_explanation:
        st.markdown("### What this prompt asks the AI to do")
        st.markdown(st.session_state.simple_explanation)


if __name__ == "__main__":
    main()
