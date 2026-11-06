from manual_spss.content_model.html_text import html_to_plain_text


def test_html_to_plain_text_preserves_block_and_line_breaks() -> None:
    body = "<h1>Título</h1><p>Texto <strong>importante</strong>.</p><p>Fin.</p>"

    assert html_to_plain_text(body) == "Título\nTexto importante.\nFin."


def test_html_to_plain_text_ignores_scripts_styles_and_comments() -> None:
    body = (
        "<p>Visible</p><script>secret()</script><style>.x { color: red; }</style>"
        "<!-- comentario oculto --><p>También visible</p>"
    )

    assert html_to_plain_text(body) == "Visible\nTambién visible"


def test_html_to_plain_text_decodes_entities_and_normalizes_whitespace() -> None:
    body = "<p>  ¿Qué&nbsp;es SPSS? &amp; ¿para qué sirve?  </p><p>  Fin  </p>"

    assert html_to_plain_text(body) == "¿Qué es SPSS? & ¿para qué sirve?\nFin"


def test_html_to_plain_text_returns_empty_string_for_empty_input() -> None:
    assert html_to_plain_text("") == ""
