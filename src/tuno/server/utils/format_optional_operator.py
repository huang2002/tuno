def format_optional_operator(
    message: str,
    operator_name: str | None,
    *,
    is_player: bool,
    preposition: str = "by",
) -> str:
    if is_player:
        return f"{message} {preposition} player#{operator_name}."
    elif operator_name:
        return f"{message} {preposition} {operator_name}."
    else:
        return message + "."
