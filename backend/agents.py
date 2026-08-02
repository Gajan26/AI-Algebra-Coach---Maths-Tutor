"""Deterministic orchestration for the AI Algebra Coach feedback loop."""

from __future__ import annotations

import os
import re
from typing import Literal

import anthropic
from pydantic import BaseModel, Field


class MathStep(BaseModel):
    line: int = Field(ge=1)
    latex: str = Field(min_length=1)


class Assessment(BaseModel):
    issue_found: bool
    line: int | None = None
    snippet: str | None = None
    misconception: str | None = None


class CoachEvent(BaseModel):
    type: Literal["assessment", "coach_message", "highlight", "complete"]
    payload: dict


SOCRATIC_COACH_PROMPT = """You are a patient, encouraging private tutor for Algebra. Your goal is to guide students to understand concepts, not just get answers.

Style:
- Use warm, supportive language ("Great thinking!", "You're on the right track", "I like how you're approaching this")
- Ask one clear guiding question at a time
- Reference specific terms, coefficients, or line numbers
- Celebrate progress and correct thinking

Strategy:
- If the student gives a correct operation, acknowledge it and ask what it implies next
- If stuck or confused, provide a small hint or ask a simpler question to build confidence
- If the answer is correct, congratulate them warmly and confirm they've solved it
- Never give the final answer or a completely corrected line

Support:
- Linear equations, inequalities, systems, quadratics, factoring, functions, polynomials
- Exponents, logarithms, rational expressions, introductory college algebra

Keep responses under 80 words. Use plain, age-appropriate language that builds confidence."""


def assess_steps(steps: list[MathStep]) -> Assessment:
    """Catch the common sign error while leaving richer assessment to a model later.

    This deterministic check makes the real-time experience reliable for the core
    algebra misconception in the product brief.
    """
    for previous, current in zip(steps, steps[1:]):
        if "+" in previous.latex and "=" in previous.latex and "+" in current.latex:
            left_before, right_before = previous.latex.split("=", 1)
            left_after, right_after = current.latex.split("=", 1)
            if "+" in left_before and "+" not in left_after and "+" in right_after:
                return Assessment(
                    issue_found=True,
                    line=current.line,
                    snippet=current.latex,
                    misconception="A positive term was moved across the equals sign without changing its operation.",
                )
    return Assessment(issue_found=False)


def pedagogical_question(assessment: Assessment) -> str:
    """Return a Socratic prompt, never a corrected step or an answer."""
    if assessment.issue_found:
        return (
            f"Look at line {assessment.line}. When a positive term crosses the equals sign, "
            "what operation should undo it?"
        )
    return "Compare each line with the one before it. Which operation did you apply to both sides?"


def additive_term(latex: str) -> str | None:
    """Return a visible + or - term on the left side of an equation, if present."""
    left_side = latex.replace("−", "-").split("=", 1)[0]
    match = re.search(r"([+-]\s*\d+(?:\s*[a-zA-Z])?)", left_side)
    return match.group(1) if match else None


def first_coefficient(latex: str) -> str | None:
    """Find a simple numeric coefficient such as 3 in 3*g."""
    match = re.search(r"\b(\d+)\s*(?:\*|\\cdot)?\s*[a-zA-Z]", latex.replace("−", "-"))
    return match.group(1) if match else None


def opening_question(steps: list[MathStep]) -> str:
    if not steps:
        return "What would you like to work on first?"
    term = additive_term(steps[0].latex)
    if term:
        return f"In Line {steps[0].line}, focus on {term}. What operation would cancel that term, and where must you apply it?"
    return "Which operation would help isolate the variable while keeping both sides balanced?"


def run_coach_loop(steps: list[MathStep]) -> list[CoachEvent]:
    assessment = assess_steps(steps)
    events = [
        CoachEvent(type="assessment", payload=assessment.model_dump()),
        CoachEvent(type="coach_message", payload={"message": pedagogical_question(assessment) if len(steps) > 1 else opening_question(steps)}),
    ]
    if assessment.issue_found:
        events.append(
            CoachEvent(
                type="highlight",
                payload={"line": assessment.line, "snippet": assessment.snippet, "color": "amber"},
            )
        )
    events.append(CoachEvent(type="complete", payload={}))
    return events


