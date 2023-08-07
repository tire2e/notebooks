from collections import Counter, defaultdict
from datetime import datetime
from json import load
from numpy import mean, median
from os.path import join

badges = {'e2e', 'tir', 'colab', 'youtube', 'git', 'wiki', 'kaggle', 'arxiv', 'tf', 'pt', 'medium', 'reddit', 'neurips', 'paperswithcode', 'huggingface', 'docs', 'slack', 'twitter', 'deepmind', 'discord'}

TIR_BASE_URL = "https://gpu-notebooks.e2enetworks.com"
TOP_K = 2  # TODO


def format_tir_url(url: str) -> str:
    return url.format(tir_base_url=TIR_BASE_URL)


def tir_url(url: str) -> str:
    url = format_tir_url(url)
    return f'[![Open In TIR](images/open-in-tir.png)]({url})'


def doi_url(url: str) -> str:
    doi = url.split('org/')[1]
    return f'[![](https://api.juleskreuer.eu/citation-badge.php?doi={doi})]({url})'


def git_url(url: str) -> str:
    repo = '/'.join(url.split('com/')[1].split('/')[:2])
    return f'[![](https://img.shields.io/github/stars/{repo}?style=social)]({url})'


def read_json(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        return load(f)


def parse_link(link_tuple: list[list[str, str]], height=20) -> str:
    name, url = link_tuple
    if name in badges:
        return f'[<img src="images/{name}.svg" alt="{name}" height={height}/>]({url})'
    return f'[{name}]({url})'


def parse_authors(authors: list[tuple[str, str]], num_of_visible: int) -> str:
    num_authors = len(authors)
    if num_authors == 1:
        return "[{}]({})".format(*authors[0])

    elif num_authors <= num_of_visible + 1:
        return (
            "<ul>"
            + " ".join(
                f"<li>[{author}]({link})</li>" for author, link in authors[: num_of_visible + 1]
            )
            + "</ul>"
        )

    else:
        return (
            "<ul>"
            + " ".join(
                f"<li>[{author}]({link})</li>" for author, link in authors[:num_of_visible]
            )
            + "<details><summary>others</summary>"
            + " ".join(
                f"<li>[{author}]({link})</li>" for author, link in authors[num_of_visible:]
            )
            + "</ul></details>"
        )


def parse_links(list_of_links: list[tuple[str, str]]) -> str:
    if len(list_of_links) == 0:
        return ""

    dct = defaultdict(list)
    for tupl in list_of_links:
        name, url = tupl[0], tupl[1]
        dct[name].append(url)

    line = ""
    if "doi" in dct:
        line += doi_url(dct["doi"][0]) + " "
        dct.pop("doi")
    if "git" in dct:
        line += git_url(dct["git"][0]) + " "
        if len(dct["git"]) == 1:
            dct.pop("git")
        else:
            dct["git"].pop(0)
    if len(dct) == 0:
        return line

    return (
        line
        + "<ul>"
        + "".join(
            "<li>" + ", ".join(parse_link((name, url)) for url in dct[name]) + "</li>"
            for name in dct.keys()
        )
        + "</ul>"
    )


def get_top_authors(topK) -> tuple[str, int]:
    global TOP_K
    research = read_json(join("data", "research.json"))
    tutorials = read_json(join("data", "tutorials.json"))

    authors, num_of_authors = [], []
    for project in research + tutorials:
        authors.extend([tuple(author) for author in project["author"]])
        num_of_authors.append(len(project["author"]))

    cnt = Counter(authors)
    most_common = cnt.most_common()
    contributions = most_common[topK][1]
    idx = topK
    while most_common[idx][1] == contributions:
        idx += 1
    num_of_visible = int(min(mean(num_of_authors), median(num_of_authors)))
    print(f"idx={idx}")
    TOP_K = idx

    return (
        "<ul>"
        + " ".join(
            f"<li>[{author}]({link})</li>" for (author, link), _ in most_common[:idx]
        )
        + "</ul>",
        num_of_visible,
    )


def get_top_repos(topK) -> str:
    research = read_json(join("data", "research.json"))
    tutorials = read_json(join("data", "tutorials.json"))

    repos = set()
    for project in research + tutorials:
        for link in project["links"]:
            if link[0] == "git":
                repos.add((link[1], link[2]))
                break
    repos = sorted(repos, key=lambda f: f[1], reverse=True)[:topK]
    print(len(repos), repos)

    return (
        "<ul>"
        + " ".join(
            f"<li>{'/'.join(url.split('com/')[1].split('/')[:2])} {git_url(url)}</li>" for url, _ in repos
        )
        + "</ul>"
    )


def get_best_of_the_best(authors: str, topK: int) -> str:
    table = f'''| Top Authors | Top Repositories |
|---|---|
| {authors} | {get_top_repos(topK)} |'''
    return table


def generate_table(fn: str, num_visible_authors: int, f):
    data = read_json(fn)
    colabs = sorted(data, key=lambda kv: kv['update'], reverse=True)

    print('| Name | Description | Authors | Links | <div style="width:207px">Open in TIR</div> |', file=f)
    print('|------|-------------|:--------|:------|:-----------:|', file=f)
    for line in colabs:
        nb_item = {
            "name": line["name"],
            "description": line["description"],
            "author": parse_authors(line['author'], num_visible_authors),
            "links": parse_links(sorted(line['links'], key=lambda x: x[0])),
            "url": tir_url(line['tir_url']),
            # "update": datetime.fromtimestamp(line['update']).strftime('%d.%m.%Y'),
        }
        print('| {name} | {description} | {author} | {links} | {url} |'.format(**nb_item), file=f)


def generate_markdown():
    top_authors, num_visible_authors = get_top_authors(TOP_K)
    with open('README.md', 'w', encoding='utf-8') as f:
        # print('[![Hits](https://hits.seeyoufarm.com/api/count/incr/badge.svg?url=https://github.com/tire2e/notebooks)](https://hits.seeyoufarm.com)', file=f)
        print('# Some popular notebooks\' collection for ML experiments', file=f)
        print('## Research', file=f)
        generate_table(join('data', 'research.json'), num_visible_authors, f)
        print('## Tutorials', file=f)
        generate_table(join('data', 'tutorials.json'), num_visible_authors, f)
        print('# Best of the best', file=f)
        print(get_best_of_the_best(top_authors, TOP_K), file=f)
        # print('\n[![Stargazers over time](https://starchart.cc/tire2e/notebooks.svg)](https://starchart.cc/tire2e/notebooks)', file=f)
        # print(f'\n(generated by [generate_markdown.py](generate_markdown.py) based on [research.json](data/research.json) and [tutorials.json](data/tutorials.json))', file=f)


def main():
    generate_markdown()


if __name__ == '__main__':
    main()
