def format_optional_operator(message: str, operator_name: str | None) -> str:
    if operator_name:
        return f"{message} by {operator_name}."
    else:
        return message + "."
