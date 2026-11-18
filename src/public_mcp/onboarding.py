"""User-selected starter prompts; no credentials or database access required."""

STARTER_PROMPTS = {
    "getting_started": (
        "Get started",
        "Welcome me briefly and help me get started with card rewards research. "
        "Explain that I can ask a question immediately or add my cards for tailored guidance. "
        "Use get_portfolio to check existing cards before asking me to enter them. "
        "If reading fails, explain that without assuming my portfolio is empty. "
        "Ask whether I want to set up my portfolio, explore my next card, or evaluate a redemption. "
        "Use 'you', never an internal owner key or connection secret. "
        "Do not repeat the welcome during this conversation unless I ask to start over.",
    ),
    "build_portfolio": (
        "Set up my portfolio",
        "Help me add my cards to my portfolio. Read get_portfolio first to avoid re-entry. "
        "Collect issuer, product, opening date, annual fee, business status, and personal-credit "
        "reporting status for each card. Tell me ballpark dates and fees are fine. Ask for missing "
        "facts without guessing; save an approximate month as its first day and say so. Never request "
        "account numbers or credentials. Use add_portfolio_card for the cards I ask to save, "
        "then summarize successful additions and anything still missing. Do not claim a save "
        "succeeded unless the tool confirms it. Offer optional points/miles balance entry by program. "
        "Read get_point_balances first, resolve names with list_point_programs, and use "
        "set_point_balance only for totals I ask you to save. Never infer a balance from my cards.",
    ),
    "next_card": (
        "Explore my next card",
        "Help me explore my next credit card using my saved portfolio and current research. "
        "Read get_portfolio, ask about my goals and relevant spending, and explain tradeoffs "
        "and any missing eligibility information. Cite dated evidence and verify issuer terms. "
        "Do not promise approval or bonus eligibility, or claim my goals have been saved.",
    ),
    "evaluate_redemption": (
        "Evaluate a points redemption",
        "Help me compare a points redemption with paying cash. Ask for the program, points "
        "required, cash price, and taxes or fees, then use the available valuation tools. "
        "Use get_point_balances when my available points matter, noting the recorded dates. "
        "Explain the assumptions and tradeoffs without requiring portfolio setup first.",
    ),
}


def register_starter_prompts(mcp):
    for name, (title, text) in STARTER_PROMPTS.items():
        # A factory avoids leaking the template text as a prompt argument.
        def make_prompt(content):
            def starter() -> str:
                return content

            return starter

        mcp.prompt(name=name, title=title, description=title)(make_prompt(text))
