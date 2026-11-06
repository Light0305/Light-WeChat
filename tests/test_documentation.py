from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
import markdown


def test_owned_markdown_links_resolve():
    root = Path(__file__).resolve().parents[1]
    missing = []
    paths = [*root.glob('*.md'), *root.joinpath('references').rglob('*.md'),
             *root.joinpath('assets/readme').glob('*.md')]
    for path in paths:
        soup = BeautifulSoup(markdown.markdown(path.read_text(encoding='utf-8-sig'),
                                               extensions=['tables', 'fenced_code']), 'html.parser')
        targets = [node[attr] for tag, attr in [('a', 'href'), ('img', 'src')]
                   for node in soup.find_all(tag) if node.get(attr)]
        targets += [candidate.strip().split()[0] for node in soup.find_all('source')
                    for candidate in node.get('srcset', '').split(',') if candidate.strip()]
        for target in targets:
            if urlsplit(target).scheme or target.startswith('#'):
                continue
            destination = unquote(urlsplit(target).path)
            if destination and not (path.parent / destination).exists():
                missing.append((path.relative_to(root).as_posix(), destination))
    assert missing == []


def test_bilingual_readme_showcase_and_contact_order():
    root = Path(__file__).resolve().parents[1]
    for name, alternate in [('README.md', 'README.zh-CN.md'), ('README.zh-CN.md', 'README.md')]:
        soup = BeautifulSoup(markdown.markdown((root / name).read_text(encoding='utf-8'),
                                               extensions=['tables', 'fenced_code']), 'html.parser')
        assert soup.find('a', href=alternate)
        assert soup.find('picture').find('source')['srcset'].endswith('logo-dark.svg')
        assert len(soup.find_all('img', src='assets/readme/site-home.png')) == 1
        table = soup.find('img', src='assets/readme/wechat-contact.png').find_parent('table')
        assert table['align'] == 'center'
        assert [image['src'].rsplit('/', 1)[-1] for image in table.find_all('img')] == [
            'wechat-donation.jpg', 'wechat-contact.png', 'wechat-official-account.jpg']
        assert all(cell.get('align') == 'center' for cell in table.find_all('td'))
        assert '/Light-WeChat --skill light-wechat' in soup.get_text()
    assert (root / 'SKILL.md').read_text(encoding='utf-8').splitlines()[1] == 'name: light-wechat'
