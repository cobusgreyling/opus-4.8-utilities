import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-4-8"  # mid-conversation system messages need Claude 4+

# A system prompt big enough to clear Opus's ~4096-token cache minimum,
# so cache writes vs reads are actually observable.
POLICY_LINE = "Refunds follow section 7: cite the exact subsection when answering. "
BIG_SYSTEM = "You are ACME Corp's support agent.\n" + POLICY_LINE * 1200


def system_blocks(text):
    # cache_control marks the end of the cacheable prefix
    return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]


def call(system, messages, max_tokens=128):
    return client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )


def show(label, u):
    print(
        f"{label:<40} input={u.input_tokens:>4}  "
        f"cache_write={u.cache_creation_input_tokens:>5}  "
        f"cache_read={u.cache_read_input_tokens:>5}"
    )


# --- Turn 1: cold call — writes the big system prefix into the cache ---
msgs = [{"role": "user", "content": "What's the standard refund window?"}]
r1 = call(system_blocks(BIG_SYSTEM), msgs)
show("turn 1 (cold, writes cache)", r1.usage)

answer1 = next(b.text for b in r1.content if b.type == "text")

# --- Turn 2a: inject a mid-conversation instruction as a system MESSAGE ---
# Top-level system stays byte-identical, so the cached prefix survives.
msgs_good = msgs + [
    {"role": "assistant", "content": answer1},
    {"role": "system", "content": "For this turn only: answer in one sentence and cite the subsection."},
    {"role": "user", "content": "And for damaged items?"},
]
r2 = call(system_blocks(BIG_SYSTEM), msgs_good)
show("turn 2a (system entry in messages)", r2.usage)

# --- Turn 2b (contrast): fold the same instruction into the top-level system ---
# This mutates the prefix -> cache invalidated, full re-write.
mutated = BIG_SYSTEM + "\nFor this turn only: answer in one sentence and cite the subsection."
msgs_bad = msgs + [
    {"role": "assistant", "content": answer1},
    {"role": "user", "content": "And for damaged items?"},
]
r3 = call(system_blocks(mutated), msgs_bad)
show("turn 2b (edited top-level system)", r3.usage)

print("\nturn 2a reads the cached prefix (cache_read > 0); "
      "turn 2b re-pays it (cache_write > 0, cache_read = 0).")
