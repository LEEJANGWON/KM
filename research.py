"""Free, source-backed literature monitor; no clinical inference or paid API."""
import argparse
import datetime as dt
import json
from pathlib import Path
import time
import urllib.parse
import urllib.request

TOPICS = {
    '침': 'acupuncture',
    '부항': 'cupping therapy',
    '추나': 'Chuna OR Tuina',
    '한약': 'Korean herbal medicine OR Chinese herbal medicine',
}


def fetch(query, limit):
    params = urllib.parse.urlencode({
        'query': f'({query}) AND FIRST_PDATE:[{dt.date.today() - dt.timedelta(days=90)} TO {dt.date.today()}]',
        'format': 'json', 'resultType': 'core', 'pageSize': limit,
        'sort': 'FIRST_PDATE_D desc',
    })
    url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?' + params
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                return json.load(response)['resultList']['result']
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def summarize(items):
    seen, papers = set(), []
    for item in items:
        identity = (item.get('source'), item.get('id'))
        if not all(identity) or identity in seen:
            continue
        seen.add(identity)
        papers.append({
            'title': item.get('title', ''), 'year': item.get('pubYear'),
            'source': identity[0], 'id': identity[1], 'doi': item.get('doi'),
            'url': 'https://europepmc.org/article/' + '/'.join(map(urllib.parse.quote, identity)),
            'publication_types': item.get('pubTypeList', {}).get('pubType', []),
            'abstract': item.get('abstractText', ''),
            'status': 'unreviewed; publication type is not evidence quality',
        })
    return papers


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='results')
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.limit <= 25:
        parser.error('--limit must be between 1 and 25')
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    report = {'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
              'mode': 'literature monitoring, no generative AI or simulated clinical outcomes',
              'topics': {}, 'errors': {}}
    for topic, query in TOPICS.items():
        try:
            report['topics'][topic] = summarize(fetch(query, args.limit))
        except Exception as exc:
            report['errors'][topic] = type(exc).__name__ + ': ' + str(exc)
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# 한의학 문헌 모니터링', '', '자동 수집 자료이며 치료 권고나 효과 검증 결과가 아닙니다.', '',
             '고전 연결 및 새로운 조합은 아직 구현되지 않았습니다. 전문가가 원문과 연구 방법을 검토해야 합니다.', '']
    for topic, papers in report['topics'].items():
        lines += [f'## {topic}', '']
        for paper in papers:
            title = paper['title'].replace('\n', ' ').replace('[', '').replace(']', '')
            lines += [f"- [{title}]({paper['url']}) — {paper['year']}; 미검토"]
        if not papers:
            lines.append('검색 기간 내 결과 없음')
        lines.append('')
    if report['errors']:
        lines += ['## 수집 실패', '', json.dumps(report['errors'], ensure_ascii=False)]
    (output / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f"Collected {sum(map(len, report['topics'].values()))} papers; failures: {len(report['errors'])}")
    if report['errors']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