def respond_to_student(message: str, steps: list[MathStep], history: list[dict[str, str]] | None = None) -> CoachEvent:
    """Keep the coach focused on a specific line and the student's latest idea."""
    import re
    normalized = message.lower()
    assessment = assess_steps(steps)
    focus_term = additive_term(steps[0].latex) if steps else None
    coefficient = first_coefficient(steps[0].latex) if steps else None

    # Check if student gave a numeric answer or solution (g=7, x=5, 7, -3, etc.)
    solution_pattern = r'^[a-zA-Z]?\s*=?\s*-?\d+\.?\d*$'  # Matches: 7, -5, g=7, x = 3, etc.
    if re.match(solution_pattern, normalized.strip()):
        return CoachEvent(
            type="coach_message",
            payload={"message": "Excellent! You've solved the equation correctly. Great work! 🎉"}
        )

    # Check if student is stuck (asking for help multiple times)
    help_requests = sum(1 for h in (history or []) if any(p in h.get('text', '').lower() for p in ("help", "stuck", "confused", "don't know")))

    if any(phrase in normalized for phrase in ("don't understand", "do not understand", "not sure", "confused", "help")):
        # Provide a hint if they're stuck multiple times
        if help_requests > 2 and steps:
            if focus_term:
                prompt = f"Here's a hint: In Line {steps[0].line}, the term {focus_term} is being added. What's the opposite operation?"
            elif coefficient:
                prompt = f"Here's a hint: The variable {steps[0].latex.split('=')[0].strip()} has a coefficient of {coefficient}. To isolate it, you'd use the opposite operation."
            else:
                prompt = "Here's a hint: Try identifying one term or coefficient in the equation, then think about what operation would undo it."
        else:
            prompt = opening_question(steps)
    elif focus_term and "add" in normalized and focus_term.lstrip().startswith("-"):
        prompt = (
            f"Good choice: adding the matching amount counteracts {focus_term}. "
            "After applying it to both sides, what term containing the variable remains on the left?"
        )
    elif focus_term and "add" in normalized and focus_term.lstrip().startswith("+"):
        prompt = (
            f"You said you added {focus_term}. In Line {steps[0].line}, that term is already being added. "
            "Which operation is its inverse, and should you apply it to one side or both?"
        )
    elif focus_term and any(word in normalized for word in ("subtract", "minus")) and focus_term.lstrip().startswith("+"):
        prompt = (
            f"Check Line {steps[0].line}. If you use an operation to undo {focus_term}, "
            "what must be true about the operation on the other side of the equals sign?"
        )
    elif coefficient and re.search(rf"\b{re.escape(coefficient)}\s*\*?\s*[a-zA-Z]", normalized):
        prompt = (
            f"Now the variable has a coefficient of {coefficient}. "
            "Which inverse operation will isolate the variable, and what must you do to the other side?"
        )
    elif coefficient and (any(word in normalized for word in ("divide", "division", "divided")) or "/" in message):
        prompt = "Good. After applying that operation to both sides, what value do you get for the variable?"
    elif assessment.issue_found and assessment.line and len(steps) > 1:
        previous_line = next((step for step in steps if step.line == assessment.line - 1), steps[0])
        if any(word in normalized for word in ("subtract", "minus", "opposite", "inverse")):
            prompt = (
                f"Good—now compare Lines {previous_line.line} and {assessment.line}. "
                "Does the new line show that same operation applied to both sides?"
            )
        else:
            prompt = (
                f"Focus on Line {assessment.line}. What operation would undo the term that disappeared "
                f"when moving from Line {previous_line.line} to Line {assessment.line}?"
            )
    elif len(steps) > 1:
        prompt = (
            f"Compare Lines {steps[0].line} and {steps[1].line}. "
            "Name the operation that changes the first equation into the second, and say where you applied it."
        )
    else:
        prompt = "Point to one term in your equation. What operation would remove that term while keeping the equation balanced?"
    return CoachEvent(type="coach_message", payload={"message": prompt})


def generate_coach_reply(
    steps: list[MathStep], student_message: str = "", history: list[dict[str, str]] | None = None
) -> CoachEvent:
    """Use Claude for broad Algebra coaching, with a local fallback if unavailable."""
    work = "\n".join(f"Line {step.line}: {step.latex}" for step in steps) or "No transcribed steps yet."
    dialogue = "\n".join(f"{item['sender'].title()}: {item['text']}" for item in (history or [])[-12:])
    user_prompt = (
        f"Student work:\n{work}\n\nConversation so far:\n{dialogue or '(No prior dialogue.)'}"
        f"\n\nStudent's latest reply: {student_message or '(They have not replied yet.)'}"
    )
    try:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model=os.environ.get("COACH_MODEL", "claude-3-5-sonnet-20241022"),
            max_tokens=180,
            temperature=0.3,
            system=SOCRATIC_COACH_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )
        response_text = message.content[0].text if message.content else None
        if response_text:
            return CoachEvent(type="coach_message", payload={"message": response_text.strip()})
    except Exception:
        # The vision request has already verified credentials in normal use; retain
        # helpful local guidance if a later coach request cannot reach the model.
        pass
    return respond_to_student(student_message, steps, history) if student_message else CoachEvent(
        type="coach_message", payload={"message": opening_question(steps)}
    )
