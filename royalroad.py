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


    def setup(self, directory='html'):
              
        if os.path.exists(directory):
            shutil.rmtree(directory)

        os.makedirs(directory)


    def download_page(self, directory, link, id):
        request_chapter_html = requests.get(link)
        chapter_html = etree.HTML(request_chapter_html.text)

        save_directory = directory + '/' + 'ch' + str(id)
        
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        with open(os.path.join(save_directory, 'content.html'), 'w', encoding='utf-8') as writer:
            writer.write(request_chapter_html.text)
        
        
        page_content = chapter_html.xpath("//div[@class='chapter-inner chapter-content']")[0]
        chap_title = chapter_html.xpath('/html/body/div[3]/div/div/div/div/div[1]/div/div[2]/h1')[0]
        note_content = chapter_html.xpath("//div[@class='portlet solid author-note-portlet']")

        if len(note_content) > 0:
            page_content.insert(0, note_content[0])

        page_content.insert(0, chap_title)

        images = []
        for image in page_content.xpath("//div[@class='chapter-inner chapter-content']//img"):
            if image.attrib['src'][0] == '/':
                image.attrib['src'] = 'https://www.royalroad.com' + image.attrib['src'][0]

            actual_image = requests.get(image.attrib['src'], allow_redirects=True)
            extension = actual_image.headers['Content-type'].split('/')[1]
            file_name = str(len(images)) + '.' + extension
            image_path = os.path.join(save_directory, file_name)
            
            with open(image_path, 'wb') as writer:
                writer.write(actual_image.content)
            
            image.attrib['src'] = 'ch' + str(id) + '/' + file_name
            images.append((image.attrib['src'], actual_image.headers['Content-type'], image_path))
        

        return lxml.html.tostring(page_content), images

    def prepare_book(self, title, extension, cover_path):
        book = epub.EpubBook()

        book.set_language("en")
        book.set_title(title)
        book.set_cover("cover." + extension, open(cover_path, 'rb').read())
        book.spine.append('cover')

        return book

    def save_cover(self, html_page):
        page_cover  = html_page.xpath("//img[@class='thumbnail inline-block']")[0]
        cover_link = page_cover.attrib['src']
        book_title = self.slugify(html_page.xpath('/html/body/div[3]/div/div/div/div[1]/div/div[1]/div[2]/div/h1')[0].text)

        self.setup(book_title)

        actual_cover = requests.get(cover_link, allow_redirects=True)
        extension = actual_cover.headers['Content-type'].split('/')[1]
        cover_path = book_title + '/' + 'cover.' + extension

        with open(cover_path, 'wb') as writer:
            writer.write(actual_cover.content)
        
        return book_title, extension, cover_path

    def read_chapters_and_titles(self, html_page):
        page_chapters = html_page.xpath('/html/body/div[3]/div/div/div/div[1]/div/div[2]/div/div[2]/div[5]/div[2]/table/tbody')[0]
        titles   = []
        chapters = []
        for child in page_chapters.getchildren():
            chapters.append('https://www.royalroad.com' + child.attrib['data-url'])
            titles.append(child.getchildren()[0].getchildren()[0].text.strip('\n').strip())
        
        return titles, chapters

    def add_chapter(self, book, title, content, image_info, id):
        chap = epub.EpubHtml(title=title, file_name="chap_" + str(id) + ".xhtml")
        chap.title = title
            
        chap.set_content(content)

        book.add_item(chap)
        book.spine.append(chap)

        for image_path, image_type, local_path in image_info:
            book.add_item(
                epub.EpubImage(file_name=image_path, media_type='image/gif', content=open(local_path, 'rb').read())
            )

    def download(self, clear=True):
        page = requests.get(self.url)
        html_page = etree.HTML(page.text)

        title, extension, cover_path = self.save_cover(html_page)
        directory = title


        titles, chapters = self.read_chapters_and_titles(html_page)


        book = self.prepare_book(title=title, extension=extension, cover_path=cover_path)

        for i in range(len(chapters)):
            print(titles[i])

            content, image_info = self.download_page(directory=directory, link=chapters[i], id=i)
            self.add_chapter(book, titles[i], content, image_info, i)


        epub_path = ''.join(c for c in title + '.epub' if c in ("-_.() %s%s" % (string.ascii_letters, string.digits)))
            
        if os.path.exists(epub_path):
            os.remove(epub_path)

        epub.write_epub(epub_path, book, {})

        if clear:
            shutil.rmtree(directory)

        return epub_path