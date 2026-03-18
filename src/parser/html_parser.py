from bs4 import BeautifulSoup, Tag
from typing import Dict, Any, List, Optional
import re


def _text_or_none(el):
    return el.get_text(strip=True) if el else None


def extract_id_from_url(url: str) -> str:
    parts = url.rstrip('/').split('/')
    return parts[-1] if parts else url


def _find_exercise_section(soup: BeautifulSoup, exercise_num: int) -> Optional[Tag]:
    """Find the container div for a given exercise number.

    Engoo uses anchor links like href="...#exercise-N". We find such an anchor,
    then walk up the DOM to the container that has 3+ direct div children
    (header, instruction, content).
    """
    pattern = re.compile(rf'#exercise-{exercise_num}$')
    anchors = soup.find_all('a', href=pattern)
    if not anchors:
        return None
    a = anchors[0]
    section = a.parent
    while section and section.parent:
        section = section.parent
        if not isinstance(section, Tag):
            continue
        children = section.find_all('div', recursive=False)
        if len(children) >= 3:
            return section
    return None


def parse_vocabulary(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract vocabulary items from Exercise 1.

    Each vocab item contains a link to /app/words/word/ with the word text.
    The word's container (data-mouseover-dictionary-disabled) holds part of speech.
    The sibling div holds phonetics, definition, and example sentence.
    """
    items = []
    section = _find_exercise_section(soup, 1)
    if not section:
        return {'label': 'Vocabulary', 'items': items}

    word_links = section.find_all('a', href=re.compile(r'/app/words/word/'))
    for link in word_links:
        word = link.get_text(strip=True)
        pos = None
        phonetics = None
        definition = None
        example = None

        definition_ja = None
        example_ja = None

        # Navigate to the word container div (has data-mouseover-dictionary-disabled)
        word_container = link.find_parent(
            'div', attrs={'data-mouseover-dictionary-disabled': ''}
        )
        if word_container:
            # Part of speech is in a span within a css-1no1tp4 div
            for span in word_container.find_all('span'):
                text = span.get_text(strip=True)
                if text and text not in (word, '') and not span.find('a'):
                    # Filter to likely POS labels (Japanese or English)
                    if re.match(r'^[a-zA-Zぁ-んァ-ヶ一-龠々ー]+$', text):
                        pos = text
                        break

            # Japanese definition is in a span[lang="ja"] inside the word container
            for ja_span in word_container.find_all('span', attrs={'lang': 'ja'}):
                t = ja_span.get_text(strip=True)
                if t:
                    definition_ja = t
                    break

            # The detail div is a sibling of word_container
            detail_div = word_container.find_next_sibling('div')
            if detail_div:
                # Find divs that contain phonetics and definition
                # They are typically in separate child divs
                info_spans = detail_div.find_all('span', class_='css-l5xv05')
                texts = []
                for sp in info_spans:
                    # Skip spans that contain nested spans with lang attr (those are translations)
                    if sp.find('span', attrs={'lang': True}):
                        continue
                    t = sp.get_text(strip=True)
                    if t:
                        texts.append(t)

                if len(texts) >= 2:
                    phonetics = texts[0]
                    definition = texts[1]
                elif len(texts) == 1:
                    definition = texts[0]

                # Example sentence contains a <strong> tag with the vocab word
                strong = detail_div.find('strong')
                if strong and strong.parent:
                    # Get text with proper spacing around the bold word
                    example_parts = []
                    for child in strong.parent.children:
                        if isinstance(child, Tag) and child.name == 'strong':
                            example_parts.append(child.get_text())
                        elif isinstance(child, Tag):
                            example_parts.append(child.get_text())
                        else:
                            example_parts.append(str(child))
                    example = ''.join(example_parts).strip()

                # Japanese example sentence is in a span[lang="ja"] in the detail div
                for ja_span in detail_div.find_all('span', attrs={'lang': 'ja'}):
                    t = ja_span.get_text(strip=True)
                    if t:
                        example_ja = t
                        break

        items.append({
            'word': word,
            'phonetics': phonetics or None,
            'part_of_speech': pos or None,
            'definition': definition or None,
            'definition_ja': definition_ja or None,
            'example': example or None,
            'example_ja': example_ja or None,
        })

    return {'label': 'Vocabulary', 'items': items}


def parse_article_body(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extract article body from Exercise 2."""
    section = _find_exercise_section(soup, 2)
    paragraphs = []

    if section:
        # Article paragraphs are in <p> tags or lang="en" spans within the content area
        children = section.find_all('div', recursive=False)
        if len(children) >= 3:
            content = children[2]  # Third child is the content
            for p in content.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)

    # Fallback: try generic selectors
    if not paragraphs:
        body_el = soup.select_one('.article-body, .article-content, .content')
        if not body_el:
            body_el = soup.find('article') or soup.find('main')
        if body_el:
            for p in body_el.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    paragraphs.append(text)

    body = "\n\n".join(paragraphs)
    return {'label': 'Article', 'body': body, 'paragraphs': paragraphs}


def _parse_discussion_section(soup: BeautifulSoup, exercise_num: int) -> Dict[str, Any]:
    """Extract discussion questions from a given exercise section.

    Questions are numbered (1., 2., etc.) and the question text is in lang="en" spans.
    """
    label = 'Discussion' if exercise_num == 3 else 'Further Discussion'
    questions = []
    section = _find_exercise_section(soup, exercise_num)
    if not section:
        return {'label': label, 'questions': questions}

    children = section.find_all('div', recursive=False)
    if len(children) < 3:
        return {'label': label, 'questions': questions}

    content = children[2]  # Third child is the content

    # Find all question text spans with lang="en"
    en_spans = content.find_all('span', attrs={'lang': 'en'})
    for span in en_spans:
        text = span.get_text(strip=True)
        if text and len(text) > 5:  # Filter out empty or trivial spans
            questions.append(text)

    return {'label': label, 'questions': questions}


def parse_article(html: str, url: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, 'lxml')
    # Title
    title = None
    title_el = soup.find('h1') or soup.select_one('.title')
    if title_el:
        title = title_el.get_text(strip=True)
    else:
        og = soup.select_one('meta[property="og:title"]')
        if og and og.get('content'):
            title = og.get('content')

    # Level: look for text containing Beginner/Intermediate/Advanced
    level = 'Unknown'
    text = soup.get_text(' ', strip=True)
    m = re.search(r"\b(Beginner|Intermediate|Advanced)\b", text, re.IGNORECASE)
    if m:
        level = m.group(1).capitalize()

    vocab = parse_vocabulary(soup)
    article = parse_article_body(soup)
    discussion = _parse_discussion_section(soup, 3)
    further = _parse_discussion_section(soup, 4)

    parsed = {
        'id': extract_id_from_url(url),
        'meta': {
            'title': title,
            'title_ja': None,
            'level': level,
            'category': None,
            'url': url,
            'thumbnail_url': None,
            'published_date': None,
            'scraped_at': None,
        },
        'exercises': {
            'exercise_1_vocabulary': vocab,
            'exercise_2_article': article,
            'exercise_3_discussion': discussion,
            'exercise_4_further_discussion': further,
        }
    }
    return parsed
