import os
import time
import argparse
from datetime import datetime
from dateutil import parser
from newspaper import Article
import feedparser
import tempfile,zipfile
import csv,json,yaml,toml
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import requests
import re
import random
from pathlib import Path
from urllib.parse import urlparse
from shutil import copyfile
import html



def download_article_content(article_url, news_date):
    article = Article(article_url, keep_article_html=True)
    print(article)
    # article.set_html(article.html.encode('utf-8', 'ignore').decode('utf-8'))
    article.download()
    article.parse()

    # soup = BeautifulSoup(article.html, 'html.parser')
    # decoded_html = html.unescape(str(soup))
    # article.set_html(decoded_html)
    # article.parse()
    # if article.publish_date.strftime('%Y-%m-%dT%H:%M:%S%z') == str(news_date):


    return article


def get_metadata(article_url):
    try:
        response = requests.get(article_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        metadata = {
            'published_time': soup.find('meta', property='article:published_time')['content'] if soup.find('meta', property='article:published_time') else None,
            'categories': [],
            'tags': [],
            'keywords': [],
        }

        categories_meta = soup.find_all('meta', property='article:section')
        tags_meta = soup.find_all('meta', property='article:tag')
        keywords_meta = soup.find('meta', attrs={'name': 'keywords'})

        for meta in categories_meta:
            metadata['categories'].extend([cat.strip() for cat in re.split(r'[/,]', meta['content'])])

        for meta in tags_meta:
            metadata['tags'].extend([tag.strip() for tag in re.split(r'[/,]', meta['content'])])

        if keywords_meta:
            metadata['keywords'] = [kw.strip() for kw in re.split(r'[/,]', keywords_meta['content'])]

        metadata['categories'] = metadata['categories'][:3]
        metadata['tags'] = metadata['tags'][:3]
        metadata['keywords'] = metadata['keywords'][:3]

        return metadata
    except Exception as e:
        print(f"Error retrieving metadata for {article_url}: {e}")
        return {}



def generate_hugo_posts(site_no, site_name, article_urls, output_dir, news_date):
    articles_list = []
    now = datetime.now()

    output_image_dir = os.path.join(output_dir, '../images')
    os.makedirs(output_image_dir, exist_ok=True)

    # alt_image_path = Path('static/images/alt.png')
    # alt_image_copy_path = os.path.join(output_image_dir, 'alt.png')
    # copyfile(alt_image_path, alt_image_copy_path)

    for index, article_url in enumerate(article_urls):
        entry = {}
        article = {}
        try:
            entry = download_article_content(article_url, news_date)

            metadata = get_metadata(article_url)
            article['categories'] = metadata['categories']
            article['tags'] = metadata['tags']
            article['keywords'] = metadata['keywords']

            if metadata['published_time'] is not None:
                article['publish_date'] = metadata['published_time']
            elif entry.publish_date is not None:
                article['publish_date'] = entry.publish_date.strftime('%Y-%m-%dT%H:%M:%S%z')
            else:
                article['publish_date'] = now.strftime('%Y-%m-%dT%H:%M:%S%z')

            # ts = parser.parse(article['publish_date']).strftime('%y%m%d')
            ts = parser.parse(article['publish_date']).timestamp()

            file_name = f"{ts}_{site_no :04d}_{index + 1 :03d}.md"
            file_path = os.path.join(output_dir, file_name)


            article['short_url'] = site_name
            article['full_url'] = article_url
            article['author'] = entry.authors
            article['title'] = entry.title
            article['body'] = entry.article_html
            article['summary'] = entry.summary
            article['keywords'] = entry.keywords
            article['image_url'] = entry.top_image
            article['images'] = entry.images
            article['movies'] = entry.movies

            article['popular'] = random.choice([True, False])
            article['latest'] = random.choice([True, False])
            article['trend'] = random.choice([True, False])
            article['featured'] = random.choice([True, False])


            # Download image
            # ext = os.path.splitext(urlparse(article['image_url']).path)[-1]
            # image_file_name = f"{ts}_{site_no :04d}_{index + 1 :03d}{ext}"
            # image_file_path = os.path.join(output_image_dir, image_file_name)

            # response = requests.get(article['image_url'])
            # if response.status_code == 200:
            #     with open(image_file_path, 'wb') as file:
            #         file.write(response.content)
            #     article['image_url'] = image_file_path
            # else:
            #     print(f"Failed to download image from {article['image_url']}")
            #     article['image_url'] = alt_image_copy_path

            # relative_path = os.path.relpath(article['image_url'], start=output_dir)
            # article['image_url'] = relative_path

            # print(article['image_url'])


            articles_list.append(article)

            title = safe_yaml(article['title'])
            body = safe_yaml(html.unescape(article['body']))

            with open(file_path, 'w', encoding='utf-8') as f:
            # with open(file_path, 'w', encoding='cp932') as f:

                f.write(f'---\n')
                f.write(f'title: "{title}"\n')
                f.write(f'full_url: "{article["full_url"]}"\n')
                f.write(f'short_url: "{article["short_url"]}"\n')
                f.write(f'date: {article["publish_date"]}\n')
                f.write(f'draft: false\n')
                f.write(f'author: {article["author"]}\n')
                # f.write(f'categories: {article["category_urls"]}\n')
                f.write(f'categories: {article["categories"]}\n')
                f.write(f'tags: {article["tags"]}\n')
                f.write(f'keywords: {article["keywords"]}\n')
                f.write(f'thumbnail: "{article["image_url"]}"\n')
                f.write(f'popular: {article["popular"]}\n')
                f.write(f'latest: {article["latest"]}\n')
                f.write(f'trend: {article["trend"]}\n')
                f.write(f'featured: "{article["featured"]}"\n')
                f.write(f'---\n\n')
                f.write(f'![]({article["image_url"]})\n\n')
                f.write(body)

            print(f"New Hugo post '{file_name}' for {site_name} generated in {output_dir}.")
        except Exception as e:
            print(e)

def safe_yaml(text):
    char_mapping = {
        # ':': '\\:',
        # '-': '\\-',
        # '&': '\\&',
        # "'": "\\'",
        # '"': '\\"',
        # '!': '\\!',
        # '|': '\\|',
        '\n': ' ',
        '\u3000': ' ',
    }
    for char, replacement in char_mapping.items():
        text = text.replace(char, replacement)

    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', '\n\n', text)

    exclusion_words = {
    }
    exw_file = None # TODO
    try:
        if exw_file:
            df = Interface.read_file(exw_file)
            df = df['items']
            for k, v in df:
                exclusion_words[k] = v
    except Exception as e:
        print(e)


    for word, _ in exclusion_words.items():
        print(word)
        text = text.replace(word, '')


    return text


def remove_old_hugo_posts(output_dir, max_posts=1000):
    files = os.listdir(output_dir)
    files.sort(key=lambda x: os.path.getctime(os.path.join(output_dir, x)))

    while len(files) > max_posts:
        file_to_delete = os.path.join(output_dir, files.pop(0))
        os.remove(file_to_delete)
        print(f"Removed old Hugo post: {file_to_delete}")



class Interface:

    def get_tempdir():
        timestamp = int(time.time())
        temp_dir = tempfile.mkdtemp()
        return timestamp, temp_dir

    def create_zip(filelist):
        if not filelist:
            return
        else:
            tmp_dir = os.path.dirname(filelist[0])
            tmp_fname = "tmp.zip"
            zip_name = os.path.join(tmp_dir, tmp_fname)
            with zipfile.ZipFile(zip_name, "w") as zipf:
                for file in filelist:
                    zipf.write(file, os.path.basename(file))
            return zip_name

    def read_csv(csv_file):
        feeds = []
        with open(csv_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                feeds.append(row)
        data = {"items": feeds}
        return data

    def read_json(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)
        return data

    def read_yaml(yaml_file):
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
        return data

    def read_toml(toml_file):
        with open(toml_file, 'r') as f:
            data = toml.load(f)
        return data

    def read_raw(raw_file):
        with open(raw_file, 'r') as f:
            data = f.read()
        return {"items": [{'data': data}]}

    def read_xml(xml_file):
        data = {}
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for child in root:
            data[child.tag] = child.text

        return data

    def read_opml(opml_file):
        feeds = []
        tree = ET.parse(opml_file)
        root = tree.getroot()
        body = root.find('body')

        for outer_outline in body.findall('outline'):
            # Process the inner outlines
            for inner_outline in outer_outline.findall('outline'):
                feed = dict(inner_outline.attrib)  # Extract all attributes of the inner outline
                feeds.append(feed)

                # console.print(f'+++ {feed["url"]}')

        data = {"items": feeds}
        return data

    def read_file(fpath):
        if fpath.endswith('.csv'):
            data = Interface.read_csv(fpath)
        elif fpath.endswith('.json'):
            data = Interface.read_json(fpath)
        elif fpath.endswith('.opml'):
            data = Interface.read_opml(fpath)
            data = Interface.transform_opml_data(data)
        elif fpath.endswith('.toml'):
            data = Interface.read_toml(fpath)
        elif fpath.endswith('.yaml') or fpath.endswith('.yml'):
            data = Interface.read_yaml(fpath)
        elif fpath.endswith(''):
            data = Interface.read_raw(fpath)
        else:
            raise ValueError(f"Invalid file format: {fpath}")
        return data

def main():
    parser = argparse.ArgumentParser(description="Generate Hugo posts from article URLs.")
    parser.add_argument("-i", "--input_file", nargs="?", const=None, help="Path to the input JSON file")
    parser.add_argument("-o", "--output_dir", nargs="?", default="content/draft", help="Output directory for Hugo posts")
    parser.add_argument("--news_date", default=datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'), help="News date")
    parser.add_argument("-l", "--limit", type=int, default=1, help="Limit the number of articles to process")

    args = parser.parse_args()

    rss_urls = {
        "kanpo": "https://kanpo-kanpo.blog.jp/index.rdf",
    }

    limit = 1

    if args.input_file:
        rss_df = Interface.read_file(args.input_file)
        df = rss_df['items']

        for item in df:
            rss_urls[item["name"]] = item["url"]
            limit = item["limit"]

    if args.limit:
        limit = args.limit

    os.makedirs(args.output_dir, exist_ok=True)

    for site_no, (site_name, rss_url) in enumerate(rss_urls.items()):
        feed = feedparser.parse(rss_url)
        article_urls = [entry.link for entry in feed.entries[:limit]]
        generate_hugo_posts(site_no, site_name, article_urls, args.output_dir, args.news_date)

    remove_old_hugo_posts(args.output_dir, max_posts=1000)


if __name__ == "__main__":
    main()
