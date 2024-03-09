import requests
from html.parser import HTMLParser
import re

# -*- coding:utf-8 -*-
ranges = [
  {"from": ord(u"\u3300"), "to": ord(u"\u33ff")},         # compatibility ideographs
  {"from": ord(u"\ufe30"), "to": ord(u"\ufe4f")},         # compatibility ideographs
  {"from": ord(u"\uf900"), "to": ord(u"\ufaff")},         # compatibility ideographs
  {"from": ord(u"\U0002F800"), "to": ord(u"\U0002fa1f")}, # compatibility ideographs
  {'from': ord(u'\u3040'), 'to': ord(u'\u309f')},         # Japanese Hiragana
  {"from": ord(u"\u30a0"), "to": ord(u"\u30ff")},         # Japanese Katakana
  {"from": ord(u"\u2e80"), "to": ord(u"\u2eff")},         # cjk radicals supplement
  {"from": ord(u"\u4e00"), "to": ord(u"\u9fff")},
  {"from": ord(u"\u3400"), "to": ord(u"\u4dbf")},
  {"from": ord(u"\U00020000"), "to": ord(u"\U0002a6df")},
  {"from": ord(u"\U0002a700"), "to": ord(u"\U0002b73f")},
  {"from": ord(u"\U0002b740"), "to": ord(u"\U0002b81f")},
  {"from": ord(u"\U0002b820"), "to": ord(u"\U0002ceaf")}  # included as of Unicode 8.0
]


def is_cjk(char):
    return any([r["from"] <= ord(char) <= r["to"] for r in ranges])


class MyHTMLParser(HTMLParser):
    def __init__(self):
        self.in_b = False
        self.in_div = False
        self.names = []
        self.stripped_names = ["game", "genre", "version"]
        self.genre_img_urls = []
        self.genre_flag = None
        self.other_text = False
        super().__init__()

    def handle_starttag(self, tag, attrs):
        if tag == "b":
            self.in_b = True
        for attr in attrs:
            if tag == "img" and attr[0] == "src":
                if "gen4" in attr[1] or "genr" in attr[1]:
                    url = attr[1].replace("http://", "https://")
                    self.genre_img_urls.append(url)
                    self.genre_flag = True

    def handle_endtag(self, tag):
        if tag == "b":
            self.in_b = False
        self.other_text = False

    def handle_data(self, data):
        data = data.replace(u'\xa0', u' ').strip()
        stripped_name = re.sub(r"\s+", "", data.lower()).strip()
        if self.other_text and self.names:
            return
        self.other_text = True
        if not self.in_b:
            return
        if not stripped_name:
            return
        if stripped_name in self.stripped_names:
            return
        if any(is_cjk(c) for c in data) and self.names:
            return
        if data.replace("x", "").replace("0", "").isdigit():
            return
        if len(data) < 3 or len(data) > 100:
            return
        self.names.append(data)
        self.stripped_names.append(stripped_name)


BLOG_ID = "760759784775244167"

response = requests.get(
    url=f"https://www.googleapis.com/blogger/v3/blogs/{BLOG_ID}/posts",
    params={
        "labels": "weekly",
        "maxResults": "500",
        "status": "LIVE",
        "key": "[PUT YOUR GOOGLE CLOUD API KEY HERE]"
    }
)
response_json = response.json()
for item in response_json['items']:
    # Parse metadata from body of post
    parser = MyHTMLParser()
    content = item['content']
    parser.feed(content)

    # Fetch parsed metadata information
    song_names = parser.names
    genre_img_urls = parser.genre_img_urls
    post_url = item['url']
    post_title = item['title']
    title_elements = post_title.split(" ")
    year = title_elements[-1]
    month = title_elements[-2][:3] + "."
    day = title_elements[-3]

    genre_string = "".join(f'<img src="{genre_img_url}" />&nbsp;'
                           for genre_img_url in set(genre_img_urls))
    song_strings = [f'{genre_string}<a href="{post_url}">{song_name}</a>'
                    for song_name in song_names]
    joined = " / ".join(song_strings)
    song_string = (song_strings[0] if len(song_strings) == 1
                   else joined)

    # Print the HTML
    if int(year) > 2019:
        print(f'{month} {day} -&nbsp;{song_string}<br />')
