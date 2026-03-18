from src.parser.html_parser import parse_article


def test_parse_sample_fixture():
    path = 'tests/fixtures/sample_article.html'
    html = open(path, 'r', encoding='utf-8').read()
    url = 'https://engoo.jp/app/daily-news/articles/BttvaDsYEeet95PQUY-xEA'
    parsed = parse_article(html, url)

    assert parsed['id'] == 'BttvaDsYEeet95PQUY-xEA'
    assert parsed['meta']['title'] == 'AI Robot Becomes New Friend for Lonely Elderly'
    assert parsed['meta']['level'] == 'Intermediate'
    assert parsed['exercises']['exercise_1_vocabulary']['items'][0]['word'] == 'companion'
    assert len(parsed['exercises']['exercise_2_article']['paragraphs']) == 2
    assert 'AI companions' in parsed['exercises']['exercise_3_discussion']['questions'][0]
