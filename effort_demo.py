import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY

MODEL = "claude-opus-4-8"  # same model for every call — only effort changes
PROMPT = (
    "A train leaves at 14:35 going 80 km/h. A second leaves the same station "
    "at 15:05 going 110 km/h on the same track. When and where does the second "
    "catch the first?"
)


def ask(effort: str) -> None:
    """Run the same prompt at a given effort level and report the tradeoff."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        thinking={"type": "adaptive"},      # let Claude decide how much to think
        output_config={"effort": effort},    # <-- the dial
        messages=[{"role": "user", "content": PROMPT}],
    )

    answer = next((b.text for b in resp.content if b.type == "text"), "")
    print(f"\n=== effort={effort} ===")
    print(answer.strip())
    print(f"[tokens] in={resp.usage.input_tokens} out={resp.usage.output_tokens}")


# Same model, same prompt — you turn the dial, not swap the model.
for level in ["low", "medium", "high", "xhigh", "max"]:
    ask(level)
