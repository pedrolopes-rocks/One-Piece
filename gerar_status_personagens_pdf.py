from __future__ import annotations

from pathlib import Path

from game_data import CHARACTERS


OUTPUT = Path(__file__).with_name("status_personagens.pdf")
PAGE_WIDTH = 842
PAGE_HEIGHT = 595
MARGIN = 42


def fix_text(value: str) -> str:
    """Corrige textos UTF-8 que foram carregados como Latin-1."""
    try:
        return value.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return value


def pdf_text(value: str) -> str:
    encoded = fix_text(value).encode("cp1252", errors="replace")
    text = encoded.decode("latin-1")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def text_command(x: int, y: int, text: str, size: int = 10, bold: bool = False) -> str:
    font = "F2" if bold else "F1"
    return f"BT /{font} {size} Tf {x} {y} Td ({pdf_text(text)}) Tj ET"


def line_command(x1: int, y1: int, x2: int, y2: int, gray: float = 0.82) -> str:
    return f"{gray} G {x1} {y1} m {x2} {y2} l S 0 G"


def build_pages() -> list[bytes]:
    pages: list[bytes] = []
    per_page = 6
    total_pages = (len(CHARACTERS) + per_page - 1) // per_page

    for page_index in range(total_pages):
        commands = [
            text_command(MARGIN, PAGE_HEIGHT - 38, "Status dos Personagens", 18, True),
            text_command(
                PAGE_WIDTH - 122,
                PAGE_HEIGHT - 34,
                f"Página {page_index + 1} de {total_pages}",
                9,
            ),
            line_command(MARGIN, PAGE_HEIGHT - 48, PAGE_WIDTH - MARGIN, PAGE_HEIGHT - 48, 0.45),
        ]

        start = page_index * per_page
        for slot, character in enumerate(CHARACTERS[start : start + per_page]):
            top = PAGE_HEIGHT - 78 - slot * 82
            name = fix_text(character["name"])
            roles = ", ".join(fix_text(role) for role in character["roles"])
            skills = character["skills"]
            skill_values = " | ".join(
                f"{fix_text(role)}: {value}" for role, value in skills.items()
            )

            commands.extend(
                [
                    text_command(MARGIN, top, name, 13, True),
                    text_command(MARGIN + 205, top, f"Rank: {character['rank']}", 11, True),
                    text_command(
                        MARGIN + 305,
                        top,
                        f"Ataque: {character['attack']}   Defesa: {character['defense']}",
                        10,
                    ),
                    text_command(MARGIN, top - 19, f"Função(ões): {roles}", 10),
                    text_command(MARGIN, top - 38, f"Status de função: {skill_values}", 9),
                    line_command(MARGIN, top - 54, PAGE_WIDTH - MARGIN, top - 54),
                ]
            )

        pages.append(("\n".join(commands) + "\n").encode("latin-1"))

    return pages


def write_pdf(path: Path) -> None:
    page_streams = build_pages()
    page_count = len(page_streams)
    first_page_object = 5
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        (
            "<< /Type /Pages /Kids ["
            + " ".join(f"{first_page_object + index * 2} 0 R" for index in range(page_count))
            + f"] /Count {page_count} >>"
        ).encode("ascii"),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
    ]

    for index, stream in enumerate(page_streams):
        page_object = first_page_object + index * 2
        content_object = page_object + 1
        objects.append(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                f"/Contents {content_object} 0 R >>"
            ).encode("ascii")
        )
        objects.append(
            f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")
            + stream
            + b"endstream"
        )

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_number, content in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_number} 0 obj\n".encode("ascii"))
        pdf.extend(content)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))

    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(pdf)


if __name__ == "__main__":
    write_pdf(OUTPUT)
    print(f"PDF gerado: {OUTPUT}")
