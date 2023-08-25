import requests, lxml.html, os, shutil, string
from lxml import etree
from ebooklib import epub
import unicodedata
import re

class Novelful:

    def __init__(self, url):
        self.url = url

    def slugify(self, value, allow_unicode=False):
        """
        Taken from https://github.com/django/django/blob/master/django/utils/text.py
        Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
        dashes to single dashes. Remove characters that aren't alphanumerics,
        underscores, or hyphens. Convert to lowercase. Also strip leading and
        trailing whitespace, dashes, and underscores.
        """
        value = str(value)
        if allow_unicode:
            value = unicodedata.normalize('NFKC', value)
        else:
            value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
        value = re.sub(r'[^\w\s-]', '', value.lower())
        return re.sub(r'[-\s]+', '-', value).strip('-_')
    
    def setup(self):
        directory = 'html'
        if os.path.exists(directory):
            shutil.rmtree(directory)

        os.makedirs(directory)


    def download_chapter(self, directory, link, id):
        request_chapter_html = requests.get(link)
        chapter_html = etree.HTML(request_chapter_html.text)
        
        with open(directory + '/' + 'ch' + str(id) + '.html', 'w', encoding='utf-8') as writer:
            writer.write(request_chapter_html.text)
        
        
        page_content = chapter_html.xpath('//div[@id="chapter-content"]')[0]
        chapter_title = chapter_html.xpath('//span[@class="chapter-text"]')[0]
        page_content.insert(0, chapter_title)

        next_chapter = chapter_html.xpath('//*[@id="next_chap"]')[0]

        if 'href' in next_chapter.attrib:
            return lxml.html.tostring(page_content), next_chapter.attrib['href'], next_chapter.attrib['title']
        else:
            return lxml.html.tostring(page_content), None, None

    def prepare_book(self, title, extension, cover_path):
        book = epub.EpubBook()

        book.set_language("en")
        book.set_title(title)
        book.set_cover("cover." + extension, open(cover_path, 'rb').read())
        book.spine.append('cover')

        return book

    def save_cover(self, html_page, directory, novel_title):
        page_cover  = html_page.xpath('//img[@alt="' + novel_title + '"]')[0]
        cover_link = 'https://novelfull.com' + page_cover.attrib['src']

        actual_cover = requests.get(cover_link, allow_redirects=True)
        extension = actual_cover.headers['Content-type'].split('/')[1]
        cover_path = directory + '/' + 'cover.' + extension

        with open(cover_path, 'wb') as writer:
            writer.write(actual_cover.content)
        
        return extension, cover_path

    def add_chapter(self, book, title, content, id):
        chap = epub.EpubHtml(title=title, file_name="chap_" + str(id) + ".xhtml")
        chap.title = title
            
        chap.set_content(content)

        book.add_item(chap)
        book.spine.append(chap)

    def download(self):
        directory = 'html'
        self.setup()

        page = requests.get(self.url)

        with open(directory + '/' + 'home.html', 'w', encoding='utf-8') as writer:
            writer.write(page.text)

        html_page = etree.HTML(page.text)
        novel_title = html_page.xpath('/html/body/div/main/div[2]/div[1]/div/div[1]/div[2]/div[1]/div[1]/h3')[0].text.strip('\n').strip()

        extension, cover_path = self.save_cover(html_page, directory, novel_title)

        print(novel_title)

        first_chapter = html_page.xpath('//ul[@class="list-chapter"]')[0].getchildren()[0].getchildren()[1]

        links = [first_chapter.attrib['href']]
        titles = [first_chapter.attrib['title']]

        book = self.prepare_book(novel_title, extension, cover_path)

        id = 0

        while len(links) != 0:
            content, next_link, next_title = self.download_chapter(directory, 'https://novelfull.com' + links[-1], id)

            self.add_chapter(book, titles[-1], content, id)

            print(titles[-1])
            
            titles.pop()
            links.pop()

            if next_title != None:
                titles.append(next_title)
                links.append(next_link)
            
                id = id + 1


        epub_path = ''.join(c for c in self.slugify(novel_title) + '.epub' if c in ("-_.() %s%s" % (string.ascii_letters, string.digits)))
            
        if os.path.exists(epub_path):
            os.remove(epub_path)

        epub.write_epub(epub_path, book, {})

        return epub_path