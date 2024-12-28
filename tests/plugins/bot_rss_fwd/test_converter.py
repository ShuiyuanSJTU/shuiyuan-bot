import pytest
from bs4 import BeautifulSoup

@pytest.fixture(autouse=True)
def auto_patch(patch_bot_config, patch_bot_kv_storage):
    yield

@pytest.mark.parametrize('html, expected', [
    ('<h1>hello</h1>', '# hello\n'),
    ('<h2>hello</h2>', '## hello\n'),
    ('<h3>hello</h3>', '### hello\n'),
    ('<h1>hello</h1><h2>hello</h2><h3>hello</h3>', '# hello\n## hello\n### hello\n'),
])
def test_render_h(html, expected):
    from backend.plugins.bot_rss_fwd.markdown_converter import render_md
    element = BeautifulSoup(html, 'lxml')
    assert render_md(element) == expected

@pytest.mark.parametrize('html, expected', [
    ('<p></p>', '\n'),
    ('<p>  </p>', '\n'),
    ('<p>hello</p>', 'hello\n'),
    # p tags should not be nested, lxml will close the previous p tag
    ('<p><p>123</p></p>', '\n123\n'),
])
def test_render_p(html, expected):
    from backend.plugins.bot_rss_fwd.markdown_converter import render_md
    element = BeautifulSoup(html, 'lxml')
    assert render_md(element) == expected

@pytest.mark.parametrize('html, expected', [
    ('<br>', '\n'),
    ('<br><br>', '\n\n'),
])
def test_render_br(html, expected):
    from backend.plugins.bot_rss_fwd.markdown_converter import render_md
    element = BeautifulSoup(html, 'lxml')
    assert render_md(element) == expected

@pytest.mark.parametrize('html, expected', [
    ('<img src="https://example.com/image.jpg">', '![](https://example.com/image.jpg)'),
    ('<img src="https://example.com/image.jpg" alt="image">', '![image](https://example.com/image.jpg)'),
    ('<img src="https://example.com/image.jpg" alt="image"><img src="https://example.com/image.jpg" alt="image">', '![image](https://example.com/image.jpg)![image](https://example.com/image.jpg)'),
])
def test_render_img(html, expected):
    from backend.plugins.bot_rss_fwd.markdown_converter import render_md
    element = BeautifulSoup(html, 'lxml')
    assert render_md(element) == expected

@pytest.mark.parametrize('html, expected', [
    ('<a>hello</a>', '[hello]()'),
    ('<a href="https://example.com">hello</a>', '[hello](https://example.com)'),
    ('<a href="https://example.com"><span>123</span></a>', '[123](https://example.com)'),
    ('<a href="https://example.com"><strong>123</strong></a>', '[**123**](https://example.com)'),
])
def test_render_a(html, expected):
    from backend.plugins.bot_rss_fwd.markdown_converter import render_md
    element = BeautifulSoup(html, 'lxml')
    assert render_md(element) == expected

@pytest.mark.parametrize('html, expected', [
    ('<table><tr><td>hello</td></tr></table>', '<table><tr><td>hello</td></tr></table>\n'),
    ('<table id="tab"><tr class="tab1"><td style="">test</td></tr></table>', '<table><tr><td>test</td></tr></table>\n')
])
def test_render_table(html, expected):
    from backend.plugins.bot_rss_fwd.markdown_converter import render_md
    element = BeautifulSoup(html, 'lxml')
    assert render_md(element) == expected

@pytest.mark.parametrize('html, expected', [
    ('<strong>hello</strong>', ' **hello** '),
    ('<strong><strong>hello</strong></strong>', ' **hello** '),
    ('<em>hello</em>', ' *hello* '),
    ('<em><em>hello</em></em>', ' *hello* '),
    ('<strong><em>hello</em></strong>', ' ***hello*** '),
    ('<em><strong>hello</strong></em>', ' ***hello*** '),
    ('<strong>hello</strong><em>hello</em>', ' **hello**  *hello* '),
])
def test_render_style(html, expected):
    from backend.plugins.bot_rss_fwd.markdown_converter import render_md
    element = BeautifulSoup(html, 'lxml')
    assert render_md(element) == expected

@pytest.mark.parametrize('html, expected', [
    ('<strong>hello</strong><strong>hello</strong>', ' **hellohello** '),
    ('<em>hello</em><em>hello</em>', ' *hellohello* '),
    ('<strong>hello<em>hello</em></strong>', ' **hello**  ***hello*** '),
])
def test_merge_neibours(html, expected):
    from backend.plugins.bot_rss_fwd.markdown_converter import render_md
    element = BeautifulSoup(html, 'lxml')
    assert render_md(element) == expected

@pytest.mark.parametrize('html, expected', [
    ('<span>https://example.com/一二三</span>', 'https://example.com/ 一二三'),
    ('<p>https://example.com/一二三</p>', 'https://example.com/ 一二三\n'),
])
def test_fix_url_in_text_node(html, expected):
    from backend.plugins.bot_rss_fwd.markdown_converter import render_md
    element = BeautifulSoup(html, 'lxml')
    assert render_md(element) == expected

@pytest.mark.parametrize('html, expected', [
    ('<p>hello</p><p>hello</p>', 'hello\nhello\n'),
    ('<p>hello</p><br><p>hello</p>', 'hello\n\nhello\n'),
    ('<span>1</span><span>2</span><p>3</p>', '12\n3\n'),
    ('<span>1</span><span>2</span><h1>3</h1>', '12\n# 3\n'),
])
def test_instert_breakline(html, expected):
    from backend.plugins.bot_rss_fwd.markdown_converter import render_md
    element = BeautifulSoup(html, 'lxml')
    assert render_md(element) == expected