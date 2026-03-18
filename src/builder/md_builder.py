from typing import Dict, Any


def to_markdown(article: Dict[str, Any]) -> str:
    """Convert a parsed article dict to Markdown format."""
    lines = []
    meta = article.get('meta', {})
    exercises = article.get('exercises', {})

    # Title
    title = meta.get('title') or article.get('id', 'Untitled')
    lines.append(f"# {title}")
    lines.append("")

    # Meta
    level = meta.get('level')
    url = meta.get('url')
    published = meta.get('published_date')
    if level:
        lines.append(f"**Level:** {level}")
    if published:
        lines.append(f"**Published:** {published}")
    if url:
        lines.append(f"**URL:** {url}")
    if level or published or url:
        lines.append("")

    # Exercise 1: Vocabulary
    vocab = exercises.get('exercise_1_vocabulary', {})
    items = vocab.get('items', [])
    if items:
        lines.append("---")
        lines.append("")
        lines.append("## Exercise 1: Vocabulary")
        lines.append("")
        for item in items:
            word = item.get('word', '')
            phonetics = item.get('phonetics')
            pos = item.get('part_of_speech')
            definition = item.get('definition', '')
            definition_ja = item.get('definition_ja')
            example = item.get('example')
            example_ja = item.get('example_ja')

            # Word heading with phonetics and POS
            heading_parts = [f"### {word}"]
            sub_parts = []
            if phonetics:
                sub_parts.append(f"/{phonetics}/")
            if pos:
                sub_parts.append(f"*{pos}*")
            if sub_parts:
                heading_parts.append(" ".join(sub_parts))
            lines.append(heading_parts[0])
            if len(heading_parts) > 1:
                lines.append(heading_parts[1])
            lines.append("")

            # Definition
            lines.append(f"**Definition:** {definition}")
            if definition_ja:
                lines.append(f"**定義:** {definition_ja}")
            lines.append("")

            # Example
            if example:
                lines.append(f"> {example}")
                if example_ja:
                    lines.append(f">")
                    lines.append(f"> *{example_ja}*")
                lines.append("")

    # Exercise 2: Article
    article_ex = exercises.get('exercise_2_article', {})
    paragraphs = article_ex.get('paragraphs', [])
    if paragraphs:
        lines.append("---")
        lines.append("")
        lines.append("## Exercise 2: Article")
        lines.append("")
        for p in paragraphs:
            lines.append(p)
            lines.append("")

    # Exercise 3: Discussion
    disc = exercises.get('exercise_3_discussion', {})
    questions = disc.get('questions', [])
    if questions:
        lines.append("---")
        lines.append("")
        lines.append("## Exercise 3: Discussion")
        lines.append("")
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q}")
        lines.append("")

    # Exercise 4: Further Discussion
    further = exercises.get('exercise_4_further_discussion', {})
    questions = further.get('questions', [])
    if questions:
        lines.append("---")
        lines.append("")
        lines.append("## Exercise 4: Further Discussion")
        lines.append("")
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q}")
        lines.append("")

    return "\n".join(lines)
