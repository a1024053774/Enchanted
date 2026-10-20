"""T-113 产品页链接检查：内部锚点与相对文件必须存在；外链逐个请求，记录最终状态码。

用法：python3 check_links.py <docs 目录> [--offline]
"""
import sys
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs = set(), []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for name in ('href', 'src'):
            if attrs.get(name):
                self.refs.append((tag, name, attrs[name]))


def status(url):
    request = urllib.request.Request(url, method='GET', headers={'User-Agent': 'T-113-link-check'})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.url
    except urllib.error.HTTPError as error:
        return error.code, url
    except Exception as error:  # 网络错误照实记录，不当作通过
        return f'error: {error}', url


def main():
    root = Path(sys.argv[1]).resolve()
    offline = '--offline' in sys.argv
    failures = 0
    for page in sorted(root.rglob('*.html')):
        collector = Collector()
        collector.feed(page.read_text(encoding='utf-8'))
        print(f'## {page.relative_to(root)}: {len(collector.refs)} 个引用')
        for tag, name, ref in collector.refs:
            if ref.startswith('data:'):
                continue
            if ref.startswith('#'):
                ok = ref[1:] in collector.ids
                print(f"{'PASS' if ok else 'FAIL'}  锚点 {ref}")
            elif ref.startswith(('http://', 'https://')):
                if offline:
                    print(f'SKIP  外链 {ref}')
                    continue
                code, final = status(ref)
                ok = code == 200
                print(f"{'PASS' if ok else 'FAIL'}  外链 {ref} -> {code}{'' if final == ref else ' ' + final}")
            else:
                target = (page.parent / ref.split('#')[0].split('?')[0]).resolve()
                ok = target.is_file() and root in target.parents
                print(f"{'PASS' if ok else 'FAIL'}  文件 {ref}")
            failures += not ok
    print(f'\n失败 {failures} 项')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
