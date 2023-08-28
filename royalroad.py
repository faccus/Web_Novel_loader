import requests, lxml.html, os, shutil, string
from lxml import etree
from ebooklib import epub
import unicodedata
import re

class Royalroad:
    
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


    def download_page(self, directory, link, id):
        request_chapter_html = requests.get(link)
        chapter_html = etree.HTML(request_chapter_html.text)
        
        with open(directory + '/' + 'ch' + str(id) + '.html', 'w', encoding='utf-8') as writer:
            writer.write(request_chapter_html.text)
        
        
        page_content = chapter_html.xpath("//div[@class='chapter-inner chapter-content']")[0]
        chap_title = chapter_html.xpath('/html/body/div[3]/div/div/div/div/div[1]/div/div[2]/h1')[0]
        
        page_content.insert(0, chap_title)

        return lxml.html.tostring(page_content)

    def prepare_book(self, title, extension, cover_path):
        book = epub.EpubBook()

        book.set_language("en")
        book.set_title(title)
        book.set_cover("cover." + extension, open(cover_path, 'rb').read())
        book.spine.append('cover')

        return book

    def save_cover(self, html_page, directory):
        page_cover  = html_page.xpath("//img[@class='thumbnail inline-block']")[0]
        cover_link = page_cover.attrib['src']
        book_title = html_page.xpath('/html/body/div[3]/div/div/div/div[1]/div/div[1]/div[2]/div/h1')[0].text

        actual_cover = requests.get(cover_link, allow_redirects=True)
        extension = actual_cover.headers['Content-type'].split('/')[1]
        cover_path = directory + '/' + 'cover.' + extension

        with open(cover_path, 'wb') as writer:
            writer.write(actual_cover.content)
        
        return self.slugify(book_title), extension, cover_path

    def read_chapters_and_titles(self, html_page):
        page_chapters = html_page.xpath('/html/body/div[3]/div/div/div/div[1]/div/div[2]/div/div[2]/div[5]/div[2]/table/tbody')[0]
        titles   = []
        chapters = []
        for child in page_chapters.getchildren():
            chapters.append('https://www.royalroad.com' + child.attrib['data-url'])
            titles.append(child.getchildren()[0].getchildren()[0].text.strip('\n').strip())
        
        return titles, chapters

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

        title, extension, cover_path = self.save_cover(html_page, directory)


        titles, chapters = self.read_chapters_and_titles(html_page)


        book = self.prepare_book(title=title, extension=extension, cover_path=cover_path)

        for i in range(len(chapters)):
            print(titles[i])

            self.add_chapter(book, titles[i], self.download_page(directory=directory, link=chapters[i], id=i), i)


        epub_path = ''.join(c for c in title + '.epub' if c in ("-_.() %s%s" % (string.ascii_letters, string.digits)))
            
        if os.path.exists(epub_path):
            os.remove(epub_path)

        epub.write_epub(epub_path, book, {})

        return epub_path
    
downlaoder = Royalroad('https://www.royalroad.com/fiction/73052/technomagica-progression-fantasy-litrpg').download()